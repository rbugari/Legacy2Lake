"""
ProjectAssistantService - v4.5 Sprint 2
Chat assistant scoped to legacy source analysis.
Answers questions grounded in Triage metadata (utm_objects, utm_table_impacts,
utm_asset_columns, understanding_payload). If Triage is incomplete, refuses and
instructs the user to run it first.

History persistence:
  - Messages stored in utm_project_chat_threads + utm_project_chat_messages
  - Thread version increments on triage rerun (invalidates old messages)
  - get_history() returns current thread messages
  - clear_history() deletes all messages for current thread
"""
from typing import Any, Dict, List, Optional
import json

try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence
    except ImportError:
        from ..utils.logger import logger
        from .persistence_service import SupabasePersistence

try:
    from langchain_openai import AzureChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
except ImportError:
    AzureChatOpenAI = None  # type: ignore
    SystemMessage = HumanMessage = None  # type: ignore

# Maximum chars per context block sent to the LLM to avoid token overload
_MAX_OBJECTS_CONTEXT = 8_000
_MAX_IMPACTS_CONTEXT = 4_000
_MAX_COLUMNS_CONTEXT = 3_000

# Intent keywords used for lightweight classification
_INTENT_RULES: list[tuple[str, list[str]]] = [
    ("table_usage",    ["table", "tabla", "where is", "donde se usa", "used in", "usada en", "read", "write", "lee", "escribe"]),
    ("field_usage",    ["field", "column", "campo", "columna", "attribute", "atributo"]),
    ("pii",            ["pii", "personal", "privacy", "privacidad", "sensitive", "sensible", "mask", "mascara"]),
    ("asset_deps",     ["depends", "dependencia", "dependency", "requires", "upstream", "downstream", "dag"]),
    ("readiness",      ["ready", "listo", "viable", "readiness", "blocker", "bloqueo", "risk", "riesgo"]),
]


def _classify_intent(message: str) -> str:
    lower = message.lower()
    for intent, keywords in _INTENT_RULES:
        if any(kw in lower for kw in keywords):
            return intent
    return "general"


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... [truncated]"


class ProjectAssistantService:
    """
    Bounded chat assistant for a single project.
    Retrieves Triage metadata from DB, builds a context-bound prompt,
    and calls the tenant-configured LLM.
    """

    def __init__(self, tenant_id: str, project_id: str):
        self.tenant_id = tenant_id
        self.project_id = project_id
        self.db = SupabasePersistence(tenant_id=tenant_id)

    # ------------------------------------------------------------------
    # Thread management (history persistence)
    # ------------------------------------------------------------------

    def _get_or_create_thread(self) -> str:
        """Returns the current thread id for this project, creating one if needed."""
        try:
            res = (
                self.db.client.table("utm_project_chat_threads")
                .select("id")
                .eq("project_id", self.project_id)
                .eq("tenant_id", self.tenant_id)
                .order("thread_version", desc=True)
                .limit(1)
                .execute()
            )
            rows = res.data or []
            if rows:
                return rows[0]["id"]
        except Exception:
            pass

        # Create new thread
        try:
            res = (
                self.db.client.table("utm_project_chat_threads")
                .insert({
                    "tenant_id": self.tenant_id,
                    "project_id": self.project_id,
                    "thread_version": 1,
                })
                .execute()
            )
            return (res.data or [{}])[0].get("id", "")
        except Exception as exc:
            logger.error(f"[Assistant] Failed to create thread: {exc}", "ProjectAssistant")
            return ""

    def _persist_exchange(self, thread_id: str, message: str, result: Dict[str, Any]) -> None:
        """Save user message + assistant answer to the DB (non-blocking)."""
        if not thread_id:
            return
        try:
            rows = [
                {
                    "tenant_id": self.tenant_id,
                    "project_id": self.project_id,
                    "thread_id": thread_id,
                    "role": "user",
                    "intent": result.get("intent"),
                    "question": message,
                    "answer": None,
                    "confidence": None,
                },
                {
                    "tenant_id": self.tenant_id,
                    "project_id": self.project_id,
                    "thread_id": thread_id,
                    "role": "assistant",
                    "intent": result.get("intent"),
                    "question": message,
                    "answer": result.get("answer"),
                    "confidence": result.get("confidence"),
                },
            ]
            self.db.client.table("utm_project_chat_messages").insert(rows).execute()
        except Exception as exc:
            logger.error(f"[Assistant] Failed to persist messages: {exc}", "ProjectAssistant")

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Returns messages from the current (latest version) thread.
        Returns [ { role, question, answer, intent, confidence, created_at }, ... ]
        """
        try:
            # Get latest thread
            thread_res = (
                self.db.client.table("utm_project_chat_threads")
                .select("id")
                .eq("project_id", self.project_id)
                .eq("tenant_id", self.tenant_id)
                .order("thread_version", desc=True)
                .limit(1)
                .execute()
            )
            rows = thread_res.data or []
            if not rows:
                return []
            thread_id = rows[0]["id"]

            msg_res = (
                self.db.client.table("utm_project_chat_messages")
                .select("role,intent,question,answer,confidence,created_at")
                .eq("thread_id", thread_id)
                .eq("role", "assistant")
                .order("created_at", desc=False)
                .execute()
            )
            return msg_res.data or []
        except Exception as exc:
            logger.error(f"[Assistant] Failed to get history: {exc}", "ProjectAssistant")
            return []

    def clear_history(self) -> Dict[str, Any]:
        """
        Deletes all messages in the current thread and resets (new thread version).
        Returns { cleared: int, new_thread_id: str }
        """
        try:
            # Find current thread
            thread_res = (
                self.db.client.table("utm_project_chat_threads")
                .select("id,thread_version")
                .eq("project_id", self.project_id)
                .eq("tenant_id", self.tenant_id)
                .order("thread_version", desc=True)
                .limit(1)
                .execute()
            )
            rows = thread_res.data or []
            cleared = 0
            if rows:
                old_thread_id = rows[0]["id"]
                # Count messages
                count_res = (
                    self.db.client.table("utm_project_chat_messages")
                    .select("id", count="exact")
                    .eq("thread_id", old_thread_id)
                    .execute()
                )
                cleared = getattr(count_res, "count", len(count_res.data or []))
                # Delete messages (cascade via FK, but explicit for safety)
                self.db.client.table("utm_project_chat_messages").delete().eq("thread_id", old_thread_id).execute()
                # Delete old thread
                self.db.client.table("utm_project_chat_threads").delete().eq("id", old_thread_id).execute()

            # Create new thread
            new_thread_id = self._get_or_create_thread()
            return {"cleared": cleared, "new_thread_id": new_thread_id}
        except Exception as exc:
            logger.error(f"[Assistant] Failed to clear history: {exc}", "ProjectAssistant")
            return {"cleared": 0, "new_thread_id": ""}

    def reset_for_triage_rerun(self) -> None:
        """
        Called by triage rerun completion.
        Creates a new thread version (old messages remain readable but new chats go to new thread).
        """
        try:
            # Get latest thread_version
            thread_res = (
                self.db.client.table("utm_project_chat_threads")
                .select("thread_version")
                .eq("project_id", self.project_id)
                .eq("tenant_id", self.tenant_id)
                .order("thread_version", desc=True)
                .limit(1)
                .execute()
            )
            rows = thread_res.data or []
            next_version = (rows[0]["thread_version"] + 1) if rows else 1

            self.db.client.table("utm_project_chat_threads").insert({
                "tenant_id": self.tenant_id,
                "project_id": self.project_id,
                "thread_version": next_version,
            }).execute()
            logger.info(
                f"[Assistant] Triage rerun: new thread version {next_version} for project={self.project_id}",
                "ProjectAssistant",
            )
        except Exception as exc:
            logger.error(f"[Assistant] Failed to reset thread for triage rerun: {exc}", "ProjectAssistant")

    # ------------------------------------------------------------------
    # Triage gate
    # ------------------------------------------------------------------

    def _triage_is_ready(self) -> bool:
        """
        Returns True when triage analysis is available for this project.
        Accepts two signals:
          1. utm_objects has at least one row (deep triage via Agent-S)
          2. quick_assessment.file_details exists on utm_projects (QuickAssessmentService path)
        """
        try:
            # Path 1: deep triage rows
            res = (
                self.db.client.table("utm_objects")
                .select("object_id", count="exact")
                .eq("project_id", self.project_id)
                .eq("tenant_id", self.tenant_id)
                .limit(1)
                .execute()
            )
            count = getattr(res, "count", None)
            if count is None:
                count = len(res.data or [])
            if count > 0:
                return True
        except Exception:
            pass

        # Path 2: quick_assessment with file_details (triage_approved_at or qa score)
        try:
            res = (
                self.db.client.table("utm_projects")
                .select("quick_assessment,triage_approved_at")
                .eq("project_id", self.project_id)
                .eq("tenant_id", self.tenant_id)
                .limit(1)
                .execute()
            )
            row = (res.data or [{}])[0]
            qa = row.get("quick_assessment") or {}
            if qa.get("file_details") or row.get("triage_approved_at"):
                return True
        except Exception:
            pass

        return False

    # ------------------------------------------------------------------
    # Context builders
    # ------------------------------------------------------------------

    def _fetch_objects_context(self) -> str:
        try:
            res = (
                self.db.client.table("utm_objects")
                .select("source_name,type,category,is_pii,criticality,layer")
                .eq("project_id", self.project_id)
                .eq("tenant_id", self.tenant_id)
                .execute()
            )
            rows = res.data or []
            if rows:
                lines = [f"- {r.get('source_name','?')} | type={r.get('type','-')} | layer={r.get('layer','-')} | criticality={r.get('criticality','-')} | pii={r.get('is_pii',False)}" for r in rows]
                return _truncate("\n".join(lines), _MAX_OBJECTS_CONTEXT)
        except Exception:
            pass

        # Fallback: quick_assessment.file_details
        try:
            res = (
                self.db.client.table("utm_projects")
                .select("quick_assessment")
                .eq("project_id", self.project_id)
                .eq("tenant_id", self.tenant_id)
                .limit(1)
                .execute()
            )
            row = (res.data or [{}])[0]
            qa = row.get("quick_assessment") or {}
            files = qa.get("file_details") or []
            if files:
                lines = [f"- {f.get('filename','?')} | category={f.get('category','-')} | tech={f.get('detected_tech','-')} | complexity={f.get('complexity_hint','-')}" for f in files]
                return _truncate("\n".join(lines), _MAX_OBJECTS_CONTEXT)
        except Exception as exc:
            return f"(error fetching assets: {exc})"

        return "(no assets found)"

    def _fetch_table_impacts_context(self) -> str:
        """
        Returns table impact data. Primary source: utm_table_impacts (Phase C).
        Fallback: source_query and data_flow_analysis extracted from utm_objects during triage.
        """
        try:
            res = (
                self.db.client.table("utm_table_impacts")
                .select("table_name,operation,asset_id")
                .eq("project_id", self.project_id)
                .eq("tenant_id", self.tenant_id)
                .limit(200)
                .execute()
            )
            rows = res.data or []
            if rows:
                lines = [f"- {r.get('table_name','?')} | op={r.get('operation','-')} | asset={r.get('asset_id','-')}" for r in rows]
                return _truncate("\n".join(lines), _MAX_IMPACTS_CONTEXT)
        except Exception:
            pass

        # Fallback: source queries extracted from SSIS during triage
        try:
            res = (
                self.db.client.table("utm_objects")
                .select("source_name,source_query,data_flow_analysis")
                .eq("project_id", self.project_id)
                .eq("tenant_id", self.tenant_id)
                .execute()
            )
            rows = res.data or []
            lines = []
            for r in rows:
                name = r.get("source_name", "?")
                sq = r.get("source_query") or ""
                dfa = r.get("data_flow_analysis") or {}
                if isinstance(dfa, str):
                    try:
                        import json as _json
                        dfa = _json.loads(dfa)
                    except Exception:
                        dfa = {}
                extra_queries = [q.get("query", "") for q in (dfa.get("queries") or []) if q.get("query")]
                all_sql = " | ".join(filter(None, [sq] + extra_queries))
                if all_sql:
                    lines.append(f"- {name}: {all_sql[:400]}")
            if lines:
                header = "[NOTE: Table impact analysis (Phase C) not yet run. Showing raw SQL queries from SSIS assets for reference.]\n"
                return _truncate(header + "\n".join(lines), _MAX_IMPACTS_CONTEXT)
            return "(no table impact data available — run Phase C analysis for detailed table read/write mapping)"
        except Exception as exc:
            return f"(error fetching source queries: {exc})"

    def _fetch_columns_context(self) -> str:
        try:
            res = (
                self.db.client.table("utm_asset_columns")
                .select("column_name,data_type,is_pii,pii_category,partition_candidate")
                .eq("project_id", self.project_id)
                .limit(200)
                .execute()
            )
            rows = res.data or []
            if not rows:
                return "(no column profiles found)"
            lines = [f"- {r.get('column_name','?')} | type={r.get('data_type','-')} | pii={r.get('is_pii',False)} | pii_cat={r.get('pii_category','-')}" for r in rows]
            return _truncate("\n".join(lines), _MAX_COLUMNS_CONTEXT)
        except Exception as exc:
            return f"(error fetching columns: {exc})"

    def _fetch_understanding_context(self) -> str:
        try:
            res = (
                self.db.client.table("utm_projects")
                .select("understanding_payload,name,quick_assessment")
                .eq("project_id", self.project_id)
                .eq("tenant_id", self.tenant_id)
                .limit(1)
                .execute()
            )
            row = (res.data or [{}])[0]
            payload = row.get("understanding_payload") or {}
            qa = row.get("quick_assessment") or {}
            project_name = row.get("name", "unknown")
            parts = [f"Project: {project_name}"]
            if qa.get("score"):
                parts.append(f"Quick assessment score: {qa['score']} ({qa.get('semaforo','?')})")
            if isinstance(payload, dict):
                fmap = payload.get("functional_map") or {}
                omap = payload.get("operational_map") or {}
                rec = payload.get("recommendation_set") or {}
                if fmap.get("domains"):
                    domains = [d.get("name", "?") for d in (fmap.get("domains") or [])]
                    parts.append(f"Functional domains: {', '.join(domains)}")
                if omap.get("processes"):
                    processes = [p.get("name", "?") for p in (omap.get("processes") or [])]
                    parts.append(f"Processes: {', '.join(processes[:10])}")
                if rec.get("items"):
                    items = [i.get("recommendation", "?") for i in (rec.get("items") or [])]
                    parts.append(f"Key recommendations: {'; '.join(items[:5])}")
            return "\n".join(parts)
        except Exception as exc:
            return f"(error fetching understanding: {exc})"

    # ------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------

    async def _get_llm(self):
        resolved = await self.db.resolve_agent_model("agent-a")
        if not resolved:
            raise ValueError(
                f"LLM not configured for tenant {self.tenant_id}. "
                "Check Agent Matrix and Provider Vault."
            )
        provider = resolved.get("provider", "azure").lower()
        endpoint = resolved.get("endpoint")
        key = resolved.get("api_key")
        deployment = resolved.get("deployment")
        api_version = resolved.get("api_version")
        temperature = resolved.get("temperature", 0.2)

        if AzureChatOpenAI is None:
            raise ImportError("langchain_openai is not installed.")

        if provider == "azure":
            return AzureChatOpenAI(
                azure_endpoint=endpoint,
                azure_deployment=deployment,
                openai_api_version=api_version,
                api_key=key,
                temperature=temperature,
            )
        else:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=deployment,
                api_key=key,
                base_url=endpoint,
                temperature=temperature,
            )

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def chat(self, message: str) -> Dict[str, Any]:
        """
        Process one user message. Returns:
          { answer, intent, confidence, triage_ready }
        """
        message = (message or "").strip()
        if not message:
            return {
                "answer": "Please enter a question.",
                "intent": "unknown",
                "confidence": "low",
                "triage_ready": False,
            }

        if not self._triage_is_ready():
            return {
                "answer": (
                    "Triage has not been run for this project yet. "
                    "Please execute Triage first so the assistant can access the source analysis data."
                ),
                "intent": "triage_gate",
                "confidence": "high",
                "triage_ready": False,
            }

        intent = _classify_intent(message)

        # Always load ALL context blocks — the LLM decides what to use
        objects_ctx = self._fetch_objects_context()
        impacts_ctx = self._fetch_table_impacts_context()
        columns_ctx = self._fetch_columns_context()
        understanding_ctx = self._fetch_understanding_context()

        system_prompt = (
            "You are an analyst assistant for a legacy data modernization project. "
            "Your job is to answer questions about the LEGACY SOURCE assets based strictly on the "
            "structured metadata provided below. "
            "Do NOT invent data. If evidence is missing, say so clearly. "
            "Use all the metadata sections you consider relevant for each question — you have full freedom "
            "to combine information from any section to give the best possible answer.\n\n"
            "SCOPE: Answer only questions about legacy source assets (inventory, tables, fields, PII, "
            "dependencies, complexity, readiness). You do NOT answer about modernized target output code.\n\n"
            "=== PROJECT SUMMARY ===\n"
            f"{understanding_ctx}\n\n"
            "=== ASSETS INVENTORY ===\n"
            "Each line: asset name | type (SSIS/SQL/etc) | layer | criticality | pii flag\n"
            f"{objects_ctx}\n\n"
            "=== TABLE IMPACTS ===\n"
            "Shows which database tables each asset reads from or writes to, and the operation (SELECT/INSERT/UPDATE/DELETE).\n"
            "Use this to answer questions about table usage, data flow, and dependencies.\n"
            f"{impacts_ctx}\n\n"
            "=== COLUMN PROFILES ===\n"
            "Each line: column name | data type | pii flag | pii category\n"
            "Use this to answer questions about fields, data types, PII attributes, or date/temporal columns.\n"
            f"{columns_ctx}\n\n"
            "=== END OF METADATA ===\n\n"
            f"Detected question intent: {intent}\n\n"
            "Answer clearly and concisely. End your answer with a confidence label: "
            "[Confidence: high | medium | low] based on how complete the evidence is."
        )

        try:
            llm = await self._get_llm()
            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=message),
            ])
            answer = response.content.strip() if hasattr(response, "content") else str(response)
            confidence = "medium"
            if "no registered information" in answer.lower() or "not found" in answer.lower():
                confidence = "low"
            elif "high confidence" in answer.lower():
                confidence = "high"

            result = {
                "answer": answer,
                "intent": intent,
                "confidence": confidence,
                "triage_ready": True,
            }

            # Persist exchange (non-blocking — errors are logged, not raised)
            try:
                thread_id = self._get_or_create_thread()
                self._persist_exchange(thread_id, message, result)
            except Exception as persist_exc:
                logger.error(f"[Assistant] History persist failed (non-critical): {persist_exc}", "ProjectAssistant")

            logger.info(
                f"[Assistant] project={self.project_id} intent={intent} answer_len={len(answer)}",
                "ProjectAssistant",
            )
            return result

        except Exception as exc:
            logger.error(f"[Assistant] LLM error: {exc}", "ProjectAssistant")
            return {
                "answer": (
                    "The assistant is temporarily unavailable. "
                    "Please check that the LLM provider is configured for this tenant."
                ),
                "intent": intent,
                "confidence": "low",
                "triage_ready": True,
            }
