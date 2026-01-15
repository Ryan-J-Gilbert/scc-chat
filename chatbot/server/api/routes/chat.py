"""Chat endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException

from server.models.chat_models import ChatRequest, ChatResponse
from server.services.llm.base import BaseLLMService
from server.api.dependencies import get_llm_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    llm_service: BaseLLMService = Depends(get_llm_service)
) -> ChatResponse:
    """
    Main chat endpoint that processes messages and returns responses.
    
    Args:
        request: Chat request with message history
        llm_service: Injected LLM service
        
    Returns:
        Chat response with updated message history
        
    Raises:
        HTTPException: If chat processing fails
    """
    try:
        logger.info(f"Processing chat request with {len(request.messages)} messages")
        
        # Execute chat with LLM service
        response = await llm_service.execute(request.messages)
        
        logger.info(
            f"Chat completed successfully. "
            f"Total messages: {len(response.messages)}, "
            f"Tokens used: {response.usage.total_tokens if response.usage else 'N/A'}"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat: {str(e)}"
        )
