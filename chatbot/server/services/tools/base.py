"""Abstract base class for tool services."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseToolService(ABC):
    """Abstract base class for all tool services."""
    
    @abstractmethod
    def execute(self, query: str, **kwargs) -> str:
        """
        Execute the tool with the given query.
        
        Args:
            query: The query string
            **kwargs: Additional tool-specific parameters
            
        Returns:
            String result from tool execution
        """
        pass
    
    @abstractmethod
    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Return OpenAI-compatible tool definition.
        
        Returns:
            Dictionary containing tool schema
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Tool name identifier.
        
        Returns:
            Unique name for this tool
        """
        pass