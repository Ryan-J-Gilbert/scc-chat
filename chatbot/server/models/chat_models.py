"""Chat-related Pydantic models."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """Represents a tool call from the LLM."""
    
    id: str = Field(..., description="Unique identifier for this tool call")
    name: str = Field(..., description="Name of the tool to call")
    arguments: str = Field(..., description="JSON string of arguments")


class Message(BaseModel):
    """Represents a single message in the conversation."""
    
    role: str = Field(..., description="Role: 'user', 'assistant', or 'tool'")
    content: Optional[str] = Field(None, description="Message content")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="Tool calls made by assistant")
    tool_call_id: Optional[str] = Field(None, description="ID of tool call this message responds to")
    name: Optional[str] = Field(None, description="Name of the tool (for tool role messages)")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "What are the Q&A pairs about Python?"
            }
        }


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    
    messages: List[Message] = Field(..., description="Conversation history")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ]
            }
        }


class UsageInfo(BaseModel):
    """Token usage information."""
    
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    
    messages: List[Message] = Field(..., description="Updated conversation history")
    usage: Optional[UsageInfo] = Field(None, description="Token usage statistics")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "messages": [
                    {"role": "user", "content": "Hello!"},
                    {"role": "assistant", "content": "Hi! How can I help you?"}
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 8,
                    "total_tokens": 18
                }
            }
        }