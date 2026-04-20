"""
Tech Stack Contracts: Single source of truth for destination technology capabilities.

Maps canonical tech stacks to their cartridge, SQL flavor, and supported patterns.
This module ensures consistency across:
- CartridgeFactory (cartridge selection)
- PromptService (prompt ID resolution)
- Agent C/F (code generation and review)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from enum import Enum


class SQLFlavor(str, Enum):
    """Enumeration of SQL dialects we generate and support."""
    SNOWFLAKE_SQL = "snowflake_sql"
    MS_FABRIC_SQL = "ms_fabric_sql"
    ANSI_SQL = "ansi_sql"
    PYSPARK = "pyspark"  # Not SQL, but included for completeness


@dataclass(frozen=True)
class TechStackContract:
    """
    Contract for a target tech stack.
    
    Attributes:
        canonical_tech: Single normalized form (e.g., 'snowflake_sql')
        aliases: List of accepted input variants
        cartridge_class: Name of the cartridge class to use
        sql_flavor: SQL dialect or language flavor generated
        supported_layers: Set of execution layers (direct, bronze, silver, gold, etc.)
        requires_sql_only: If True, code MUST be SQL, not alternative languages
    """
    canonical_tech: str
    aliases: List[str]
    cartridge_class: str
    sql_flavor: SQLFlavor
    supported_layers: Set[str]
    requires_sql_only: bool = False


# Registry of all supported tech stacks
TECH_STACK_REGISTRY: Dict[str, TechStackContract] = {
    "snowflake_sql": TechStackContract(
        canonical_tech="snowflake_sql",
        aliases=["snowflake_sql", "snowflake_native_sql", "snowflake_sql_native", "snowflake_sql_direct"],
        cartridge_class="SnowflakeCartridge",
        sql_flavor=SQLFlavor.SNOWFLAKE_SQL,
        supported_layers={"direct", "bronze", "silver", "gold"},
        requires_sql_only=True,
    ),
    "snowflake": TechStackContract(
        canonical_tech="snowflake",
        aliases=["snowflake", "snowflake_snowpark"],
        cartridge_class="SnowflakeCartridge",
        sql_flavor=SQLFlavor.PYSPARK,  # Primary is Snowpark Python
        supported_layers={"direct", "bronze", "silver", "gold"},
        requires_sql_only=False,
    ),
    "ms_fabric_sql": TechStackContract(
        canonical_tech="ms_fabric_sql",
        aliases=["ms_fabric_sql", "fabric_sql", "ms_fabric_warehouse"],
        cartridge_class="MSFabricCartridge",
        sql_flavor=SQLFlavor.MS_FABRIC_SQL,
        supported_layers={"direct", "bronze", "silver", "gold"},
        requires_sql_only=True,
    ),
    "ms_fabric": TechStackContract(
        canonical_tech="ms_fabric",
        aliases=["ms_fabric", "fabric", "microsoft_fabric"],
        cartridge_class="MSFabricCartridge",
        sql_flavor=SQLFlavor.PYSPARK,  # Primary is PySpark Notebook
        supported_layers={"direct", "bronze", "silver", "gold"},
        requires_sql_only=False,
    ),
    "pyspark": TechStackContract(
        canonical_tech="pyspark",
        aliases=["pyspark", "databricks", "databricks_pyspark"],
        cartridge_class="PySparkCartridge",
        sql_flavor=SQLFlavor.PYSPARK,
        supported_layers={"direct", "bronze", "silver", "gold"},
        requires_sql_only=False,
    ),
    "dbt": TechStackContract(
        canonical_tech="dbt",
        aliases=["dbt"],
        cartridge_class="DbtCartridge",
        sql_flavor=SQLFlavor.ANSI_SQL,
        supported_layers={"direct", "bronze", "silver", "gold"},
        requires_sql_only=True,
    ),
    "gcp": TechStackContract(
        canonical_tech="gcp",
        aliases=["gcp", "google", "bigquery"],
        cartridge_class="GCPCartridge",
        sql_flavor=SQLFlavor.ANSI_SQL,
        supported_layers={"direct", "bronze", "silver", "gold"},
        requires_sql_only=False,
    ),
    "aws": TechStackContract(
        canonical_tech="aws",
        aliases=["aws", "amazon", "redshift"],
        cartridge_class="AWSCartridge",
        sql_flavor=SQLFlavor.ANSI_SQL,
        supported_layers={"direct", "bronze", "silver", "gold"},
        requires_sql_only=False,
    ),
}


def resolve_contract(tech_input: Optional[str]) -> Optional[TechStackContract]:
    """
    Resolve a tech input string to its contract.
    
    Args:
        tech_input: Raw tech string from user input, registry, or config
        
    Returns:
        TechStackContract if found, None otherwise
    """
    if not tech_input:
        return None
    
    normalized = str(tech_input).lower().replace("-", "_").replace(" ", "_")
    
    # Direct lookup by canonical tech
    if normalized in TECH_STACK_REGISTRY:
        return TECH_STACK_REGISTRY[normalized]
    
    # Lookup by alias
    for contract in TECH_STACK_REGISTRY.values():
        if normalized in contract.aliases:
            return TECH_STACK_REGISTRY[contract.canonical_tech]
    
    return None


def get_canonical_tech(tech_input: Optional[str]) -> Optional[str]:
    """Get canonical tech name for a given input."""
    contract = resolve_contract(tech_input)
    return contract.canonical_tech if contract else None


def get_cartridge_class(tech_input: Optional[str]) -> Optional[str]:
    """Get cartridge class name for a given tech input."""
    contract = resolve_contract(tech_input)
    return contract.cartridge_class if contract else None


def get_sql_flavor(tech_input: Optional[str]) -> Optional[SQLFlavor]:
    """Get SQL flavor for a given tech input."""
    contract = resolve_contract(tech_input)
    return contract.sql_flavor if contract else None


def validate_sql_flavor_coverage(
    tech_input: Optional[str],
    generated_code: str,
    layer: str = "direct",
) -> Dict[str, any]:
    """
    Validate that generated code matches the expected SQL flavor for the tech stack.
    
    Args:
        tech_input: Target technology string
        generated_code: Generated code artifact
        layer: Execution layer (direct, bronze, silver, gold)
        
    Returns:
        Dict with 'valid': bool, 'flavor_expected': str, 'issues': List[str]
    """
    contract = resolve_contract(tech_input)
    if not contract:
        return {
            "valid": False,
            "flavor_expected": None,
            "issues": [f"Unknown tech stack: {tech_input}"],
        }
    
    if layer not in contract.supported_layers:
        return {
            "valid": False,
            "flavor_expected": contract.sql_flavor.value,
            "issues": [f"Layer '{layer}' not supported for {contract.canonical_tech}"],
        }
    
    code = (generated_code or "").strip()
    issues = []
    
    # Snowflake SQL: Must have COPY INTO, MERGE, or CREATE/INSERT
    if contract.sql_flavor == SQLFlavor.SNOWFLAKE_SQL:
        if not any(keyword in code.upper() for keyword in ["COPY INTO", "MERGE", "CREATE", "INSERT"]):
            issues.append(
                f"Snowflake SQL expected but code lacks COPY INTO, MERGE, or CREATE/INSERT keywords"
            )
        if "spark.read" in code.lower() or "spark.write" in code.lower():
            issues.append(
                f"Generated code contains PySpark calls (spark.read/write) but Snowflake SQL was expected"
            )
    
    # MS Fabric SQL: Must have T-SQL keywords
    elif contract.sql_flavor == SQLFlavor.MS_FABRIC_SQL:
        if not any(keyword in code.upper() for keyword in ["CREATE", "INSERT", "DELETE", "MERGE"]):
            issues.append(
                f"MS Fabric SQL expected but code lacks CREATE/INSERT/DELETE/MERGE keywords"
            )
    
    # PySpark: Must have spark.read or spark.write
    elif contract.sql_flavor == SQLFlavor.PYSPARK:
        if "spark.read" not in code.lower() and "spark.write" not in code.lower():
            issues.append(
                f"PySpark expected but code lacks spark.read/write"
            )
    
    return {
        "valid": len(issues) == 0,
        "flavor_expected": contract.sql_flavor.value,
        "issues": issues,
    }
