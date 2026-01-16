"""Abstract base class for LLM services."""

import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from server.models.chat_models import Message, ToolCall, ChatResponse, UsageInfo
from server.services.tools.base import BaseToolService
from server.core.config import settings

logger = logging.getLogger(__name__)


class BaseLLMService(ABC):
    """Abstract base class for all LLM service implementations."""
    
    def __init__(self, tools: List[BaseToolService], system_prompt: str = None):
        """
        Initialize the LLM service with tools.
        
        Args:
            tools: List of tool services available to the LLM
            system_prompt: Custom system prompt (defaults to settings.system_prompt)
        """
        self.tools: Dict[str, BaseToolService] = {tool.name: tool for tool in tools}
        self.system_prompt = system_prompt or settings.system_prompt
        logger.info(f"Initialized LLM service with tools: {list(self.tools.keys())}")
    
    @abstractmethod
    async def _call_llm(self, messages: List[Message]) -> Any:
        """
        Make a call to the LLM provider.
        
        Args:
            messages: List of messages in the conversation
            
        Returns:
            Provider-specific response object
        """
        pass
    
    @abstractmethod
    def _extract_response(self, llm_response: Any) -> tuple[Message, UsageInfo]:
        """
        Extract message and usage from provider response.
        
        Args:
            llm_response: Provider-specific response object
            
        Returns:
            Tuple of (Message, UsageInfo)
        """
        pass
    
    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions for all registered tools.
        
        Returns:
            List of tool definitions in OpenAI format
        """
        return [tool.get_tool_definition() for tool in self.tools.values()]
    
    def _ensure_system_message(self, messages: List[Message]) -> List[Message]:
        """
        Ensure the conversation starts with a system message.
        
        Args:
            messages: Current message list
            
        Returns:
            Messages with system message prepended if not present
        """
        # Check if first message is already a system message
        if messages and messages[0].role == "system" and messages[0].content == self.system_prompt:
            return messages
        
        # Prepend system message
        system_message = Message(
            role="system",
            content=self.system_prompt
        )
        return [system_message] + messages
    
    def _execute_tools(self, tool_calls: List[ToolCall]) -> List[Message]:
        """
        Execute tool calls and return tool result messages.
        
        Args:
            tool_calls: List of tool calls to execute
            
        Returns:
            List of tool result messages
        """
        tool_messages = []
        
        for tool_call in tool_calls:
            logger.info(f"Executing tool: {tool_call.name} (id: {tool_call.id})")
            
            try:
                # Parse arguments
                arguments = json.loads(tool_call.arguments)
                
                # Get tool service
                if tool_call.name not in self.tools:
                    result = f"Error: Tool '{tool_call.name}' not found"
                    logger.error(result)
                else:
                    tool_service = self.tools[tool_call.name]
                    result = tool_service.execute(**arguments)
                    logger.info(f"Tool {tool_call.name} executed successfully")
                
            except json.JSONDecodeError as e:
                result = f"Error parsing tool arguments: {str(e)}"
                logger.error(result)
            except Exception as e:
                result = f"Error executing tool: {str(e)}"
                logger.error(result, exc_info=True)
            
            # Create tool result message
            tool_messages.append(Message(
                role="tool",
                content=result,
                tool_call_id=tool_call.id,
                name=tool_call.name
            ))
        
        return tool_messages
    
    async def execute(self, messages: List[Message], max_iterations: int = 5) -> ChatResponse:
        """
        Execute the full chat cycle with tool calling support.
        
        Args:
            messages: List of messages in the conversation
            max_iterations: Maximum number of LLM calls (to prevent infinite loops)
            
        Returns:
            ChatResponse with updated messages and usage info
        """
        # Ensure system message is present
        current_messages = self._ensure_system_message(messages)
        
        total_usage = UsageInfo()
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"LLM iteration {iteration}/{max_iterations}")
            
            # Call LLM
            llm_response = await self._call_llm(current_messages)
            assistant_message, usage = self._extract_response(llm_response)
            
            # Update usage
            total_usage.prompt_tokens += usage.prompt_tokens
            total_usage.completion_tokens += usage.completion_tokens
            total_usage.total_tokens += usage.total_tokens
            
            # Add assistant message to history
            current_messages.append(assistant_message)
            
            # Check if there are tool calls
            if not assistant_message.tool_calls:
                # No more tool calls, we're done
                logger.info("No tool calls found, conversation complete")
                break
            
            # Execute tool calls
            tool_messages = self._execute_tools(assistant_message.tool_calls)
            current_messages.extend(tool_messages)
            
            logger.info(f"Executed {len(tool_messages)} tool calls, continuing conversation")
        
        if iteration >= max_iterations:
            logger.warning(f"Reached maximum iterations ({max_iterations})")
        
        return ChatResponse(
            messages=current_messages,
            usage=total_usage
        )
