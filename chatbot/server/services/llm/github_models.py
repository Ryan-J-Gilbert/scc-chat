"""GitHub Models LLM service implementation using OpenAI library."""

import logging
from typing import List, Any

from openai import AsyncOpenAI

from server.core.config import settings
from server.models.chat_models import Message, ToolCall, UsageInfo
from server.services.tools.base import BaseToolService
from .base import BaseLLMService

logger = logging.getLogger(__name__)


class GithubModelsLLMService(BaseLLMService):
    """LLM service using GitHub Models via OpenAI library."""
    
    def __init__(
        self,
        tools: List[BaseToolService],
        api_key: str = None,
        model: str = None,
        max_tokens: int = None,
        temperature: float = None,
        system_prompt: str = None,
    ):
        """
        Initialize GitHub Models LLM service.
        
        Args:
            tools: List of available tool services
            api_key: GitHub API token (defaults to settings)
            model: Model name (defaults to settings)
            max_tokens: Maximum tokens (defaults to settings)
            temperature: Temperature setting (defaults to settings)
            system_prompt: Custom system prompt (defaults to settings)
        """
        super().__init__(tools, system_prompt=system_prompt)
        
        self.api_key = api_key or settings.github_api_key
        self.model = model or settings.default_model
        self.max_tokens = max_tokens or settings.max_tokens
        self.temperature = temperature or settings.temperature
        
        # Initialize OpenAI client pointing to GitHub Models
        self.client = AsyncOpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=self.api_key
        )
        
        logger.info(f"Initialized GithubModelsLLMService with model: {self.model}")
    
    def _messages_to_openai_format(self, messages: List[Message]) -> List[dict]:
        """
        Convert our Message objects to OpenAI API format.
        
        Args:
            messages: List of Message objects
            
        Returns:
            List of dictionaries in OpenAI format
        """
        openai_messages = []
        
        for msg in messages:
            message_dict = {"role": msg.role}
            
            if msg.content is not None:
                message_dict["content"] = msg.content
            
            if msg.tool_calls:
                message_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": tc.arguments
                        }
                    }
                    for tc in msg.tool_calls
                ]
            
            if msg.tool_call_id:
                message_dict["tool_call_id"] = msg.tool_call_id
            
            if msg.name:
                message_dict["name"] = msg.name
            
            openai_messages.append(message_dict)
        
        return openai_messages
    
    async def _call_llm(self, messages: List[Message]) -> Any:
        """
        Make a call to GitHub Models API.
        
        Args:
            messages: List of messages in the conversation
            
        Returns:
            OpenAI ChatCompletion response object
        """
        openai_messages = self._messages_to_openai_format(messages)
        tool_definitions = self._get_tool_definitions()
        
        logger.debug(f"Calling GitHub Models API with {len(openai_messages)} messages")
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            tools=tool_definitions if tool_definitions else None,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        
        return response
    
    def _extract_response(self, llm_response: Any) -> tuple[Message, UsageInfo]:
        """
        Extract message and usage from OpenAI response.
        
        Args:
            llm_response: OpenAI ChatCompletion response
            
        Returns:
            Tuple of (Message, UsageInfo)
        """
        choice = llm_response.choices[0]
        message = choice.message
        
        # Extract tool calls if present
        tool_calls = None
        if message.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=tc.function.arguments
                )
                for tc in message.tool_calls
            ]
        
        # Create our Message object
        assistant_message = Message(
            role="assistant",
            content=message.content,
            tool_calls=tool_calls
        )
        
        # Extract usage info
        usage = UsageInfo(
            prompt_tokens=llm_response.usage.prompt_tokens,
            completion_tokens=llm_response.usage.completion_tokens,
            total_tokens=llm_response.usage.total_tokens
        )
        
        return assistant_message, usage
