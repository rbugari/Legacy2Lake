# AI Agent Service Pattern

**Category:** Backend - AI Services  
**Use Case:** Creating LLM-powered agent services

## Pattern Template

```python
"""
Agent {X} Service
==================

Purpose:
    {Description of agent's responsibility}

Key Methods:
    - {main_method}(): {What it does}
    - _get_llm(): Resolves LLM client from database configuration
    - _load_prompt(): Loads system prompt from database

Integration:
    - Used by: {Which routers or services use this}
    - Depends on: SupabasePersistence, LangChain

Author: Legacy2Lake Engineering
Date: {Current Date}
Version: v1.0
"""

import json
from typing import Dict, Any, List, Optional
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence
    from apps.api.services.knowledge_service import KnowledgeService
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence
        from services.knowledge_service import KnowledgeService
    except ImportError:
        from ..utils.logger import logger
        from .persistence_service import SupabasePersistence
        from .knowledge_service import KnowledgeService


class Agent{X}Service:
    """
    Agent {X}: {Purpose}
    
    Capabilities:
        - {Capability 1}
        - {Capability 2}
        - {Capability 3}
    """
    
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        """
        Initialize Agent {X} service.
        
        Args:
            tenant_id: Tenant ID for multi-tenant isolation
            client_id: Client ID (deprecated, use tenant_id)
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.db = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)
        self.knowledge = KnowledgeService(tenant_id=tenant_id, client_id=client_id)
        
        logger.info(
            f"[Agent{X}] Initialized: tenant_id={tenant_id}",
            "Agent{X}"
        )
    
    async def _get_llm(self, project_id: Optional[str] = None):
        """
        Resolves LLM client strictly from Agent Matrix (database).
        
        Args:
            project_id: Optional project ID for project-specific config
        
        Returns:
            LangChain LLM client (AzureChatOpenAI or ChatOpenAI)
        
        Raises:
            Exception: If no LLM configuration found
        """
        logger.info(f"[Agent{X}] Resolving LLM configuration", "Agent{X}")
        
        try:
            # Resolve agent model from database
            config = await self.db.resolve_agent_model(
                agent_id="agent-{x}",
                project_id=project_id
            )
            
            if not config:
                raise Exception("No LLM configuration found for agent-{x}")
            
            provider = config.get("provider", "azure")
            
            # Azure OpenAI
            if provider == "azure":
                return AzureChatOpenAI(
                    deployment_name=config["deployment_name"],
                    api_key=config["api_key"],
                    azure_endpoint=config["endpoint"],
                    api_version=config.get("api_version", "2024-05-01-preview"),
                    temperature=config.get("temperature", 0.7),
                    max_tokens=config.get("max_tokens", 4096)
                )
            
            # OpenAI or Groq
            else:
                return ChatOpenAI(
                    model=config["model"],
                    api_key=config["api_key"],
                    base_url=config.get("base_url"),  # For Groq
                    temperature=config.get("temperature", 0.7),
                    max_tokens=config.get("max_tokens", 4096)
                )
        
        except Exception as e:
            logger.error(f"[Agent{X}] Failed to resolve LLM: {e}", "Agent{X}")
            raise
    
    async def _load_prompt(self, prompt_id: str = "agent_{x}_base", **kwargs) -> str:
        """
        Load system prompt from database (global or tenant-specific).
        
        Args:
            prompt_id: Prompt identifier (e.g., "agent_c_pyspark_bronze")
            **kwargs: Additional variables for prompt templating
        
        Returns:
            Formatted prompt content
        """
        logger.info(f"[Agent{X}] Loading prompt: {prompt_id}", "Agent{X}")
        
        try:
            # Get prompt from database
            prompt = await self.db.get_prompt(
                prompt_id=prompt_id,
                tenant_id=self.tenant_id
            )
            
            if not prompt:
                raise Exception(f"Prompt not found: {prompt_id}")
            
            # Apply templating if variables provided
            if kwargs:
                for key, value in kwargs.items():
                    prompt = prompt.replace(f"{{{key}}}", str(value))
            
            return prompt
        
        except Exception as e:
            logger.error(f"[Agent{X}] Failed to load prompt: {e}", "Agent{X}")
            raise
    
    async def save_prompt(self, prompt_id: str, content: str):
        """
        Save or update prompt in database (requires admin role).
        
        Args:
            prompt_id: Prompt identifier
            content: Prompt content
        """
        logger.info(f"[Agent{X}] Saving prompt: {prompt_id}", "Agent{X}")
        
        try:
            await self.db.save_prompt(
                prompt_id=prompt_id,
                content=content,
                agent_id="agent-{x}",
                tenant_id=self.tenant_id
            )
            
            logger.info(f"[Agent{X}] ✅ Prompt saved: {prompt_id}", "Agent{X}")
        
        except Exception as e:
            logger.error(f"[Agent{X}] Failed to save prompt: {e}", "Agent{X}")
            raise
    
    @logger.llm_debug("Agent-{X}")
    async def {main_method}(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main processing method for Agent {X}.
        
        Args:
            input_data: Input data to process
            context: Optional context information
        
        Returns:
            Processing results
        """
        logger.info(
            f"[Agent{X}] Starting {main_method}: data_keys={list(input_data.keys())}",
            "Agent{X}"
        )
        
        try:
            # Step 1: Get LLM client
            llm = await self._get_llm()
            
            # Step 2: Load system prompt
            system_prompt = await self._load_prompt(
                prompt_id="agent_{x}_base",
                tech_stack=input_data.get("tech_stack", "generic")
            )
            
            # Step 3: Enrich with knowledge (if applicable)
            enriched_prompt = await self.knowledge.enrich_prompt(
                base_prompt=system_prompt,
                tech_id=input_data.get("tech_stack"),
                context=context or {}
            )
            
            # Step 4: Build user message
            user_message = self._build_user_message(input_data)
            
            # Step 5: Call LLM
            messages = [
                SystemMessage(content=enriched_prompt),
                HumanMessage(content=user_message)
            ]
            
            logger.info(f"[Agent{X}] Calling LLM...", "Agent{X}")
            response = await llm.ainvoke(messages)
            
            # Step 6: Parse response
            result = self._parse_response(response.content)
            
            logger.info(
                f"[Agent{X}] ✅ Processing complete",
                "Agent{X}"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"[Agent{X}] Processing failed: {e}", "Agent{X}")
            raise
    
    def _build_user_message(self, input_data: Dict[str, Any]) -> str:
        """
        Build user message from input data.
        
        Args:
            input_data: Input data
        
        Returns:
            Formatted user message
        """
        # Customize based on agent's needs
        message_parts = []
        
        if "source_code" in input_data:
            message_parts.append(f"Source Code:\n```\n{input_data['source_code']}\n```")
        
        if "requirements" in input_data:
            message_parts.append(f"\nRequirements: {input_data['requirements']}")
        
        if "constraints" in input_data:
            message_parts.append(f"\nConstraints: {input_data['constraints']}")
        
        return "\n\n".join(message_parts)
    
    def _parse_response(self, response_content: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured data.
        
        Args:
            response_content: Raw LLM response
        
        Returns:
            Structured response data
        """
        try:
            # Try to parse as JSON
            if response_content.strip().startswith("{"):
                return json.loads(response_content)
            
            # Extract JSON from markdown code blocks
            if "```json" in response_content:
                json_start = response_content.find("```json") + 7
                json_end = response_content.find("```", json_start)
                json_str = response_content[json_start:json_end].strip()
                return json.loads(json_str)
            
            # Return raw content if not JSON
            return {"content": response_content}
        
        except Exception as e:
            logger.warning(f"[Agent{X}] Failed to parse response as JSON: {e}", "Agent{X}")
            return {"content": response_content}
```

## Usage Example

```python
# Initialize agent
agent = Agent{X}Service(tenant_id="550e8400-e29b-41d4-a716-446655440000")

# Process data
result = await agent.{main_method}(
    input_data={
        "source_code": "SELECT * FROM customers",
        "tech_stack": "pyspark",
        "requirements": "Convert to medallion architecture"
    },
    context={
        "project_id": "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4",
        "target_layer": "bronze"
    }
)

print(result)
```

## Key Features

- ✅ Multi-tenancy support via tenant_id
- ✅ Dynamic LLM client resolution from database
- ✅ Dynamic prompt loading from database
- ✅ Knowledge enrichment integration
- ✅ Structured logging with LLM debug decorator
- ✅ Error handling with context
- ✅ Flexible response parsing (JSON or raw text)
- ✅ Import resolution for multiple contexts

## Testing

```python
import pytest
from unittest.mock import AsyncMock, Mock

@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.ainvoke = AsyncMock(return_value=Mock(content='{"result": "success"}'))
    return llm

@pytest.fixture
def agent_{x}_service(mock_supabase, mock_llm):
    service = Agent{X}Service(tenant_id="test-tenant")
    service._get_llm = AsyncMock(return_value=mock_llm)
    return service

@pytest.mark.asyncio
async def test_{main_method}(agent_{x}_service):
    result = await agent_{x}_service.{main_method}(
        input_data={"source_code": "test code"}
    )
    
    assert result is not None
    assert "result" in result or "content" in result
```

## Integration with Routers

```python
from fastapi import APIRouter, Depends
from apps.api.routers.dependencies import get_db
from apps.api.services.agent_{x}_service import Agent{X}Service

router = APIRouter()

@router.post("/process")
async def process_with_agent_{x}(
    payload: ProcessRequest,
    db: SupabasePersistence = Depends(get_db)
):
    agent = Agent{X}Service(tenant_id=db.tenant_id)
    result = await agent.{main_method}(
        input_data=payload.dict()
    )
    return result
```

## Customization Guide

1. **Replace placeholders:**
   - `{X}` → A, C, F, G, S, D (agent letter)
   - `{x}` → a, c, f, g, s, d (lowercase)
   - `{main_method}` → Primary method name (e.g., `transpile_task`, `critique_code`)
   - `{Purpose}` → Agent's responsibility

2. **Add agent-specific logic:**
   - Custom validation in `_build_user_message()`
   - Specialized parsing in `_parse_response()`
   - Additional helper methods as needed

3. **Extend with advanced features:**
   - Multi-turn conversations
   - Streaming responses
   - Retry logic with exponential backoff
   - Caching for repeated calls
