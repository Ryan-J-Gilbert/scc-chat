"""API client for communicating with the chatbot server."""

import logging
from typing import List, Dict, Any

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class ChatbotAPIClient:
    """Client for interacting with the chatbot API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the chatbot API
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        logger.info(f"Initialized API client with base URL: {self.base_url}")
    
    def check_health(self) -> bool:
        """
        Check if the server is healthy.
        
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json().get("status") == "healthy"
        except RequestException as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def send_message(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send messages to the chat endpoint.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Response dictionary with updated messages
            
        Raises:
            RequestException: If the request fails
        """
        try:
            logger.debug(f"Sending {len(messages)} messages to server")
            
            response = self.session.post(
                f"{self.base_url}/chat",
                json={"messages": messages},
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Received response with {len(data.get('messages', []))} messages")
            
            return data
            
        except RequestException as e:
            logger.error(f"Error sending message: {e}")
            raise
    
    def close(self):
        """Close the session."""
        self.session.close()
