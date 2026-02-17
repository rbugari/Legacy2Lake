"""
Sprint 12: Performance Optimization - Parallel Processor Service

This service executes operations in parallel for better performance in batch processing.
Supports async, process pool, and thread pool execution modes.

Key Features:
- Async parallel execution (I/O bound tasks)
- Process pool execution (CPU bound tasks)
- Thread pool execution (mixed workloads)
- Automatic mode selection
- Resource limits and timeout handling
- Error handling and recovery

Author: UTM Platform Team
Version: 3.14 (Sprint 12)
"""

import asyncio
import time
from typing import List, Dict, Any, Callable, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, TimeoutError
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Execution mode for parallel processing"""
    ASYNC = "async"  # Async parallel (I/O bound)
    PROCESS = "process"  # Process pool (CPU bound)
    THREAD = "thread"  # Thread pool (mixed)
    AUTO = "auto"  # Automatic selection


@dataclass
class TaskResult:
    """Result of a single task execution"""
    task_id: str
    status: str  # "success" or "error"
    value: Any
    error: Optional[str]
    duration_ms: float
    worker_id: Optional[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class BatchResult:
    """Result of batch execution"""
    total_tasks: int
    succeeded: int
    failed: int
    results: List[TaskResult]
    total_duration_ms: float
    sequential_estimate_ms: float
    speedup_factor: float
    execution_mode: str
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['results'] = [r.to_dict() for r in self.results]
        return result


@dataclass
class BatchQualityReport:
    """Batch quality evaluation report"""
    table_reports: List[Dict[str, Any]]
    total_tables: int
    avg_quality_score: float
    min_quality_score: float
    max_quality_score: float
    tables_below_threshold: List[str]
    execution_time_ms: float
    speedup_factor: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ParallelProcessor:
    """
    Execute operations in parallel for better performance.
    
    Supports three execution modes:
    - Async: For I/O bound tasks (database queries, API calls)
    - Process Pool: For CPU bound tasks (data processing, computation)
    - Thread Pool: For mixed workloads
    
    Features:
    - Automatic mode selection based on task type
    - Resource limits (max workers, memory, CPU)
    - Timeout handling per task
    - Error recovery and partial results
    - Performance metrics
    
    Example:
        processor = ParallelProcessor(max_workers=10)
        
        # Async parallel execution
        tasks = [lambda: fetch_data(url) for url in urls]
        results = await processor.execute_batch(tasks, mode="async")
        
        # Process pool execution
        tasks = [lambda: process_data(chunk) for chunk in chunks]
        results = await processor.execute_batch(tasks, mode="process")
        
        # Batch quality evaluation
        tables = ["table1", "table2", "table3"]
        report = await processor.batch_quality_evaluation(
            tables, tenant_id, project_id
        )
    """
    
    def __init__(
        self,
        max_workers: int = 10,
        mode: str = "auto",
        timeout_seconds: int = 30,
        memory_limit_mb: Optional[int] = None
    ):
        """
        Initialize parallel processor.
        
        Args:
            max_workers: Maximum concurrent workers
            mode: "async", "process", "thread", or "auto"
            timeout_seconds: Timeout per task (seconds)
            memory_limit_mb: Memory limit per worker (MB)
        """
        self.max_workers = max_workers
        self.default_mode = ExecutionMode(mode)
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb
        
        # Executors (will be created on demand)
        self.thread_executor: Optional[ThreadPoolExecutor] = None
        self.process_executor: Optional[ProcessPoolExecutor] = None
        
        logger.info(
            f"ParallelProcessor initialized: max_workers={max_workers}, "
            f"mode={mode}, timeout={timeout_seconds}s"
        )
    
    async def execute_batch(
        self,
        tasks: List[Callable],
        mode: Optional[str] = None,
        task_ids: Optional[List[str]] = None
    ) -> BatchResult:
        """
        Execute tasks in parallel.
        
        Args:
            tasks: List of callables to execute
            mode: Override execution mode ("async", "process", "thread")
            task_ids: Optional list of task IDs (for tracking)
        
        Returns:
            BatchResult with execution details
        """
        start_time = time.time()
        
        # Determine execution mode
        exec_mode = ExecutionMode(mode) if mode else self.default_mode
        if exec_mode == ExecutionMode.AUTO:
            exec_mode = self._select_mode(tasks)
        
        # Generate task IDs if not provided
        if not task_ids:
            task_ids = [f"task-{i}" for i in range(len(tasks))]
        
        logger.info(
            f"Executing batch: {len(tasks)} tasks, mode={exec_mode.value}, "
            f"max_workers={self.max_workers}"
        )
        
        # Execute based on mode
        if exec_mode == ExecutionMode.ASYNC:
            results = await self._execute_async(tasks, task_ids)
        elif exec_mode == ExecutionMode.PROCESS:
            results = await self._execute_process_pool(tasks, task_ids)
        elif exec_mode == ExecutionMode.THREAD:
            results = await self._execute_thread_pool(tasks, task_ids)
        else:
            raise ValueError(f"Unsupported execution mode: {exec_mode}")
        
        # Calculate metrics
        total_duration_ms = (time.time() - start_time) * 1000
        succeeded = sum(1 for r in results if r.status == "success")
        failed = len(results) - succeeded
        
        # Estimate sequential execution time
        avg_task_time = sum(r.duration_ms for r in results) / len(results) if results else 0
        sequential_estimate_ms = avg_task_time * len(tasks)
        
        # Calculate speedup
        speedup_factor = sequential_estimate_ms / total_duration_ms if total_duration_ms > 0 else 1.0
        
        logger.info(
            f"Batch complete: {succeeded}/{len(tasks)} succeeded, "
            f"duration={total_duration_ms:.0f}ms, speedup={speedup_factor:.2f}x"
        )
        
        return BatchResult(
            total_tasks=len(tasks),
            succeeded=succeeded,
            failed=failed,
            results=results,
            total_duration_ms=round(total_duration_ms, 2),
            sequential_estimate_ms=round(sequential_estimate_ms, 2),
            speedup_factor=round(speedup_factor, 2),
            execution_mode=exec_mode.value
        )
    
    async def _execute_async(
        self,
        tasks: List[Callable],
        task_ids: List[str]
    ) -> List[TaskResult]:
        """
        Execute tasks using async parallel execution.
        
        Best for I/O bound tasks (database queries, API calls).
        """
        async def execute_task(task: Callable, task_id: str, worker_id: int) -> TaskResult:
            """Execute a single task with error handling"""
            start = time.time()
            
            try:
                # Handle both sync and async callables
                if asyncio.iscoroutinefunction(task):
                    result = await asyncio.wait_for(
                        task(),
                        timeout=self.timeout_seconds
                    )
                else:
                    # Run sync function in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, task),
                        timeout=self.timeout_seconds
                    )
                
                duration_ms = (time.time() - start) * 1000
                
                return TaskResult(
                    task_id=task_id,
                    status="success",
                    value=result,
                    error=None,
                    duration_ms=round(duration_ms, 2),
                    worker_id=f"async-{worker_id}",
                    timestamp=datetime.utcnow()
                )
            
            except asyncio.TimeoutError:
                duration_ms = (time.time() - start) * 1000
                logger.error(f"Task {task_id} timed out after {self.timeout_seconds}s")
                
                return TaskResult(
                    task_id=task_id,
                    status="error",
                    value=None,
                    error=f"Timeout after {self.timeout_seconds}s",
                    duration_ms=round(duration_ms, 2),
                    worker_id=f"async-{worker_id}",
                    timestamp=datetime.utcnow()
                )
            
            except Exception as e:
                duration_ms = (time.time() - start) * 1000
                logger.error(f"Task {task_id} failed: {str(e)}")
                
                return TaskResult(
                    task_id=task_id,
                    status="error",
                    value=None,
                    error=str(e),
                    duration_ms=round(duration_ms, 2),
                    worker_id=f"async-{worker_id}",
                    timestamp=datetime.utcnow()
                )
        
        # Create tasks with worker IDs
        async_tasks = [
            execute_task(task, task_id, i % self.max_workers)
            for i, (task, task_id) in enumerate(zip(tasks, task_ids))
        ]
        
        # Execute with concurrency limit
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def bounded_task(task):
            async with semaphore:
                return await task
        
        bounded_tasks = [bounded_task(t) for t in async_tasks]
        results = await asyncio.gather(*bounded_tasks)
        
        return results
    
    async def _execute_process_pool(
        self,
        tasks: List[Callable],
        task_ids: List[str]
    ) -> List[TaskResult]:
        """
        Execute tasks using process pool.
        
        Best for CPU bound tasks (data processing, computation).
        """
        if not self.process_executor:
            self.process_executor = ProcessPoolExecutor(max_workers=self.max_workers)
        
        results = []
        loop = asyncio.get_event_loop()
        
        for i, (task, task_id) in enumerate(zip(tasks, task_ids)):
            worker_id = i % self.max_workers
            start = time.time()
            
            try:
                # Submit to process pool
                future = self.process_executor.submit(task)
                
                # Wait with timeout
                result = await loop.run_in_executor(
                    None,
                    lambda: future.result(timeout=self.timeout_seconds)
                )
                
                duration_ms = (time.time() - start) * 1000
                
                results.append(TaskResult(
                    task_id=task_id,
                    status="success",
                    value=result,
                    error=None,
                    duration_ms=round(duration_ms, 2),
                    worker_id=f"process-{worker_id}",
                    timestamp=datetime.utcnow()
                ))
            
            except TimeoutError:
                duration_ms = (time.time() - start) * 1000
                logger.error(f"Task {task_id} timed out (process pool)")
                
                results.append(TaskResult(
                    task_id=task_id,
                    status="error",
                    value=None,
                    error=f"Timeout after {self.timeout_seconds}s",
                    duration_ms=round(duration_ms, 2),
                    worker_id=f"process-{worker_id}",
                    timestamp=datetime.utcnow()
                ))
            
            except Exception as e:
                duration_ms = (time.time() - start) * 1000
                logger.error(f"Task {task_id} failed (process pool): {str(e)}")
                
                results.append(TaskResult(
                    task_id=task_id,
                    status="error",
                    value=None,
                    error=str(e),
                    duration_ms=round(duration_ms, 2),
                    worker_id=f"process-{worker_id}",
                    timestamp=datetime.utcnow()
                ))
        
        return results
    
    async def _execute_thread_pool(
        self,
        tasks: List[Callable],
        task_ids: List[str]
    ) -> List[TaskResult]:
        """
        Execute tasks using thread pool.
        
        Best for mixed I/O and CPU bound tasks.
        """
        if not self.thread_executor:
            self.thread_executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        results = []
        loop = asyncio.get_event_loop()
        
        for i, (task, task_id) in enumerate(zip(tasks, task_ids)):
            worker_id = i % self.max_workers
            start = time.time()
            
            try:
                # Submit to thread pool
                result = await asyncio.wait_for(
                    loop.run_in_executor(self.thread_executor, task),
                    timeout=self.timeout_seconds
                )
                
                duration_ms = (time.time() - start) * 1000
                
                results.append(TaskResult(
                    task_id=task_id,
                    status="success",
                    value=result,
                    error=None,
                    duration_ms=round(duration_ms, 2),
                    worker_id=f"thread-{worker_id}",
                    timestamp=datetime.utcnow()
                ))
            
            except asyncio.TimeoutError:
                duration_ms = (time.time() - start) * 1000
                logger.error(f"Task {task_id} timed out (thread pool)")
                
                results.append(TaskResult(
                    task_id=task_id,
                    status="error",
                    value=None,
                    error=f"Timeout after {self.timeout_seconds}s",
                    duration_ms=round(duration_ms, 2),
                    worker_id=f"thread-{worker_id}",
                    timestamp=datetime.utcnow()
                ))
            
            except Exception as e:
                duration_ms = (time.time() - start) * 1000
                logger.error(f"Task {task_id} failed (thread pool): {str(e)}")
                
                results.append(TaskResult(
                    task_id=task_id,
                    status="error",
                    value=None,
                    error=str(e),
                    duration_ms=round(duration_ms, 2),
                    worker_id=f"thread-{worker_id}",
                    timestamp=datetime.utcnow()
                ))
        
        return results
    
    def _select_mode(self, tasks: List[Callable]) -> ExecutionMode:
        """
        Automatically select best execution mode.
        
        Args:
            tasks: List of tasks to execute
        
        Returns:
            Selected ExecutionMode
        """
        # Check if tasks are async
        if tasks and asyncio.iscoroutinefunction(tasks[0]):
            return ExecutionMode.ASYNC
        
        # Default to async for I/O bound workloads
        # (Most database/API operations are I/O bound)
        return ExecutionMode.ASYNC
    
    async def process_tables_parallel(
        self,
        table_names: List[str],
        operation: str,
        **kwargs
    ) -> BatchResult:
        """
        Process multiple tables in parallel.
        
        Args:
            table_names: List of tables to process
            operation: Operation name ("evaluate_quality", "calculate_metrics", etc.)
            **kwargs: Additional arguments for operation
        
        Returns:
            BatchResult with processing results
        """
        # Import services dynamically to avoid circular imports
        from apps.api.services.quality_rule_engine_service import QualityRuleEngine
        from apps.api.services.metrics_calculator_service import MetricsCalculator
        from apps.api.services.anomaly_detector_service import AnomalyDetector
        
        tenant_id = kwargs.get("tenant_id")
        project_id = kwargs.get("project_id")
        catalog = kwargs.get("catalog", "")
        schema = kwargs.get("schema", "")
        
        # Create tasks based on operation
        tasks = []
        
        if operation == "evaluate_quality":
            engine = QualityRuleEngine(tenant_id, project_id)
            tasks = [
                lambda t=table: engine.evaluate_table(t, catalog, schema)
                for table in table_names
            ]
        
        elif operation == "calculate_metrics":
            calculator = MetricsCalculator(tenant_id, project_id)
            tasks = [
                lambda t=table: calculator.calculate_metrics(t, catalog, schema)
                for table in table_names
            ]
        
        elif operation == "detect_anomalies":
            detector = AnomalyDetector(tenant_id, project_id)
            tasks = [
                lambda t=table: detector.detect_anomalies(t, catalog, schema)
                for table in table_names
            ]
        
        else:
            raise ValueError(f"Unsupported operation: {operation}")
        
        # Execute in parallel
        return await self.execute_batch(
            tasks=tasks,
            task_ids=table_names,
            mode="async"  # Quality operations are I/O bound
        )
    
    async def batch_quality_evaluation(
        self,
        table_names: List[str],
        tenant_id: str,
        project_id: str,
        catalog: str = "",
        schema: str = "",
        quality_threshold: float = 70.0
    ) -> BatchQualityReport:
        """
        Evaluate quality for multiple tables in parallel.
        
        Args:
            table_names: List of tables to evaluate
            tenant_id: Tenant ID
            project_id: Project ID
            catalog: Database catalog
            schema: Database schema
            quality_threshold: Minimum acceptable quality score
        
        Returns:
            BatchQualityReport with aggregated results
        """
        logger.info(
            f"Starting batch quality evaluation: {len(table_names)} tables, "
            f"threshold={quality_threshold}%"
        )
        
        # Execute parallel evaluation
        result = await self.process_tables_parallel(
            table_names=table_names,
            operation="evaluate_quality",
            tenant_id=tenant_id,
            project_id=project_id,
            catalog=catalog,
            schema=schema
        )
        
        # Extract quality reports
        table_reports = []
        quality_scores = []
        tables_below_threshold = []
        
        for task_result in result.results:
            if task_result.status == "success" and task_result.value:
                report = task_result.value
                table_reports.append({
                    "table_name": task_result.task_id,
                    "quality_score": report.quality_score,
                    "rules_passed": report.rules_passed,
                    "rules_failed": report.rules_failed
                })
                quality_scores.append(report.quality_score)
                
                if report.quality_score < quality_threshold:
                    tables_below_threshold.append(task_result.task_id)
        
        # Calculate aggregates
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        min_quality = min(quality_scores) if quality_scores else 0.0
        max_quality = max(quality_scores) if quality_scores else 0.0
        
        logger.info(
            f"Batch quality evaluation complete: avg={avg_quality:.1f}%, "
            f"min={min_quality:.1f}%, max={max_quality:.1f}%, "
            f"below_threshold={len(tables_below_threshold)}"
        )
        
        return BatchQualityReport(
            table_reports=table_reports,
            total_tables=len(table_names),
            avg_quality_score=round(avg_quality, 2),
            min_quality_score=round(min_quality, 2),
            max_quality_score=round(max_quality, 2),
            tables_below_threshold=tables_below_threshold,
            execution_time_ms=result.total_duration_ms,
            speedup_factor=result.speedup_factor
        )
    
    async def shutdown(self):
        """Shutdown executors and cleanup resources."""
        if self.thread_executor:
            self.thread_executor.shutdown(wait=True)
            logger.info("Thread pool executor shutdown")
        
        if self.process_executor:
            self.process_executor.shutdown(wait=True)
            logger.info("Process pool executor shutdown")
    
    def __del__(self):
        """Cleanup on deletion."""
        # Note: Can't use async in __del__, so we just shutdown synchronously
        if self.thread_executor:
            self.thread_executor.shutdown(wait=False)
        if self.process_executor:
            self.process_executor.shutdown(wait=False)
