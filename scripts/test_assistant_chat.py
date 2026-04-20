"""
Test manual del ProjectAssistantService - v4.5 Sprint 1
Envía 10 preguntas representativas y muestra respuesta + intent + confidence.

Uso: python scripts/test_assistant_chat.py
"""
import asyncio
import sys
import os
import textwrap

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.api.services.project_assistant_service import ProjectAssistantService

# ── Configuración ────────────────────────────────────────────────────────────
PROJECT_ID = "1051e4b0-570d-443a-9412-0430a6ac3040"   # demo1  (triage completo)
TENANT_ID  = "daac0ee6-3b28-412d-8acd-43ec51149188"

QUESTIONS = [
    # Inventario general
    "¿Cuántos assets tiene este proyecto y de qué tipo son?",
    # Tablas
    "¿Qué tablas se leen en este proyecto?",
    "¿Cuáles tablas reciben escrituras?",
    # Campos / columnas
    "¿Qué columnas existen en los assets del proyecto?",
    "¿Hay algún campo de fecha o timestamp?",
    # PII
    "¿Existen campos con datos personales o PII?",
    "¿Cuáles son los campos sensibles que habría que enmascarar?",
    # Dependencias
    "¿Qué dependencias hay entre los assets?",
    # Riesgo / readiness
    "¿Hay assets críticos o con alto riesgo para la migración?",
    # Pregunta abierta / general
    "Dame un resumen ejecutivo del estado actual del proyecto desde el punto de vista técnico.",
]

SEPARATOR = "─" * 72


async def main() -> None:
    svc = ProjectAssistantService(tenant_id=TENANT_ID, project_id=PROJECT_ID)

    print(f"\n{'═' * 72}")
    print(f"  PROJECT ASSISTANT TEST  —  project_id: {PROJECT_ID}")
    print(f"{'═' * 72}\n")

    for i, question in enumerate(QUESTIONS, 1):
        print(f"[Q{i:02d}] {question}")
        result = await svc.chat(question)

        triage_ok = result.get("triage_ready", False)
        intent    = result.get("intent", "—")
        conf      = result.get("confidence", "—")
        answer    = result.get("answer", "")

        if not triage_ok:
            print(f"  ⛔  GATE: {answer}\n{SEPARATOR}\n")
            continue

        wrapped = textwrap.fill(answer, width=68, initial_indent="  ", subsequent_indent="  ")
        print(f"  intent={intent}  confidence={conf}")
        print(wrapped)
        print(f"{SEPARATOR}\n")


if __name__ == "__main__":
    asyncio.run(main())
