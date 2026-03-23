import asyncio
import json
import os
import shutil
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path
import argparse


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ["STORAGE_PROVIDER"] = "LOCAL"
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from apps.api.services.discovery_service import DiscoveryService
from apps.api.services.quick_assessment_service import QuickAssessmentService
from apps.api.services.agent_a_service import AgentAService
from apps.api.services.storage.factory import StorageFactory


FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "ssis_test_repo"
PROJECT_NAME = "ssistestrepoeval"
REPORT_PATH = ROOT / "test_results" / "ssis_fixture_evaluation.json"
DEFAULT_TENANT_ID = os.getenv("EVAL_TENANT_ID")


def build_solution_source(tenant_id: str | None) -> Path:
    if tenant_id:
        return ROOT / "solutions" / tenant_id / PROJECT_NAME / "source"
    return ROOT / "solutions" / PROJECT_NAME / "source"


def prepare_fixture_project(tenant_id: str | None) -> Path:
    solutions_source = build_solution_source(tenant_id)
    if solutions_source.parent.exists():
        def onerror(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        shutil.rmtree(solutions_source.parent, onerror=onerror)

    solutions_source.mkdir(parents=True, exist_ok=True)

    for item in FIXTURE_ROOT.iterdir():
        target = solutions_source / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)

    return solutions_source


def build_manifest(tenant_id: str | None):
    manifest = DiscoveryService.generate_manifest(
        PROJECT_NAME,
        tenant_id=tenant_id,
        source_folder="source",
    )

    file_inventory = manifest.get("file_inventory", [])
    manifest_summary = {
        "root_path": manifest.get("root_path"),
        "total_files": len(file_inventory),
        "tech_stats": manifest.get("tech_stats", {}),
        "support_intelligence_count": len(manifest.get("support_intelligence", [])),
        "sample_files": [item.get("name") for item in file_inventory[:10]],
        "file_types": {},
    }

    for item in file_inventory:
        manifest_summary["file_types"][item["type"]] = manifest_summary["file_types"].get(item["type"], 0) + 1

    return manifest, manifest_summary


async def run_quick_assessment(tenant_id: str | None):
    service = QuickAssessmentService(tenant_id=tenant_id)
    result = await service.assess(PROJECT_NAME)
    return result.model_dump()


async def run_agent_a(manifest, tenant_id: str | None):
    agent = AgentAService(tenant_id=tenant_id)
    try:
        result = await agent.analyze_manifest(manifest)
        return {
            "status": "ok",
            "result": result,
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc),
        }


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate the SSIS fixture end-to-end.")
    parser.add_argument("--tenant-id", default=DEFAULT_TENANT_ID, help="Tenant UUID to use for LLM resolution.")
    return parser.parse_args()


async def main():
    args = parse_args()
    tenant_id = args.tenant_id
    StorageFactory._instance = None
    solutions_source = prepare_fixture_project(tenant_id)
    manifest, manifest_summary = build_manifest(tenant_id)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fixture_root": str(FIXTURE_ROOT),
        "project_name": PROJECT_NAME,
        "tenant_id": tenant_id,
        "prepared_source": str(solutions_source),
        "manifest_summary": manifest_summary,
        "quick_assessment": await run_quick_assessment(tenant_id),
        "agent_a": await run_agent_a(manifest, tenant_id),
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps({
        "report_path": str(REPORT_PATH),
        "project_name": PROJECT_NAME,
        "manifest_files": manifest_summary["total_files"],
        "quick_assessment_score": report["quick_assessment"]["score"],
        "quick_assessment_semaforo": report["quick_assessment"]["semaforo"],
        "agent_a_status": report["agent_a"]["status"],
    }, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
