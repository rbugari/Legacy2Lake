import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ["STORAGE_PROVIDER"] = "LOCAL"
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from apps.api.services.agent_c_service import AgentCService
from apps.api.services.agent_f_service import AgentFService
from apps.api.services.agent_g_service import AgentGService


EVAL_REPORT_PATH = ROOT / "test_results" / "ssis_fixture_evaluation.json"
PIPELINE_REPORT_PATH = ROOT / "test_results" / "ssis_generation_pipeline.json"
DEFAULT_TENANT_ID = os.getenv("EVAL_TENANT_ID", "f98edb5e-4165-4c49-9fce-18894e8a818c")
DEFAULT_NODE_LABEL = "ETL_Dim_Customer"


def extract_code(result: dict) -> str:
    for key in ("code", "pyspark_code", "sql_code", "dbt_code", "final_code", "generated_code"):
        value = result.get(key)
        if value:
            return value
    return ""


def parse_args():
    parser = argparse.ArgumentParser(description="Run SSIS generation pipeline evaluation with Agent C/F/G.")
    parser.add_argument("--tenant-id", default=DEFAULT_TENANT_ID, help="Tenant UUID with active agent configs.")
    parser.add_argument("--node-label", default=DEFAULT_NODE_LABEL, help="Mesh node label to evaluate.")
    parser.add_argument(
        "--targets",
        nargs="*",
        default=["snowflake_sql:direct", "pyspark:direct"],
        help="Targets to evaluate in target:layer format.",
    )
    return parser.parse_args()


def load_mesh_report() -> dict:
    if not EVAL_REPORT_PATH.exists():
        raise FileNotFoundError(f"Evaluation report not found: {EVAL_REPORT_PATH}")
    return json.loads(EVAL_REPORT_PATH.read_text(encoding="utf-8"))


def find_node(mesh: dict, node_label: str) -> dict:
    for node in mesh.get("nodes", []):
        if node.get("label") == node_label:
            return node
    raise ValueError(f"Node '{node_label}' not found in mesh.")


def build_task_info(node: dict, project_name: str, target_tech: str, layer: str) -> dict:
    return {
        "project_id": project_name,
        "name": node.get("label"),
        "label": node.get("label"),
        "object_name": node.get("label"),
        "source_name": node.get("label"),
        "source_path": node.get("id"),
        "description": f"Migrate SSIS package {node.get('label')} to {target_tech}",
        "business_entity": node.get("business_entity"),
        "target_table": node.get("target_name"),
        "target_name": node.get("target_name"),
        "source_tech": "ssis",
        "target_tech": target_tech,
        "tech_id": target_tech,
        "layer": layer,
        "support_intelligence": [],
        "scout_assessment": {},
        "metadata": node.get("metadata", {}),
    }


async def evaluate_target(
    tenant_id: str,
    project_name: str,
    node: dict,
    target_tech: str,
    layer: str,
) -> dict:
    agent_c = AgentCService(tenant_id=tenant_id)
    agent_f = AgentFService(tenant_id=tenant_id)

    task_info = build_task_info(node, project_name, target_tech, layer)
    context = {
        "project_id": project_name,
        "solution_name": project_name,
    }

    c_result = await agent_c.transpile_task(task_info, context=context)
    generated_code = extract_code(c_result)

    f_result = None
    if generated_code:
        f_result = await agent_f.review_code(task_info, generated_code, project_id=project_name)

    return {
        "target_tech": target_tech,
        "layer": layer,
        "task_info": task_info,
        "agent_c": c_result,
        "generated_code_length": len(generated_code),
        "agent_f": f_result,
    }


async def main():
    args = parse_args()
    report = load_mesh_report()

    project_name = report["project_name"]
    mesh = report["agent_a"]["result"]["mesh_graph"]
    selected_node = find_node(mesh, args.node_label)

    evaluations = []
    for target_spec in args.targets:
        if ":" in target_spec:
            target_tech, layer = target_spec.split(":", 1)
        else:
            target_tech, layer = target_spec, "direct"
        evaluations.append(
            await evaluate_target(args.tenant_id, project_name, selected_node, target_tech, layer)
        )

    transformations = []
    for item in evaluations:
        transformations.append(
            {
                "node_label": selected_node.get("label"),
                "target_tech": item["target_tech"],
                "layer": item["layer"],
                "generated_code": extract_code(item["agent_c"]),
                "validation": item["agent_c"].get("validation"),
                "critic": item["agent_f"],
            }
        )

    agent_g = AgentGService(tenant_id=args.tenant_id)
    governance = await agent_g.generate_governance(
        project_name=project_name,
        mesh=mesh,
        transformations=transformations,
        metadata={
            "fixture_report": str(EVAL_REPORT_PATH),
            "evaluated_node": selected_node,
            "targets": args.targets,
        },
    )

    pipeline_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tenant_id": args.tenant_id,
        "project_name": project_name,
        "node_label": args.node_label,
        "targets": args.targets,
        "source_report": str(EVAL_REPORT_PATH),
        "selected_node": selected_node,
        "evaluations": evaluations,
        "governance": governance,
    }

    PIPELINE_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PIPELINE_REPORT_PATH.write_text(json.dumps(pipeline_report, indent=2), encoding="utf-8")

    summary = {
        "report_path": str(PIPELINE_REPORT_PATH),
        "tenant_id": args.tenant_id,
        "project_name": project_name,
        "node_label": args.node_label,
        "targets": [
            {
                "target_tech": item["target_tech"],
                "layer": item["layer"],
                "generated_code_length": item["generated_code_length"],
                "agent_c_valid": item["agent_c"].get("validation", {}).get("is_valid"),
                "agent_f_score": (item["agent_f"] or {}).get("score"),
            }
            for item in evaluations
        ],
        "governance_error": governance.get("error") if isinstance(governance, dict) else None,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
