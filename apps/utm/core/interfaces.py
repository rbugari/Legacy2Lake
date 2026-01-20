from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

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

# --- Interfaces ---

class BaseParser(ABC):
    """
    Interface for Ingestion Layer (Agent Parser).
    Responsibility: Read raw file and extract basic metadata components.
    """
    @abstractmethod
    def parse(self, file_path: str) -> MetadataObject:
        pass

class BaseCartridge(ABC):
    """
    Interface for Synthesis Layer (Agent Cartridge).
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
