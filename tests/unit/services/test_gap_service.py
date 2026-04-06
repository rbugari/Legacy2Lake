"""
Unit tests for the gap workspace service.

Validates CRUD behavior, decision notes, and signal import deduplication.
"""

import asyncio
from unittest.mock import patch

from apps.api.services.gap_service import GapCreate, GapResolve, GapService


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeTableQuery:
    def __init__(self, store, table_name):
        self.store = store
        self.table_name = table_name
        self.operation = "select"
        self.filters = []
        self.payload = None

    def select(self, _columns):
        self.operation = "select"
        return self

    def insert(self, payload):
        self.operation = "insert"
        self.payload = payload
        return self

    def update(self, payload):
        self.operation = "update"
        self.payload = payload
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def order(self, *_args, **_kwargs):
        return self

    def execute(self):
        rows = self.store.setdefault(self.table_name, [])

        def matches(row):
            return all(row.get(field) == value for field, value in self.filters)

        if self.operation == "select":
            return FakeResponse([row.copy() for row in rows if matches(row)])

        if self.operation == "insert":
            row = dict(self.payload)
            row.setdefault("gap_id", f"gap-{len(rows) + 1}")
            row.setdefault("created_at", "2026-04-01T00:00:00Z")
            row.setdefault("updated_at", "2026-04-01T00:00:00Z")
            rows.append(row)
            return FakeResponse([row.copy()])

        if self.operation == "update":
            updated = []
            for row in rows:
                if matches(row):
                    row.update(self.payload)
                    row["updated_at"] = "2026-04-01T00:00:00Z"
                    updated.append(row.copy())
            return FakeResponse(updated)

        return FakeResponse([])


class FakeClient:
    def __init__(self, store):
        self.store = store

    def table(self, table_name):
        return FakeTableQuery(self.store, table_name)


class FakeDb:
    def __init__(self, store):
        self.store = store
        self.client = FakeClient(store)

    async def get_project_metadata(self, project_id):
        return self.store.get("project_metadata", {}).get(project_id)

    async def get_project_assets(self, project_id):
        return self.store.get("project_assets", {}).get(project_id, [])


def build_service(store, *, tenant_id="tenant-1", client_id="client-1", user_id="user-1"):
    service = GapService(tenant_id=tenant_id, client_id=client_id, user_id=user_id)
    service.db = FakeDb(store)
    return service


def test_create_gap_sets_scope_and_persists_payload():
    store = {"utm_project_gaps": []}
    service = build_service(store)

    created = asyncio.run(
        service.create_gap(
            "project-1",
            GapCreate(
                category="schema",
                severity="high",
                title="Map customer keys",
                decision_note="Track owner in backlog",
            ),
        )
    )

    assert created["severity"] == "HIGH"
    assert created["resolution_status"] == "OPEN"
    assert created["tenant_id"] == "tenant-1"
    assert created["created_by"] == "user-1"
    assert store["utm_project_gaps"][0]["title"] == "Map customer keys"


def test_resolve_and_reopen_gap_updates_decision_state():
    store = {
        "utm_project_gaps": [
            {
                "gap_id": "gap-1",
                "tenant_id": "tenant-1",
                "project_id": "project-1",
                "title": "Resolve access issue",
                "resolution_status": "OPEN",
            }
        ]
    }
    service = build_service(store)

    resolved = asyncio.run(service.resolve_gap("gap-1", GapResolve(decision_note="Awaiting approval")))
    reopened = asyncio.run(service.reopen_gap("gap-1"))

    assert resolved["resolution_status"] == "RESOLVED"
    assert resolved["decision_note"] == "Awaiting approval"
    assert resolved["resolved_by"] == "user-1"
    assert reopened["resolution_status"] == "OPEN"
    assert reopened["resolved_at"] is None
    assert reopened["resolved_by"] is None


def test_import_from_signals_deduplicates_existing_titles_and_counts_imports():
    store = {
        "project_metadata": {
            "project-1": {
                "quick_assessment": {
                    "blockers": ["No source access", "Missing target mapping"],
                },
            }
        },
        "project_assets": {
            "project-1": [
                {
                    "object_id": "asset-1",
                    "object_name": "CustomerLoad",
                    "is_pii": True,
                    "metadata": {"complexity_level": "HIGH", "mismatch_count": 2},
                    "validation_result": {"violations": ["rule-1", "rule-2", "rule-3"]},
                }
            ]
        },
        "utm_project_gaps": [
            {
                "gap_id": "gap-existing",
                "tenant_id": "tenant-1",
                "project_id": "project-1",
                "title": "No source access",
                "resolution_status": "OPEN",
            }
        ],
    }
    service = build_service(store)

    result = asyncio.run(service.import_from_signals("project-1"))

    assert result == {"imported": 5, "skipped": 1, "total": 6}
    titles = {row["title"] for row in store["utm_project_gaps"]}
    assert "No source access" in titles
    assert "Missing target mapping" in titles
    assert any(title.startswith("PII data detected") for title in titles)


def test_import_from_signals_preserves_signal_metadata_and_is_case_insensitive():
    store = {
        "project_metadata": {
            "project-1": {
                "quick_assessment": {},
            }
        },
        "project_assets": {
            "project-1": [],
        },
        "utm_project_gaps": [
            {
                "gap_id": "gap-existing",
                "tenant_id": "tenant-1",
                "project_id": "project-1",
                "title": "Missing target mapping",
                "resolution_status": "OPEN",
            }
        ],
    }
    service = build_service(store)

    grouped = {
        "schema": [
            {
                "category": "schema",
                "severity": "HIGH",
                "title": "missing target mapping",
                "description": "Case-insensitive duplicate should be skipped",
                "why_it_matters": "Target fields are incomplete.",
                "source_stage": "triage",
                "asset_id": "asset-9",
            },
            {
                "category": "schema",
                "severity": "MEDIUM",
                "title": "Add target surrogate key",
                "description": "Preserve signal metadata on import",
                "why_it_matters": "Target tables need a stable key.",
                "source_stage": "refinement",
                "asset_id": "asset-10",
            },
        ]
    }

    with patch("apps.api.services.gap_service.build_gaps_summary", return_value={"grouped": grouped}):
        result = asyncio.run(service.import_from_signals("project-1"))

    assert result == {"imported": 1, "skipped": 1, "total": 2}
    imported_gap = next(row for row in store["utm_project_gaps"] if row["title"] == "Add target surrogate key")
    assert imported_gap["severity"] == "MEDIUM"
    assert imported_gap["source_stage"] == "refinement"
    assert imported_gap["asset_id"] == "asset-10"
    assert imported_gap["category"] == "schema"


def test_import_from_signals_handles_empty_summary_without_creating_gaps():
    store = {
        "project_metadata": {
            "project-1": {
                "quick_assessment": {},
            }
        },
        "project_assets": {
            "project-1": [],
        },
        "utm_project_gaps": [],
    }
    service = build_service(store)

    result = asyncio.run(service.import_from_signals("project-1"))

    assert result == {"imported": 0, "skipped": 0, "total": 0}
    assert store["utm_project_gaps"] == []
