"""
Test Case Generator Service - Sprint 8
=======================================

Purpose:
    Automatically generates pytest test cases from generated code.
    Tests are created based on function signatures, docstrings,
    and inferred data types.

Features:
    - Extract functions/classes from code (AST parsing)
    - Generate pytest fixtures
    - Create unit tests for each function
    - Generate integration tests for end-to-end flows
    - Mock data generation based on schema

Usage:
    generator = TestGeneratorService()
    test_code = await generator.generate_tests(
        code=generated_code,
        tech_id='pyspark',
        metadata={'source_table': 'customers', 'target_table': 'bronze_customers'}
    )

Integration:
    - Called by Agent C after code generation
    - Called by ValidationService after validation passes
    - Test code saved alongside generated code

Author: Legacy2Lake Engineering
Date: 2026-02-11 (Sprint 8)
Version: v1.0
"""

import ast
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

try:
    from apps.api.utils.logger import logger
except ImportError:
    from utils.logger import logger


@dataclass
class FunctionInfo:
    """Extracted function metadata"""
    name: str
    args: List[str]
    returns: Optional[str]
    docstring: Optional[str]
    is_async: bool
    line_number: int


@dataclass
class TestCase:
    """Generated test case"""
    test_name: str
    function_name: str
    test_code: str
    test_type: str  # 'unit', 'integration', 'smoke'
    description: str


class TestGeneratorService:
    """
    Generates pytest test cases from generated code.
    Supports PySpark, Snowflake SQL scripts, and generic Python.
    """
    
    # Test templates
    UNIT_TEST_TEMPLATE = '''def test_{test_name}({fixtures}):
    """
    {description}
    """
    # Arrange
{arrange_code}
    
    # Act
    result = {function_call}
    
    # Assert
{assert_code}
'''
    
    PYSPARK_FIXTURE_TEMPLATE = '''@pytest.fixture(scope="session")
def spark():
    """Create a Spark session for testing"""
    from pyspark.sql import SparkSession
    
    spark = SparkSession.builder \\
        .appName("test_session") \\
        .master("local[2]") \\
        .config("spark.sql.shuffle.partitions", "2") \\
        .getOrCreate()
    
    yield spark
    
    spark.stop()


@pytest.fixture
def sample_dataframe(spark):
    """Create a sample DataFrame for testing"""
    data = [
        (1, "Alice", 25, "2024-01-01"),
        (2, "Bob", 30, "2024-01-02"),
        (3, "Charlie", 35, "2024-01-03")
    ]
    columns = ["id", "name", "age", "load_date"]
    
    return spark.createDataFrame(data, columns)
'''
    
    def __init__(self):
        self.version = "v1.0"
    
    
    async def generate_tests(
        self,
        code: str,
        tech_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Main entry point for test generation.
        
        Args:
            code: Generated code to create tests for
            tech_id: Technology ID (pyspark, snowflake, etc.)
            metadata: Optional metadata (source_table, target_table, etc.)
        
        Returns:
            pytest-compatible test code
        """
        logger.info(f"[TestGen] Generating tests for {tech_id} code", "TestGen")
        
        metadata = metadata or {}
        
        # SQL-based targets: Use basic SQL test plan instead of pytest (since SQL isn't Python)
        sql_targets = ['snowflake', 'snowflake_sql', 'snowflake_sql_direct', 'mssql', 'postgresql', 'oracle', 'bigquery', 'redshift']
        if tech_id.lower() in sql_targets or tech_id.lower().endswith('_sql'):
            return self._generate_sql_test_plan(code, tech_id, metadata)
        
        # Extract functions from code
        functions = self._extract_functions(code)
        
        logger.info(f"[TestGen] Found {len(functions)} functions to test", "TestGen")
        
        # Generate test cases
        test_cases: List[TestCase] = []
        
        for func_info in functions:
            # Unit test for each function
            unit_test = self._generate_unit_test(func_info, tech_id, metadata)
            test_cases.append(unit_test)
        
        # Integration test (end-to-end)
        if len(functions) > 1:
            integration_test = self._generate_integration_test(functions, tech_id, metadata)
            test_cases.append(integration_test)
        
        # Build final test file
        test_file = self._build_test_file(test_cases, tech_id, metadata)
        
        logger.info(f"[TestGen] Generated {len(test_cases)} test cases", "TestGen")
        
        return test_file
    
    def _generate_sql_test_plan(self, code: str, tech_id: str, metadata: Dict[str, Any]) -> str:
        """Generate a basic SQL validation plan for SQL targets."""
        table_name = metadata.get('target_table', 'YOUR_TABLE')
        
        plan = f"""-- SQL Validation Plan for {tech_id.upper()}
-- Generated: {datetime.utcnow().isoformat()}

-- 1. Structural Validation
SELECT * FROM {table_name} LIMIT 0;

-- 2. Data Quality Checks
-- Check for nulls in key columns
SELECT COUNT(*) as null_violations 
FROM {table_name} 
WHERE 1=0; -- TODO: Add key columns

-- 3. Row Count Verification
SELECT COUNT(*) as total_rows FROM {table_name};

-- 4. Sample Data Review
SELECT * FROM {table_name} LIMIT 10;
"""
        return plan
    
    def _extract_functions(self, code: str) -> List[FunctionInfo]:
        """Extract function definitions from code using AST"""
        functions = []
        
        if not code or not code.strip():
            return functions

        # Simple check to avoid parsing SQL with AST
        if code.strip().upper().startswith(('SELECT', 'CREATE', 'INSERT', 'UPDATE', 'DELETE', 'WITH', 'DROP', 'ALTER')):
            return functions
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Extract function metadata
                    func_name = node.name
                    
                    # Skip private functions
                    if func_name.startswith('_'):
                        continue
                    
                    # Extract arguments
                    args = [arg.arg for arg in node.args.args if arg.arg != 'self']
                    
                    # Extract return type (if annotated)
                    returns = None
                    if node.returns:
                        if isinstance(node.returns, ast.Name):
                            returns = node.returns.id
                        elif isinstance(node.returns, ast.Subscript):
                            # Handle List[str], Dict[str, Any], etc.
                            returns = ast.unparse(node.returns)
                    
                    # Extract docstring
                    docstring = ast.get_docstring(node)
                    
                    # Is async?
                    is_async = isinstance(node, ast.AsyncFunctionDef)
                    
                    functions.append(FunctionInfo(
                        name=func_name,
                        args=args,
                        returns=returns,
                        docstring=docstring,
                        is_async=is_async,
                        line_number=node.lineno
                    ))
        
        except (SyntaxError, ValueError) as e:
            logger.warning(f"[TestGen] Failed to parse code as Python: {e}", "TestGen")
        
        return functions
    
    
    def _generate_unit_test(
        self,
        func_info: FunctionInfo,
        tech_id: str,
        metadata: Dict[str, Any]
    ) -> TestCase:
        """Generate a unit test for a single function"""
        
        test_name = f"{func_info.name}_success"
        description = func_info.docstring or f"Test {func_info.name} function"
        
        # Determine fixtures needed
        fixtures = []
        if 'spark' in func_info.args or 'df' in func_info.args:
            fixtures.append('spark')
        if 'df' in func_info.args or 'dataframe' in func_info.args:
            fixtures.append('sample_dataframe')
        
        fixtures_str = ', '.join(fixtures) if fixtures else ''
        
        # Generate arrange code (setup mock data)
        arrange_lines = []
        for arg in func_info.args:
            if arg == 'spark':
                continue  # Provided by fixture
            elif arg == 'df' or arg == 'dataframe':
                arrange_lines.append('    df = sample_dataframe')
            elif arg == 'source_table':
                arrange_lines.append(f'    source_table = "{metadata.get("source_table", "test_source")}"')
            elif arg == 'target_table':
                arrange_lines.append(f'    target_table = "{metadata.get("target_table", "test_target")}"')
            elif arg == 'bronze_path' or arg == 'silver_path' or arg == 'gold_path':
                arrange_lines.append(f'    {arg} = "/tmp/{arg}"')
            else:
                arrange_lines.append(f'    {arg} = None  # TODO: Provide test value')
        
        arrange_code = '\n'.join(arrange_lines) if arrange_lines else '    pass  # No setup needed'
        
        # Generate function call
        call_args = []
        for arg in func_info.args:
            if arg not in ['spark', 'self']:
                call_args.append(arg)
        
        if func_info.is_async:
            function_call = f"await {func_info.name}({', '.join(call_args)})"
        else:
            function_call = f"{func_info.name}({', '.join(call_args)})"
        
        # Generate assert code (based on return type)
        assert_lines = []
        if func_info.returns:
            if 'DataFrame' in func_info.returns:
                assert_lines.append('    assert result is not None')
                assert_lines.append('    assert result.count() > 0')
            elif 'Dict' in func_info.returns:
                assert_lines.append('    assert isinstance(result, dict)')
                assert_lines.append('    assert len(result) > 0')
            elif 'bool' in func_info.returns:
                assert_lines.append('    assert isinstance(result, bool)')
                assert_lines.append('    assert result is True')
            else:
                assert_lines.append('    assert result is not None')
        else:
            assert_lines.append('    assert result is not None')
        
        assert_code = '\n'.join(assert_lines)
        
        # Build test code
        test_code = self.UNIT_TEST_TEMPLATE.format(
            test_name=test_name,
            fixtures=fixtures_str,
            description=description,
            arrange_code=arrange_code,
            function_call=function_call,
            assert_code=assert_code
        )
        
        return TestCase(
            test_name=test_name,
            function_name=func_info.name,
            test_code=test_code,
            test_type='unit',
            description=description
        )
    
    
    def _generate_integration_test(
        self,
        functions: List[FunctionInfo],
        tech_id: str,
        metadata: Dict[str, Any]
    ) -> TestCase:
        """Generate an integration test for the entire pipeline"""
        
        test_name = "integration_pipeline_end_to_end"
        description = "Test complete data pipeline from source to target"
        
        # Build integration test code
        test_code = f'''def test_{test_name}(spark, sample_dataframe):
    """
    {description}
    
    Tests the following steps:
    {chr(10).join(f"    - {func.name}()" for func in functions)}
    """
    # Arrange: Setup test data
    df = sample_dataframe
    source_table = "{metadata.get('source_table', 'test_source')}"
    target_table = "{metadata.get('target_table', 'test_target')}"
    
    # Act: Execute pipeline steps
'''
        
        # Add function calls in order
        for i, func_info in enumerate(functions, 1):
            if func_info.is_async:
                test_code += f'    # Step {i}: {func_info.name}\n'
                test_code += f'    result_{i} = await {func_info.name}(df, source_table, target_table)\n'
            else:
                test_code += f'    # Step {i}: {func_info.name}\n'
                test_code += f'    result_{i} = {func_info.name}(df, source_table, target_table)\n'
        
        # Add assertions
        test_code += '''
    # Assert: Verify final result
    final_result = result_1  # TODO: Adjust based on actual pipeline
    
    assert final_result is not None
    # TODO: Add more specific assertions
'''
        
        return TestCase(
            test_name=test_name,
            function_name='integration',
            test_code=test_code,
            test_type='integration',
            description=description
        )
    
    
    def _build_test_file(
        self,
        test_cases: List[TestCase],
        tech_id: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Build complete pytest test file"""
        
        lines = []
        
        # Header
        lines.append('"""')
        lines.append(f'Auto-generated test file for {tech_id} code')
        lines.append(f'Generated: {datetime.utcnow().isoformat()}')
        lines.append(f'Metadata: {metadata}')
        lines.append('"""')
        lines.append('')
        
        # Imports
        lines.append('import pytest')
        
        if tech_id == 'pyspark' or 'spark' in str(metadata):
            lines.append('from pyspark.sql import SparkSession, DataFrame')
        
        lines.append('')
        lines.append('# Import functions from generated code')
        lines.append('# TODO: Adjust import path')
        lines.append('# from apps.api.services.generated_code import *')
        lines.append('')
        lines.append('')
        
        # Fixtures
        if tech_id == 'pyspark':
            lines.append(self.PYSPARK_FIXTURE_TEMPLATE)
            lines.append('')
        
        # Test cases
        for test_case in test_cases:
            lines.append(test_case.test_code)
            lines.append('')
        
        return '\n'.join(lines)
