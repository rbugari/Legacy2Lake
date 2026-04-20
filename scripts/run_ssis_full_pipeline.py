import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL_REPORT = ROOT / "test_results" / "ssis_fixture_evaluation.json"
SUMMARY_REPORT = ROOT / "test_results" / "ssis_full_pipeline_summary.json"

DEFAULT_TENANT_ID = os.getenv("EVAL_TENANT_ID", "f98edb5e-4165-4c49-9fce-18894e8a818c")
DEFAULT_TARGETS = ["snowflake_sql:direct", "pyspark:direct"]


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True)


def run_fixture(tenant_id: str) -> dict:
    cmd = [
        sys.executable,
        "scripts/evaluate_ssis_fixture.py",
        "--tenant-id",
        tenant_id,
    ]
    result = _run(cmd)

    if result.returncode != 0:
        raise RuntimeError(
            "Fixture evaluation failed.\n"
            f"Command: {' '.join(cmd)}\n"
            f"Stdout:\n{result.stdout}\n"
            f"Stderr:\n{result.stderr}"
        )

    if not EVAL_REPORT.exists():
        raise FileNotFoundError(f"Expected evaluation report not found: {EVAL_REPORT}")

    data = json.loads(EVAL_REPORT.read_text(encoding="utf-8"))
    return {
        "command": cmd,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "report": data,
    }


def get_mesh_nodes(eval_report: dict) -> list[str]:
    agent_a = eval_report.get("agent_a", {})
    status = agent_a.get("status")
    agent_result = agent_a.get("result", {})
    mesh = agent_result.get("mesh_graph", {})
    nodes = mesh.get("nodes", [])

    if status != "ok":
        raise ValueError(f"Agent A status is not ok: {status}")

    labels = [n.get("label") for n in nodes if n.get("label")]
    if not labels:
        error = agent_result.get("error") or agent_a.get("error") or "unknown"
        raise ValueError(f"Mesh has no nodes. Agent A error: {error}")

    return labels


def run_generation_for_node(tenant_id: str, node_label: str, targets: list[str]) -> dict:
    cmd = [
        sys.executable,
        "scripts/evaluate_ssis_generation_pipeline.py",
        "--tenant-id",
        tenant_id,
        "--node-label",
        node_label,
        "--targets",
        *targets,
    ]
    result = _run(cmd)

    ok = result.returncode == 0
    return {
        "node_label": node_label,
        "ok": ok,
        "returncode": result.returncode,
        "command": cmd,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run full SSIS pipeline: fixture evaluation + Drafting/Governance for mesh nodes."
    )
    parser.add_argument("--tenant-id", default=DEFAULT_TENANT_ID, help="Tenant UUID.")
    parser.add_argument(
        "--targets",
        nargs="*",
        default=DEFAULT_TARGETS,
        help="Target list in target:layer format.",
    )
    parser.add_argument(
        "--max-nodes",
        type=int,
        default=None,
        help="Optional cap for number of nodes (useful for smoke runs).",
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop immediately if one node fails.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    fixture = run_fixture(args.tenant_id)
    eval_report = fixture["report"]
    node_labels = get_mesh_nodes(eval_report)

    if args.max_nodes is not None:
        node_labels = node_labels[: args.max_nodes]

    results = []
    for label in node_labels:
        node_result = run_generation_for_node(args.tenant_id, label, args.targets)
        results.append(node_result)
        if args.stop_on_error and not node_result["ok"]:
            break

    failed = [r for r in results if not r["ok"]]

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tenant_id": args.tenant_id,
        "targets": args.targets,
        "mesh_nodes_total": len(get_mesh_nodes(eval_report)),
        "mesh_nodes_executed": len(results),
        "mesh_nodes_failed": len(failed),
        "fixture_quick_assessment": eval_report.get("quick_assessment", {}),
        "nodes": [
            {
                "node_label": r["node_label"],
                "ok": r["ok"],
                "returncode": r["returncode"],
            }
            for r in results
        ],
    }

    SUMMARY_REPORT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_REPORT.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps({
        "summary_report": str(SUMMARY_REPORT),
        "tenant_id": args.tenant_id,
        "mesh_nodes_total": summary["mesh_nodes_total"],
        "mesh_nodes_executed": summary["mesh_nodes_executed"],
        "mesh_nodes_failed": summary["mesh_nodes_failed"],
    }, indent=2))

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
