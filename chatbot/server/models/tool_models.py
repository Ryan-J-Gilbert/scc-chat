"""Tool-related Pydantic models."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    """OpenAI-compatible tool definition."""
    
    type: str = Field(default="function", description="Tool type")
    function: Dict[str, Any] = Field(..., description="Function definition")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "type": "function",
                "function": {
                    "name": "search_qa",
                    "description": "Search Q&A pairs",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"}
                        },
                        "required": ["query"]
                    }
                }
            }
        }


class ToolResult(BaseModel):
    """Result from tool execution."""
    
    tool_call_id: str = Field(..., description="ID of the tool call")
    result: str = Field(..., description="String result from tool execution")
    success: bool = Field(default=True, description="Whether execution succeeded")
    error: Optional[str] = Field(None, description="Error message if failed")


class ToolExecutionContext(BaseModel):
    """Context for tool execution."""
    
    query: str = Field(..., description="Query string")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    n_results: int = Field(default=5, description="Number of results to return")