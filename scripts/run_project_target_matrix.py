import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.services.target_matrix_service import (
    DEFAULT_BASE_URL,
    DEFAULT_CONTENT_STAGES,
    DEFAULT_TARGETS,
    TargetMatrixRunner,
    build_default_matrix_config,
    build_legacy_matrix_config,
    resolve_project_context,
)
OUTPUT_ROOT = ROOT / "test_results" / "target_matrix"
DEFAULT_MODE = "structured_refinement"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Ejecuta un mismo proyecto contra multiples salidas target, relanzando Drafting y Refinement, "
            "y captura logs mas artefactos reales desde storage."
        )
    )
    parser.add_argument("--project-id", required=False, help="UUID o nombre del proyecto a barrer.")
    parser.add_argument("--tenant-id", required=False, help="Tenant UUID valido para la API.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL de la API.")
    parser.add_argument(
        "--role",
        default="ADMIN",
        choices=["COLLABORATOR", "MANAGER", "ADMIN", "VIEWER"],
        help="Rol enviado en X-Role para ejecutar fases.",
    )
    parser.add_argument("--user-id", default=None, help="X-User-ID opcional.")
    parser.add_argument("--client-id", default="target-matrix", help="X-Client-ID opcional.")
    parser.add_argument(
        "--targets",
        nargs="*",
        default=DEFAULT_TARGETS,
        help="Lista de salidas target a ejecutar.",
    )
    parser.add_argument(
        "--post-drafting-mode",
        default=DEFAULT_MODE,
        choices=["structured_refinement", "intelligent_reengineering", "drafting_delivery"],
        help="Modo post-Drafting a aplicar antes de Refinement.",
    )
    parser.add_argument(
        "--drafting-limit",
        type=int,
        default=0,
        help="Limite opcional para orquestacion de Drafting.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=5,
        help="Intervalo de polling para status y logs.",
    )
    parser.add_argument(
        "--phase-timeout-seconds",
        type=int,
        default=1800,
        help="Timeout por fase (Drafting o Refinement).",
    )
    parser.add_argument(
        "--request-timeout-seconds",
        type=int,
        default=120,
        help="Timeout por request HTTP.",
    )
    parser.add_argument(
        "--max-text-bytes",
        type=int,
        default=500_000,
        help="Maximo de bytes a persistir por archivo textual leido desde storage.",
    )
    parser.add_argument(
        "--content-stages",
        nargs="*",
        default=DEFAULT_CONTENT_STAGES,
        help=(
            "Stages cuyo contenido textual se descarga en cada snapshot. "
            "El tree completo siempre se guarda, aunque no se descargue el contenido."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directorio base donde guardar el barrido. Default: test_results/target_matrix/<timestamp>.",
    )
    parser.add_argument(
        "--config-file",
        default=None,
        help="Archivo JSON con la matriz booleana de targets + modos.",
    )
    parser.add_argument(
        "--write-config-template",
        default=None,
        help="Si se informa una ruta, escribe una plantilla de configuracion JSON y termina.",
    )
    parser.add_argument(
        "--skip-reset-first",
        action="store_true",
        help="No hace reset antes del primer target. Los siguientes siempre resetean.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.write_config_template:
        template = build_default_matrix_config()
        target_path = Path(args.write_config_template)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(json.dumps(template, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps({"template_written": str(target_path)}, indent=2))
        return 0

    if args.config_file:
        config = json.loads(Path(args.config_file).read_text(encoding="utf-8"))
    else:
        config = build_legacy_matrix_config(
            targets=args.targets,
            post_drafting_mode=args.post_drafting_mode,
            content_stages=args.content_stages,
            skip_reset_first=args.skip_reset_first,
            drafting_limit=args.drafting_limit,
            phase_timeout_seconds=args.phase_timeout_seconds,
            poll_seconds=args.poll_seconds,
            max_text_bytes=args.max_text_bytes,
        )

    project_id = args.project_id or config.get("project_id")
    if not project_id:
        raise SystemExit("Debe indicar --project-id o definir project_id en el archivo JSON")

    config["project_id"] = project_id

    tenant_id = args.tenant_id
    if not tenant_id:
        project_context = resolve_project_context(project_id)
        tenant_id = project_context.get("tenant_id")
        if not tenant_id:
            raise SystemExit(f"No se pudo resolver tenant_id para el proyecto {project_id}")

    runner = TargetMatrixRunner(
        base_url=args.base_url,
        tenant_id=tenant_id,
        request_timeout_seconds=args.request_timeout_seconds,
        role=args.role,
        user_id=args.user_id,
        client_id=args.client_id,
    )
    summary = runner.run_config(
        project_id=project_id,
        config=config,
        output_dir=args.output_dir,
    )

    print(json.dumps({
        "output_dir": summary.get("run_root"),
        "project_id": project_id,
        "tenant_id": tenant_id,
        "combinations_requested": len(summary.get("plan", [])),
        "combinations_completed": len(summary.get("results", [])),
        "combinations_failed": len(summary.get("failures", [])),
        "bundle_path": summary.get("bundle_path"),
        "status": summary.get("status"),
    }, indent=2))

    return 0 if not summary.get("failures") else 1


if __name__ == "__main__":
    raise SystemExit(main())