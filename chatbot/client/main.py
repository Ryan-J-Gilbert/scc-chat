"""Main entry point for the terminal chatbot client."""

import logging
import sys
from typing import List, Dict, Any

from client.services.api_client import ChatbotAPIClient
from client.ui.terminal_interface import TerminalChatInterface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChatbotClient:
    """Main chatbot client orchestrator."""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        Initialize the chatbot client.
        
        Args:
            server_url: URL of the chatbot server
        """
        self.api_client = ChatbotAPIClient(base_url=server_url)
        self.ui = TerminalChatInterface()
    
    def check_server(self) -> bool:
        """
        Check if the server is available.
        
        Returns:
            True if server is healthy, False otherwise
        """
        self.ui.display_info("Checking server connection...")
        if not self.api_client.check_health():
            self.ui.display_error(
                "Cannot connect to server. Make sure the server is running at "
                f"{self.api_client.base_url}"
            )
            return False
        
        self.ui.display_info("Connected to server successfully!")
        return True
    
    def process_user_input(self, user_input: str) -> bool:
        """
        Process user input and handle commands.
        
        Args:
            user_input: Raw user input
            
        Returns:
            True to continue, False to exit
        """
        user_input = user_input.strip()
        
        if not user_input:
            return True
        
        # Handle commands
        if user_input.lower() in ["quit", "exit"]:
            self.ui.display_info("Goodbye!")
            return False
        
        if user_input.lower() == "clear":
            self.ui.clear_screen()
            self.ui.clear_messages()
            self.ui.display_info("Chat history cleared!")
            return True
        
        if user_input.lower() == "help":
            self.ui.display_help()
            return True
        
        # Process as a chat message
        self.handle_chat_message(user_input)
        return True
    
    def handle_chat_message(self, message: str):
        """
        Handle a chat message.
        
        Args:
            message: User message content
        """
        # Add user message to UI history
        self.ui.add_message("user", message)
        
        # Get current messages for API
        messages = self.ui.get_messages()
        
        try:
            # Show thinking indicator
            self.ui.display_thinking()
            
            # Send to server
            response_data = self.api_client.send_message(messages)
            
            # Update UI with all messages from response
            self.ui.messages = response_data.get("messages", [])
            
            # Display only the NEW messages from the response
            # This will display the user message we just sent plus assistant's response
            self.ui.display_response(response_data)
            
        except Exception as e:
            logger.error(f"Error handling chat message: {e}", exc_info=True)
            self.ui.display_error(f"Failed to get response: {str(e)}")
    
    def run(self):
        """Run the main chat loop."""
        # Check server availability
        if not self.check_server():
            sys.exit(1)
        
        # Display welcome
        self.ui.display_welcome()
        
        # Main loop
        try:
            while True:
                user_input = self.ui.get_user_input()
                
                if not self.process_user_input(user_input):
                    break
                    
        except KeyboardInterrupt:
            self.ui.display_info("\nGoodbye!")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            self.ui.display_error(f"Unexpected error: {str(e)}")
        finally:
            self.api_client.close()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG-powered chatbot client")
    parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="Server URL (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    client = ChatbotClient(server_url=args.server)
    client.run()


if __name__ == "__main__":
    main()