from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional


PROMPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PROMPTS_DIR.parents[2]
CARTRIDGES_DIR = PROJECT_ROOT / "prompt_lab" / "cartridges"

TECH_STACK_MAP: Dict[str, str] = {
    "aws": "aws",
    "base": "generic",
    "dbt": "dbt",
    "gcp": "gcp",
    "ms_fabric": "ms_fabric",
    "ms_fabric_sql": "ms_fabric_sql",
    "pyspark": "pyspark",
    "sf": "salesforce",
    "snowflake": "snowflake",
    "snowflake_sql": "snowflake_sql",
}

PATTERN_TYPE_MAP: Dict[str, str] = {
    "bronze_layer.md": "bronze",
    "silver_layer.md": "silver",
    "gold_layer.md": "gold",
    "direct_layer.md": "direct",
}

KNOWN_PATTERN_TYPES = set(PATTERN_TYPE_MAP.values())

TECH_STACK_ALIASES: Dict[str, str] = {
    "databricks": "pyspark",
    "fabric": "ms_fabric",
    "fabric_sql": "ms_fabric_sql",
    "microsoft_fabric": "ms_fabric",
    "microsoft_fabric_sql": "ms_fabric_sql",
    "sf": "salesforce",
    "snowflake_snowpark": "snowflake",
}

AGENT_ID_MAP: Dict[str, Optional[str]] = {
    "agent_a_discovery": "agent-a",
    "agent_c_interpreter": "agent-c",
    "agent_d_auditor": "agent-d",
    "agent_f_critic": "agent-f",
    "agent_g_governance": "agent-g",
    "agent_s_scout": "agent-s",
}


@dataclass(frozen=True)
class PromptSpec:
    prompt_id: str
    source_path: Path
    category: str
    agent_id: Optional[str] = None
    tech_stack: Optional[str] = None
    pattern_type: Optional[str] = None

    @property
    def relative_source(self) -> str:
        return self.source_path.relative_to(PROJECT_ROOT).as_posix()

    def read_text(self) -> str:
        return self.source_path.read_text(encoding="utf-8")

    def to_db_record(self) -> Dict[str, object]:
        return {
            "prompt_id": self.prompt_id,
            "content": self.read_text(),
            "agent_id": self.agent_id,
            "tech_stack": self.tech_stack,
            "pattern_type": self.pattern_type,
            "is_active": True,
            "metadata": {
                "source": self.relative_source,
                "category": self.category,
            },
        }


def iter_agent_specs() -> Iterable[PromptSpec]:
    for path in sorted(PROMPTS_DIR.glob("agent_*.md")):
        prompt_id = path.stem
        yield PromptSpec(
            prompt_id=prompt_id,
            source_path=path,
            category="agent",
            agent_id=AGENT_ID_MAP.get(prompt_id),
        )


def iter_shared_specs() -> Iterable[PromptSpec]:
    shared_path = PROMPTS_DIR / "coding_standards.md"
    if shared_path.exists():
        yield PromptSpec(
            prompt_id="coding_standards",
            source_path=shared_path,
            category="shared",
        )


def iter_cartridge_specs() -> Iterable[PromptSpec]:
    if not CARTRIDGES_DIR.exists():
        return

    for tech_dir in sorted(p for p in CARTRIDGES_DIR.iterdir() if p.is_dir()):
        tech_stack = TECH_STACK_MAP.get(tech_dir.name, tech_dir.name)
        for path in sorted(tech_dir.glob("*.md")):
            if path.name == "README.md":
                continue

            pattern_type = PATTERN_TYPE_MAP.get(path.name)
            if not pattern_type:
                continue

            prompt_id = f"agent_c_{pattern_type}_{tech_stack}"
            yield PromptSpec(
                prompt_id=prompt_id,
                source_path=path,
                category="cartridge",
                agent_id="agent-c",
                tech_stack=tech_stack,
                pattern_type=pattern_type,
            )


def normalize_tech_stack(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    return TECH_STACK_ALIASES.get(normalized, normalized)


def build_cartridge_prompt_id(layer: Optional[str], tech_stack: Optional[str]) -> Optional[str]:
    normalized_layer = (layer or "").strip().lower()
    normalized_tech = normalize_tech_stack(tech_stack)

    if normalized_layer not in KNOWN_PATTERN_TYPES or not normalized_tech:
        return None

    return f"agent_c_{normalized_layer}_{normalized_tech}"


@lru_cache(maxsize=1)
def _cached_prompt_specs() -> tuple[PromptSpec, ...]:
    specs = list(iter_agent_specs())
    specs.extend(iter_shared_specs())
    specs.extend(iter_cartridge_specs())
    return tuple(sorted(specs, key=lambda spec: spec.prompt_id))


@lru_cache(maxsize=1)
def _prompt_spec_by_id() -> Dict[str, PromptSpec]:
    return {spec.prompt_id: spec for spec in _cached_prompt_specs()}


@lru_cache(maxsize=1)
def _legacy_alias_map() -> Dict[str, str]:
    aliases: Dict[str, str] = {}
    canonical_prompt_ids = set(_prompt_spec_by_id())

    for path in sorted(PROMPTS_DIR.glob("cartridge_*.md")):
        parts = path.stem.split("_")
        if len(parts) < 3:
            continue

        layer = parts[-1].lower()
        if layer not in KNOWN_PATTERN_TYPES:
            continue

        tech_stack = normalize_tech_stack("_".join(parts[1:-1]))
        canonical_prompt_id = build_cartridge_prompt_id(layer, tech_stack)

        if canonical_prompt_id and canonical_prompt_id in canonical_prompt_ids:
            aliases[path.stem] = canonical_prompt_id

    return aliases


def get_canonical_prompt_specs() -> List[PromptSpec]:
    return list(_cached_prompt_specs())


def resolve_prompt_id(prompt_id: str) -> str:
    return _legacy_alias_map().get(prompt_id, prompt_id)


def get_prompt_lookup_ids(prompt_id: str) -> List[str]:
    lookup_ids = [prompt_id]
    canonical_prompt_id = resolve_prompt_id(prompt_id)

    if canonical_prompt_id not in lookup_ids:
        lookup_ids.append(canonical_prompt_id)

    for legacy_prompt_id, mapped_prompt_id in _legacy_alias_map().items():
        if mapped_prompt_id == canonical_prompt_id and legacy_prompt_id not in lookup_ids:
            lookup_ids.append(legacy_prompt_id)

    return lookup_ids


def is_cartridge_prompt(prompt_id: str) -> bool:
    prompt_spec = get_prompt_spec(prompt_id)
    if prompt_spec:
        return prompt_spec.category == "cartridge"

    return resolve_prompt_id(prompt_id).startswith("agent_c_")


def get_prompt_spec(prompt_id: str) -> Optional[PromptSpec]:
    return _prompt_spec_by_id().get(resolve_prompt_id(prompt_id))
