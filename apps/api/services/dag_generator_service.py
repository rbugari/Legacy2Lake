"""
DAG Generator Service - Produces orchestration files (Airflow, Databricks, YAML)
Phase B - Orchestration

Uses the dependency graph to generate executable workflows.
"""

from typing import List, Dict, Optional, Any
import json
from pathlib import Path
from services.dependency_service import DependencyService
from services.persistence_service import SupabasePersistence

class DagGeneratorService:
    def __init__(self, db_client):
        self.db = db_client
        self.dependency_service = DependencyService(db_client)

    async def _get_project_path(self, project_id: str) -> str:
        """Helper to get naming-safe project path"""
        project_name = project_id
        if "-" in project_id:
            res = self.db.table('utm_projects').select('name').eq('project_id', project_id).execute()
            if res.data:
                project_name = res.data[0]['name']
        
        from services.persistence_service import PersistenceService
        return PersistenceService.ensure_solution_dir(project_name)

    async def generate_airflow_dag(self, project_id: str, dag_id: str = "legacy2lake_dag", save: bool = False) -> str:
        """Generates an Airflow Python DAG file"""
        plan = await self.dependency_service.get_execution_plan(project_id)
        if "error" in plan:
            return f"# Error: {plan['error']}\n# Cycle: {plan['cycle']}"

        execution_order = plan["execution_order"]
        # Fetch asset names for readability
        assets_res = self.db.table('utm_objects').select('object_id, source_name').eq('project_id', project_id).execute()
        asset_map = {a['object_id']: a['source_name'].replace('.', '_').replace('-', '_') for a in assets_res.data}

        dag_template = f'''from airflow import DAG
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta

default_args = {{
    'owner': 'legacy2lake',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}}

with DAG(
    '{dag_id}',
    default_args=default_args,
    description='Automated DAG from Legacy2Lake',
    schedule_interval=timedelta(days=1),
    catchup=False,
) as dag:

    start = EmptyOperator(task_id='start')
    end = EmptyOperator(task_id='end')

'''
        # Create tasks
        for asset_id in execution_order:
            task_name = asset_map.get(asset_id, f"task_{asset_id[:8]}")
            dag_template += f"    {task_name} = EmptyOperator(task_id='{task_name}')\n"

        dag_template += "\n"

        # Create dependencies
        graph = await self.dependency_service.get_dependencies(project_id)
        for asset_id, deps in graph.items():
            task_name = asset_map.get(asset_id)
            if not deps:
                dag_template += f"    start >> {task_name}\n"
            else:
                for dep_id in deps:
                    dep_name = asset_map.get(dep_id)
                    if dep_name:
                        dag_template += f"    {dep_name} >> {task_name}\n"

        # Final tasks
        leaf_nodes = [asset_map[aid] for aid in execution_order if not any(aid in d for d in graph.values())]
        for leaf in leaf_nodes:
            dag_template += f"    {leaf} >> end\n"

        if save:
            base_path = await self._get_project_path(project_id)
            orchestration_dir = Path(base_path) / "Orchestration"
            orchestration_dir.mkdir(parents=True, exist_ok=True)
            with open(orchestration_dir / f"{dag_id}.py", "w", encoding="utf-8") as f:
                f.write(dag_template)

        return dag_template

    async def generate_databricks_workflow(self, project_id: str, job_name: str = "Legacy2Lake Job", save: bool = False) -> Dict:
        """Generates a Databricks Workflow JSON definition"""
        plan = await self.dependency_service.get_execution_plan(project_id)
        if "error" in plan:
            return {"error": plan["error"]}

        execution_order = plan["execution_order"]
        assets_res = self.db.table('utm_objects').select('object_id, source_name').eq('project_id', project_id).execute()
        asset_map = {a['object_id']: a['source_name'] for a in assets_res.data}
        graph = await self.dependency_service.get_dependencies(project_id)

        tasks = []
        for asset_id in execution_order:
            name = asset_map.get(asset_id)
            if not name:
                name = f"task_{asset_id}"

            deps = graph.get(asset_id, [])
            
            task = {
                "task_key": name.replace('.', '_').replace('-', '_'),
                "notebook_task": {
                    "notebook_path": f"/Repos/Legacy2Lake/{name}",
                    "source": "WORKSPACE"
                },
                "depends_on": [{"task_key": asset_map[d].replace('.', '_').replace('-', '_')} for d in deps if d in asset_map]
            }
            tasks.append(task)

        workflow = {
            "name": job_name,
            "tasks": tasks,
            "format": "MULTI_TASK"
        }

        if save:
            base_path = await self._get_project_path(project_id)
            orchestration_dir = Path(base_path) / "Orchestration"
            orchestration_dir.mkdir(parents=True, exist_ok=True)
            with open(orchestration_dir / "databricks_workflow.json", "w", encoding="utf-8") as f:
                json.dump(workflow, f, indent=4)
        
        return workflow

    async def generate_generic_yaml(self, project_id: str, save: bool = False) -> str:
        """Generates a generic YAML orchestration file"""
        plan = await self.dependency_service.get_execution_plan(project_id)
        if "error" in plan:
            return f"error: {plan['error']}"

        assets_res = self.db.table('utm_objects').select('object_id, source_name').eq('project_id', project_id).execute()
        asset_map = {a['object_id']: a['source_name'] for a in assets_res.data}
        graph = await self.dependency_service.get_dependencies(project_id)

        yaml_output = "pipeline:\n  name: Legacy2Lake Generated Pipeline\n  tasks:\n"
        for asset_id in plan["execution_order"]:
            name = asset_map.get(asset_id)
            deps = [asset_map[d] for d in graph.get(asset_id, []) if d in asset_map]
            yaml_output += f"    - id: {name}\n"
            if deps:
                yaml_output += f"      depends_on: {deps}\n"
            yaml_output += "      type: spark_sql\n"

        if save:
            base_path = await self._get_project_path(project_id)
            orchestration_dir = Path(base_path) / "Orchestration"
            orchestration_dir.mkdir(parents=True, exist_ok=True)
            with open(orchestration_dir / "pipeline.yaml", "w", encoding="utf-8") as f:
                f.write(yaml_output)
            
        return yaml_output

    async def generate_orchestration(self, project_id: str, target_tech: str) -> Dict[str, Any]:
        """Unified method generated orchestration based on target tech."""
        tech = target_tech.lower()
        
        if "airflow" in tech or "composer" in tech:
            code = await self.generate_airflow_dag(project_id)
            return {"type": "airflow", "content": code, "filename": f"{project_id}_dag.py"}
        elif "databricks" in tech or "pyspark" in tech:
            json_wf = await self.generate_databricks_workflow(project_id)
            import json
            return {"type": "databricks", "content": json.dumps(json_wf, indent=2), "filename": "workflow.json"}
        else:
            # Fallback to YAML
            yaml_code = await self.generate_generic_yaml(project_id)
            return {"type": "yaml", "content": yaml_code, "filename": "pipeline.yaml"}
