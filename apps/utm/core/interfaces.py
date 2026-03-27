from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from dataclasses import dataclass, field

# --- Data Structures (Shared) ---

class MetadataObject(BaseModel):
    source_name: str
    source_tech: str
    raw_content: str
    components: List[Dict[str, Any]]
    metadata: Dict[str, Any] = {}

class LogicalStep(BaseModel):
    step_id: Optional[str] = None
    step_type: str
    step_order: int
    ir_payload: Dict[str, Any]

# --- V5 Knowledge Model Structures ---

@dataclass
class EvidenceItem:
    source_path: str
    source_block_type: str
    snippet: str
    line_start: Optional[int]
    line_end: Optional[int]
    parser_name: str
    extraction_method: str  # 'parser_deterministic' | 'llm_inference' | 'heuristic' | 'human_override'
    confidence: float
    rationale: Optional[str] = None

@dataclass
class StepHint:
    name: str
    step_type: str
    order_hint: Optional[int]
    depends_on_steps: List[str] = field(default_factory=list)
    branching_hint: Optional[str] = None
    extraction_method: str = "parser_deterministic"
    confidence: float = 1.0

@dataclass
class ConstraintHint:
    constraint_type: str
    value_hint: str
    severity: str = "info"
    extraction_method: str = "parser_deterministic"
    confidence: float = 1.0

@dataclass
class ProcessHint:
    name: str
    process_type: str
    extraction_method: str
    confidence: float
    evidence_items: List[EvidenceItem] = field(default_factory=list)
    orchestration_steps: List[StepHint] = field(default_factory=list)
    operational_constraints: List[ConstraintHint] = field(default_factory=list)

# --- Interfaces ---

class BaseParser(ABC):
    """
    [Legacy v4] Interface for Ingestion Layer (Agent Parser).
    Responsibility: Read raw file and extract basic metadata components.
    """
    @abstractmethod
    def parse(self, file_path: str) -> MetadataObject:
        pass

class BaseCartridge(ABC):
    """
    [Legacy v4] Interface for Synthesis Layer (Agent Cartridge).
    Responsibility: Translate IR Steps into target code.
    """
    @abstractmethod
    def render(self, ir_steps: List[LogicalStep]) -> str:
        """
        Receives a list of Universal IR Steps and returns the final code block (e.g., PySpark script).
        """
        pass

class BaseAgent(ABC):
    """
    Interface for Autonomous Agents.
    """
    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pass

class CartridgeBase(ABC):
    """
    [V5 Knowledge Model] Interface for Discovery Cartridges.
    Responsibility: Parse a specific technology file and extract structured, tech-agnostic intelligence.
    """
    
    @abstractmethod
    def can_handle(self, ext: str, content_hint: str = None) -> bool:
        """Declares if this cartridge can parse this type of file."""
        pass
    
    @abstractmethod
    def parse(self, file_path: str, content: bytes) -> List[EvidenceItem]:
        """Extracts deterministic evidence items from the file."""
        pass
    
    def extract_processes(self, file_path: str, content: bytes) -> List[ProcessHint]:
        """Optional: extracts process constraints. Default is empty (LLM will infer if missing)."""
        return []
