"""Dependency injection for FastAPI."""

import logging
from typing import List

from server.core.config import settings
from server.services.tools.base import BaseToolService
from server.services.tools.chromadb_tools import ChromaDBQATool, ChromaDBDocsTool
from server.services.llm.base import BaseLLMService
from server.services.llm.github_models import GithubModelsLLMService

logger = logging.getLogger(__name__)


def get_tools() -> List[BaseToolService]:
    """
    Get all available tool services.
    
    Returns:
        List of tool service instances
    """
    tools = [
        ChromaDBQATool(),
        # Uncomment when you have a docs collection:
        # ChromaDBDocsTool(),
    ]
    return tools


def get_llm_service() -> BaseLLMService:
    """
    Get the LLM service instance.
    
    Returns:
        Configured LLM service
    """
    tools = get_tools()
    
    # For now, we only have GitHub Models
    # In the future, you could add logic to choose provider based on settings
    llm_service = GithubModelsLLMService(tools=tools)
    
    return llm_service