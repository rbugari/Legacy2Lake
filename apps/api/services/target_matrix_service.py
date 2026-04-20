from __future__ import annotations

import json
import os
import time
import zipfile
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib import error, parse, request


ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = ROOT / "test_results" / "target_matrix_runs"
STATUS_FILENAME = "matrix_run_status.json"
SUMMARY_FILENAME = "matrix_summary.json"
MANIFEST_FILENAME = "matrix_manifest.json"

DEFAULT_BASE_URL = os.getenv("UTM_API_BASE_URL", "http://localhost:8085").rstrip("/")
DEFAULT_TARGETS = [
    "aws",
    "databricks",
    "dbt",
    "gcp",
    "ms_fabric",
    "ms_fabric_sql",
    "pyspark",
    "salesforce",
    "snowflake",
    "snowflake_sql",
]
DEFAULT_MODES = [
    "drafting_delivery",
    "structured_refinement",
    "intelligent_reengineering",
]
DEFAULT_CONTENT_STAGES = ["drafting", "refinement"]
DEFAULT_TEXT_EXTENSIONS = {
    ".sql",
    ".py",
    ".json",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".csv",
    ".log",
    ".xml",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".sh",
    ".ps1",
    ".bat",
}
STAGE_MARKERS = ("source", "triage", "drafting", "refinement", "certification", "handover")
ROOT_LOG_FILES = {"migration.log", "refinement.log", "triage.log"}


@dataclass
class ApiClient:
    base_url: str
    tenant_id: str
    timeout: int

    def json_request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        query: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        response = self.raw_request(method=method, path=path, payload=payload, query=query)
        body = response["body"]
        if not body:
            return {}
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Respuesta JSON invalida en {path}: {exc}") from exc

    def raw_request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        query: Optional[Dict[str, Any]] = None,
        accept: str = "application/json",
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if query:
            encoded = parse.urlencode({k: v for k, v in query.items() if v is not None}, doseq=True)
            url = f"{url}?{encoded}"

        headers = {
            "Accept": accept,
            "X-Tenant-ID": self.tenant_id,
        }
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")

        req = request.Request(url=url, data=data, headers=headers, method=method.upper())

        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                return {
                    "status": resp.status,
                    "body": resp.read(),
                    "headers": dict(resp.headers.items()),
                }
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} en {method.upper()} {url}: {body[:1200]}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"No se pudo conectar a {url}: {exc.reason}") from exc


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_slug(value: str) -> str:
    return "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in value.strip().lower())


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def write_bytes(path: Path, content: bytes) -> None:
    ensure_dir(path.parent)
    path.write_bytes(content)


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def derive_local_artifact_path(remote_path: str) -> Path:
    normalized = remote_path.replace("\\", "/").strip("/")
    lower = normalized.lower()
    for marker in STAGE_MARKERS:
        token = f"/{marker}/"
        index = lower.find(token)
        if index >= 0:
            return Path(normalized[index + 1 :])
        if lower.startswith(f"{marker}/"):
            return Path(normalized)
    parts = [part for part in normalized.split("/") if part]
    if len(parts) >= 2:
        return Path(*parts[-2:])
    return Path(parts[0] if parts else "artifact.bin")


def flatten_tree(tree: Dict[str, Any]) -> List[Dict[str, Any]]:
    files: List[Dict[str, Any]] = []

    def _walk(node: Dict[str, Any]) -> None:
        node_type = node.get("type")
        if node_type == "file":
            files.append(node)
            return
        for child in node.get("children", []) or []:
            _walk(child)

    _walk(tree)
    return files


def is_text_file(path: str) -> bool:
    suffix = Path(path).suffix.lower()
    return suffix in DEFAULT_TEXT_EXTENSIONS or suffix == ""


def detect_stage(remote_path: str) -> str:
    lower_path = remote_path.replace("\\", "/").lower()
    return next(
        (marker for marker in STAGE_MARKERS if f"/{marker}/" in lower_path or lower_path.startswith(f"{marker}/")),
        "other",
    )


def should_download_content(remote_path: str, stage: str, included_stages: Iterable[str]) -> bool:
    filename = Path(remote_path).name.lower()
    included = {item.strip().lower() for item in included_stages if item and item.strip()}
    return stage in included or filename in ROOT_LOG_FILES


def parse_content_disposition(headers: Dict[str, Any]) -> Optional[str]:
    disposition = str(headers.get("Content-Disposition") or headers.get("content-disposition") or "")
    if "filename=" not in disposition:
        return None
    filename = disposition.split("filename=", 1)[1].strip().strip('"')
    return filename or None


def get_project_status(client: ApiClient, project_id: str) -> Dict[str, Any]:
    return client.json_request("GET", f"/discovery/status/{project_id}")


def get_project_metadata(client: ApiClient, project_id: str) -> Dict[str, Any]:
    return client.json_request("GET", f"/projects/{project_id}")


def get_execution_logs(client: ApiClient, project_id: str, phase_type: str) -> str:
    payload = client.json_request("GET", f"/projects/{project_id}/execution-logs", query={"type": phase_type})
    return str(payload.get("logs") or "")


def reset_project(client: ApiClient, project_id: str) -> Dict[str, Any]:
    return client.json_request("POST", f"/projects/{project_id}/reset", query={"backup": "false"})


def approve_project(client: ApiClient, project_id: str) -> Dict[str, Any]:
    return client.json_request("POST", f"/projects/{project_id}/approve")


def update_target(client: ApiClient, project_id: str, target: str) -> None:
    client.json_request("PATCH", f"/projects/{project_id}/settings", payload={"target_tech": target})
    client.json_request(
        "POST",
        f"/projects/{project_id}/registry",
        payload={"category": "PATHS", "key": "target_stack", "value": target},
    )


def set_post_drafting_mode(client: ApiClient, project_id: str, mode: str) -> Dict[str, Any]:
    return client.json_request("POST", f"/projects/{project_id}/set-post-drafting-mode", payload={"mode": mode})


def start_drafting(client: ApiClient, project_id: str, drafting_limit: int) -> Dict[str, Any]:
    return client.json_request(
        "POST",
        "/transpile/orchestrate",
        payload={"project_id": project_id, "limit": drafting_limit},
    )


def start_refinement(client: ApiClient, project_id: str) -> Dict[str, Any]:
    return client.json_request("POST", "/refine/start", payload={"project_id": project_id})


def wait_for_phase(
    client: ApiClient,
    project_id: str,
    phase_type: str,
    desired_statuses: Iterable[str],
    output_dir: Path,
    timeout_seconds: int,
    poll_seconds: int,
    in_progress_statuses: Iterable[str] = (),
) -> Dict[str, Any]:
    """Espera a que la fase alcance uno de desired_statuses.

    in_progress_statuses: si se informa, la primera vez que el servidor
    transite a uno de estos estados (e.g. ORCHESTRATING) el deadline se
    reinicia a time.time() + timeout_seconds. Esto evita que el timeout
    expire mientras el servidor estaba en cola antes de procesar.
    """
    desired = set(desired_statuses)
    in_progress = {s.upper() for s in in_progress_statuses}
    deadline = time.time() + timeout_seconds
    active_deadline_set = not in_progress  # si no hay in_progress, no resetear
    last_logs = ""
    last_status: Dict[str, Any] = {}
    last_metadata: Dict[str, Any] = {}

    while time.time() < deadline:
        last_logs = get_execution_logs(client, project_id, phase_type)
        write_text(output_dir / f"{phase_type}_execution_logs.txt", last_logs)

        last_status = get_project_status(client, project_id)
        last_metadata = get_project_metadata(client, project_id)
        write_json(
            output_dir / f"{phase_type}_status_snapshot.json",
            {
                "captured_at": utc_now(),
                "phase_type": phase_type,
                "status": last_status,
                "project": last_metadata,
            },
        )

        current_status = str(last_status.get("status", "")).upper()

        if current_status in desired:
            return {
                "completed_at": utc_now(),
                "phase_type": phase_type,
                "status": last_status,
                "project": last_metadata,
                "logs_lines": len([line for line in last_logs.splitlines() if line.strip()]),
            }

        if not active_deadline_set and current_status in in_progress:
            # El servidor acaba de empezar a procesar: reiniciamos el deadline
            # para darle el timeout_seconds completo desde este momento.
            deadline = time.time() + timeout_seconds
            active_deadline_set = True

        time.sleep(poll_seconds)

    raise TimeoutError(
        f"Timeout esperando {phase_type} para {project_id}. "
        f"Ultimo status={last_status.get('status')}"
    )


def capture_storage_snapshot(
    client: ApiClient,
    project_id: str,
    output_dir: Path,
    snapshot_name: str,
    max_text_bytes: int,
    content_stages: Iterable[str],
) -> Dict[str, Any]:
    tree = client.json_request("GET", f"/projects/{project_id}/files")
    snapshot_dir = ensure_dir(output_dir / snapshot_name)
    write_json(snapshot_dir / "tree.json", tree)

    files = flatten_tree(tree)
    file_index: List[Dict[str, Any]] = []
    stage_counts: Dict[str, int] = {}
    text_files_saved = 0
    skipped_content = 0
    included_stages = [item.strip().lower() for item in content_stages if item and item.strip()]

    for node in files:
        remote_path = str(node.get("path") or "")
        local_rel = derive_local_artifact_path(remote_path)
        stage = detect_stage(remote_path)
        stage_counts[stage] = stage_counts.get(stage, 0) + 1

        index_entry = {
            "name": node.get("name"),
            "path": remote_path,
            "type": node.get("type"),
            "stage": stage,
            "local_relative_path": str(local_rel).replace("\\", "/"),
        }

        if is_text_file(remote_path) and should_download_content(remote_path, stage, included_stages):
            content_payload = client.json_request(
                "GET",
                f"/projects/{project_id}/files/content",
                query={"path": remote_path},
            )
            content = str(content_payload.get("content") or "")
            index_entry["text_length"] = len(content)

            if len(content.encode("utf-8")) <= max_text_bytes:
                write_text(snapshot_dir / "contents" / local_rel, content)
                text_files_saved += 1
            else:
                index_entry["content_skipped"] = "too_large"
                skipped_content += 1
        elif is_text_file(remote_path):
            index_entry["content_skipped"] = "filtered_stage"
            skipped_content += 1
        else:
            index_entry["content_skipped"] = "non_text"
            skipped_content += 1

        file_index.append(index_entry)

    write_json(
        snapshot_dir / "index.json",
        {
            "captured_at": utc_now(),
            "snapshot_name": snapshot_name,
            "content_stages": included_stages,
            "total_files": len(file_index),
            "text_files_saved": text_files_saved,
            "skipped_content": skipped_content,
            "stage_counts": stage_counts,
            "files": file_index,
        },
    )

    return {
        "snapshot_name": snapshot_name,
        "content_stages": included_stages,
        "total_files": len(file_index),
        "text_files_saved": text_files_saved,
        "skipped_content": skipped_content,
        "stage_counts": stage_counts,
    }


def download_export_bundle(
    client: ApiClient,
    project_id: str,
    export_kind: str,
    output_dir: Path,
    combo_prefix: str,
) -> Dict[str, Any]:
    try:
        response = client.raw_request(
            "GET",
            f"/projects/{project_id}/export/{export_kind}",
            accept="application/zip",
        )
        filename = parse_content_disposition(response["headers"]) or f"{combo_prefix}_{export_kind}.zip"
        local_path = output_dir / filename
        write_bytes(local_path, response["body"])
        return {
            "success": True,
            "export_kind": export_kind,
            "filename": filename,
            "saved_at": str(local_path),
            "bytes": len(response["body"]),
        }
    except Exception as exc:
        return {
            "success": False,
            "export_kind": export_kind,
            "error": str(exc),
        }


def build_default_matrix_config(supported_targets: Optional[Iterable[Dict[str, Any]]] = None) -> Dict[str, Any]:
    targets = list(supported_targets or [])
    if not targets:
        targets = [
            {
                "tech_id": tech_id,
                "label": tech_id,
                "description": None,
                "role": "TARGET",
                "is_active": True,
            }
            for tech_id in DEFAULT_TARGETS
        ]

    config_targets: Dict[str, Any] = {}
    for item in targets:
        role = str(item.get("role") or "").upper()
        type_value = str(item.get("type") or "")
        if role and role != "TARGET" and type_value != "destination":
            continue

        tech_id = str(item.get("tech_id") or "").strip()
        if not tech_id:
            continue

        config_targets[tech_id] = bool(item.get("is_active", True))

    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "project_id": "",
        "targets": config_targets,
        "modes": {mode: True for mode in DEFAULT_MODES},
        "exports": {
            "download_delivery_zip": True,
            "download_governance_zip": True,
            "package_full_run_zip": True,
        },
        "options": {
            "content_stages": DEFAULT_CONTENT_STAGES,
            "skip_reset_first": False,
            "drafting_limit": 0,
            "phase_timeout_seconds": 1800,
            "poll_seconds": 5,
            "max_text_bytes": 500000,
        },
    }


def build_legacy_matrix_config(
    targets: Iterable[str],
    post_drafting_mode: str,
    content_stages: Iterable[str],
    skip_reset_first: bool,
    drafting_limit: int,
    phase_timeout_seconds: int,
    poll_seconds: int,
    max_text_bytes: int,
    include_delivery_zip: bool = True,
    include_governance_zip: bool = True,
    package_full_run_zip: bool = True,
) -> Dict[str, Any]:
    config = build_default_matrix_config(
        {
            "tech_id": target,
            "label": target,
            "role": "TARGET",
            "is_active": True,
        }
        for target in targets
    )
    for target_id in list(config["targets"].keys()):
        config["targets"][target_id] = True

    config["modes"] = {mode: mode == post_drafting_mode for mode in DEFAULT_MODES}

    config["exports"] = {
        "download_delivery_zip": include_delivery_zip,
        "download_governance_zip": include_governance_zip,
        "package_full_run_zip": package_full_run_zip,
    }
    config["options"] = {
        "content_stages": list(content_stages),
        "skip_reset_first": skip_reset_first,
        "drafting_limit": drafting_limit,
        "phase_timeout_seconds": phase_timeout_seconds,
        "poll_seconds": poll_seconds,
        "max_text_bytes": max_text_bytes,
    }
    return config


def normalize_matrix_config(config: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(config)
    targets = normalized.get("targets") or {}
    global_modes = normalized.get("modes") or {mode: True for mode in DEFAULT_MODES}
    canonical_targets: Dict[str, Dict[str, Any]] = {}

    for target_id, target_entry in targets.items():
        if isinstance(target_entry, bool):
            canonical_targets[target_id] = {
                "enabled": target_entry,
                "label": target_id,
                "description": None,
                "modes": {mode: bool(global_modes.get(mode, False)) for mode in DEFAULT_MODES},
            }
            continue

        if not isinstance(target_entry, dict):
            continue

        target_modes = target_entry.get("modes") or global_modes
        canonical_targets[target_id] = {
            "enabled": bool(target_entry.get("enabled", False)),
            "label": target_entry.get("label") or target_id,
            "description": target_entry.get("description"),
            "modes": {mode: bool(target_modes.get(mode, False)) for mode in DEFAULT_MODES},
        }

    normalized["targets"] = canonical_targets
    normalized["modes"] = {mode: bool(global_modes.get(mode, False)) for mode in DEFAULT_MODES}
    normalized.setdefault("schema_version", 2)
    normalized.setdefault("project_id", "")
    normalized.setdefault(
        "exports",
        {
            "download_delivery_zip": True,
            "download_governance_zip": True,
            "package_full_run_zip": True,
        },
    )
    normalized.setdefault(
        "options",
        {
            "content_stages": DEFAULT_CONTENT_STAGES,
            "skip_reset_first": False,
            "drafting_limit": 0,
            "phase_timeout_seconds": 1800,
            "poll_seconds": 5,
            "max_text_bytes": 500000,
        },
    )
    return normalized


def build_execution_plan(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    normalized_config = normalize_matrix_config(config)
    targets = normalized_config.get("targets") or {}
    plan: List[Dict[str, Any]] = []
    for target_id, target_entry in targets.items():
        if not isinstance(target_entry, dict) or not target_entry.get("enabled", False):
            continue
        modes = target_entry.get("modes") or {}
        for mode in DEFAULT_MODES:
            if modes.get(mode, False):
                plan.append(
                    {
                        "target": target_id,
                        "mode": mode,
                        "label": target_entry.get("label") or target_id,
                    }
                )
    return plan


def resolve_project_context(project_id: str) -> Dict[str, Any]:
    try:
        from apps.api.services.persistence_service import SupabasePersistence
    except ImportError:
        from .persistence_service import SupabasePersistence

    async def _resolve() -> Dict[str, Any]:
        db = SupabasePersistence()
        metadata = await db.get_project_metadata(project_id)
        return metadata or {}

    metadata = asyncio.run(_resolve())
    if not metadata:
        raise ValueError(f"No se pudo resolver el proyecto {project_id}")
    return metadata


def create_run_bundle(run_root: Path, bundle_name: Optional[str] = None) -> Path:
    downloads_dir = ensure_dir(run_root / "downloads")
    bundle_path = downloads_dir / (bundle_name or f"{run_root.name}_bundle.zip")

    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zip_handle:
        for file_path in sorted(run_root.rglob("*")):
            if not file_path.is_file():
                continue
            if file_path.resolve() == bundle_path.resolve():
                continue
            arcname = file_path.relative_to(run_root)
            zip_handle.write(file_path, arcname.as_posix())

    return bundle_path


class TargetMatrixRunner:
    def __init__(self, base_url: str, tenant_id: str, request_timeout_seconds: int = 120):
        self.client = ApiClient(base_url=base_url.rstrip("/"), tenant_id=tenant_id, timeout=request_timeout_seconds)

    def _project_root(self, project_id: str, run_label: Optional[str] = None) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        suffix = safe_slug(run_label or project_id)
        return ensure_dir(OUTPUT_ROOT / safe_slug(project_id) / f"{timestamp}_{suffix}")

    def _write_status(self, run_root: Path, payload: Dict[str, Any]) -> None:
        write_json(run_root / STATUS_FILENAME, payload)

    def run_config(
        self,
        project_id: str,
        config: Dict[str, Any],
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        config = normalize_matrix_config(config)
        run_root = Path(output_dir) if output_dir else self._project_root(project_id, "matrix")
        ensure_dir(run_root)

        plan = build_execution_plan(config)
        if not plan:
            raise ValueError("La configuracion no habilita ninguna combinacion target + modo")

        options = config.get("options") or {}
        exports = config.get("exports") or {}
        summary: Dict[str, Any] = {
            "generated_at": utc_now(),
            "project_id": project_id,
            "run_root": str(run_root),
            "plan": plan,
            "results": [],
            "failures": [],
            "status": "RUNNING",
            "bundle_path": None,
        }

        manifest = {
            "generated_at": utc_now(),
            "project_id": project_id,
            "config": config,
            "plan": plan,
            "output_dir": str(run_root),
        }
        write_json(run_root / MANIFEST_FILENAME, manifest)
        self._write_status(run_root, summary)

        for index, combo in enumerate(plan):
            try:
                result = self.run_combination(
                    project_id=project_id,
                    combo=combo,
                    run_root=run_root,
                    drafting_limit=int(options.get("drafting_limit", 0) or 0),
                    timeout_seconds=int(options.get("phase_timeout_seconds", 1800) or 1800),
                    poll_seconds=int(options.get("poll_seconds", 5) or 5),
                    max_text_bytes=int(options.get("max_text_bytes", 500000) or 500000),
                    content_stages=options.get("content_stages") or DEFAULT_CONTENT_STAGES,
                    do_reset=not (index == 0 and bool(options.get("skip_reset_first", False))),
                    include_delivery_zip=bool(exports.get("download_delivery_zip", True)),
                    include_governance_zip=bool(exports.get("download_governance_zip", True)),
                )
                summary["results"].append(result)
            except Exception as exc:
                failure = {
                    "target": combo.get("target"),
                    "mode": combo.get("mode"),
                    "failed_at": utc_now(),
                    "error": str(exc),
                }
                summary["failures"].append(failure)
                combo_dir = ensure_dir(run_root / safe_slug(f"{combo.get('target')}__{combo.get('mode')}"))
                write_json(combo_dir / "failure.json", failure)
            self._write_status(run_root, {**summary, "status": "RUNNING"})

        bundle_path = None
        if bool(exports.get("package_full_run_zip", True)):
            bundle_path = create_run_bundle(run_root)

        summary["generated_at"] = utc_now()
        summary["status"] = "COMPLETED_WITH_ERRORS" if summary["failures"] else "COMPLETED"
        summary["bundle_path"] = str(bundle_path) if bundle_path else None
        write_json(run_root / SUMMARY_FILENAME, summary)
        self._write_status(run_root, summary)
        return summary

    def run_combination(
        self,
        project_id: str,
        combo: Dict[str, Any],
        run_root: Path,
        drafting_limit: int,
        timeout_seconds: int,
        poll_seconds: int,
        max_text_bytes: int,
        content_stages: Iterable[str],
        do_reset: bool,
        include_delivery_zip: bool,
        include_governance_zip: bool,
    ) -> Dict[str, Any]:
        target = str(combo["target"])
        post_drafting_mode = str(combo["mode"])
        combo_slug = safe_slug(f"{target}__{post_drafting_mode}")
        combo_dir = ensure_dir(run_root / combo_slug)
        lifecycle: List[Dict[str, Any]] = []

        if do_reset:
            lifecycle.append({"step": "reset", "at": utc_now(), "result": reset_project(self.client, project_id)})

        lifecycle.append({"step": "update_target", "at": utc_now(), "target": target})
        update_target(self.client, project_id, target)

        lifecycle.append({"step": "approve", "at": utc_now(), "result": approve_project(self.client, project_id)})

        drafting_start = start_drafting(self.client, project_id, drafting_limit)
        lifecycle.append({"step": "start_drafting", "at": utc_now(), "result": drafting_start})

        drafting_result = wait_for_phase(
            client=self.client,
            project_id=project_id,
            phase_type="migration",
            desired_statuses=["DRAFTED", "REFINING", "REFINED", "CERTIFYING", "CERTIFIED", "GOVERNED", "DELIVERED"],
            output_dir=combo_dir,
            timeout_seconds=timeout_seconds,
            poll_seconds=poll_seconds,
            in_progress_statuses=["ORCHESTRATING"],
        )
        lifecycle.append({"step": "drafting_complete", "at": utc_now(), "result": drafting_result})

        mode_result = set_post_drafting_mode(self.client, project_id, post_drafting_mode)
        lifecycle.append({"step": "set_post_drafting_mode", "at": utc_now(), "result": mode_result})

        drafting_snapshot = capture_storage_snapshot(
            client=self.client,
            project_id=project_id,
            output_dir=combo_dir,
            snapshot_name="after_drafting",
            max_text_bytes=max_text_bytes,
            content_stages=content_stages,
        )

        refinement_result: Optional[Dict[str, Any]] = None
        refinement_snapshot: Optional[Dict[str, Any]] = None
        refinement_skipped_reason: Optional[str] = None

        if post_drafting_mode == "drafting_delivery":
            refinement_skipped_reason = "drafting_delivery_mode"
            lifecycle.append(
                {
                    "step": "skip_refinement",
                    "at": utc_now(),
                    "reason": refinement_skipped_reason,
                }
            )
        else:
            refinement_start = start_refinement(self.client, project_id)
            lifecycle.append({"step": "start_refinement", "at": utc_now(), "result": refinement_start})

            refinement_result = wait_for_phase(
                client=self.client,
                project_id=project_id,
                phase_type="refinement",
                desired_statuses=["REFINED", "CERTIFYING", "CERTIFIED", "GOVERNED", "DELIVERED"],
                output_dir=combo_dir,
                timeout_seconds=timeout_seconds,
                poll_seconds=max(3, poll_seconds),
            )
            lifecycle.append({"step": "refinement_complete", "at": utc_now(), "result": refinement_result})

            refinement_snapshot = capture_storage_snapshot(
                client=self.client,
                project_id=project_id,
                output_dir=combo_dir,
                snapshot_name="after_refinement",
                max_text_bytes=max_text_bytes,
                content_stages=content_stages,
            )

        export_results: List[Dict[str, Any]] = []
        exports_dir = ensure_dir(combo_dir / "downloads")
        combo_prefix = combo_slug
        if include_delivery_zip:
            export_results.append(download_export_bundle(self.client, project_id, "delivery", exports_dir, combo_prefix))
        if include_governance_zip:
            export_results.append(download_export_bundle(self.client, project_id, "governance", exports_dir, combo_prefix))

        result = {
            "target": target,
            "target_slug": safe_slug(target),
            "started_at": lifecycle[0]["at"] if lifecycle else utc_now(),
            "completed_at": utc_now(),
            "post_drafting_mode": post_drafting_mode,
            "drafting": drafting_result,
            "refinement": refinement_result,
            "refinement_skipped_reason": refinement_skipped_reason,
            "drafting_snapshot": drafting_snapshot,
            "refinement_snapshot": refinement_snapshot,
            "exports": export_results,
            "lifecycle": lifecycle,
        }
        write_json(combo_dir / "run_summary.json", result)
        return result


def list_matrix_runs(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    base_dir = OUTPUT_ROOT / safe_slug(project_id) if project_id else OUTPUT_ROOT
    if not base_dir.exists():
        return []

    statuses: List[Tuple[float, Dict[str, Any]]] = []
    for status_path in base_dir.rglob(STATUS_FILENAME):
        try:
            payload = read_json(status_path)
            statuses.append((status_path.stat().st_mtime, payload))
        except Exception:
            continue

    return [payload for _, payload in sorted(statuses, key=lambda item: item[0], reverse=True)]


def load_matrix_run(project_id: str, run_id: str) -> Dict[str, Any]:
    run_root = OUTPUT_ROOT / safe_slug(project_id) / run_id
    status_path = run_root / STATUS_FILENAME
    if not status_path.exists():
        raise FileNotFoundError(f"No existe la corrida {run_id} para el proyecto {project_id}")
    payload = read_json(status_path)
    payload["run_root"] = str(run_root)
    return payload