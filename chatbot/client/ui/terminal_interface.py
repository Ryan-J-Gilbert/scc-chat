"""Terminal-based chat interface using Rich library."""

import logging
from typing import List, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.text import Text

logger = logging.getLogger(__name__)


class TerminalChatInterface:
    """Rich terminal interface for the chatbot."""
    
    def __init__(self):
        """Initialize the terminal interface."""
        self.console = Console()
        self.messages: List[Dict[str, Any]] = []
        self.displayed_message_count = 0  # Track how many messages we've displayed
    
    def display_welcome(self):
        """Display welcome message."""
        welcome_text = """
# RAG-Powered Chatbot

Welcome! I can help answer your questions using my knowledge base.

**Commands:**
- Type your question and press Enter
- Type `quit` or `exit` to end the conversation
- Type `clear` to clear the chat history
- Type `help` to see this message again

Ask me anything!
        """
        self.console.print(Panel(Markdown(welcome_text), border_style="blue"))
    
    def display_help(self):
        """Display help message."""
        help_text = """
**Available Commands:**
- `quit` or `exit` - End the conversation
- `clear` - Clear chat history
- `help` - Show this help message

Just type your question and I'll do my best to help!
        """
        self.console.print(Panel(Markdown(help_text), border_style="yellow"))
    
    def get_user_input(self) -> str:
        """
        Get input from the user.
        
        Returns:
            User input string
        """
        return Prompt.ask("\n[bold cyan]You[/bold cyan]")
    
    def display_user_message(self, message: str):
        """
        Display a user message.
        
        Args:
            message: User message to display
        """
        self.console.print(f"\n[bold cyan]You:[/bold cyan] {message}")
    
    def display_assistant_message(self, message: str):
        """
        Display an assistant message.
        
        Args:
            message: Assistant message to display
        """
        self.console.print("\n[bold green]Assistant:[/bold green]")
        self.console.print(Markdown(message))
    
    def display_tool_call(self, tool_name: str, arguments: str):
        """
        Display a tool call.
        
        Args:
            tool_name: Name of the tool being called
            arguments: Tool arguments
        """
        text = Text(f"🔧 Calling tool: {tool_name}", style="yellow italic")
        self.console.print(text)
    
    def display_error(self, error: str):
        """
        Display an error message.
        
        Args:
            error: Error message to display
        """
        self.console.print(f"\n[bold red]Error:[/bold red] {error}")
    
    def display_info(self, info: str):
        """
        Display an info message.
        
        Args:
            info: Info message to display
        """
        self.console.print(f"\n[italic blue]{info}[/italic blue]")
    
    def display_thinking(self):
        """Display a thinking indicator."""
        self.console.print("\n[italic dim]Thinking...[/italic dim]")
    
    def clear_screen(self):
        """Clear the terminal screen."""
        self.console.clear()
        self.display_welcome()
        self.displayed_message_count = 0  # Reset counter
    
    def add_message(self, role: str, content: str):
        """
        Add a message to the conversation history.
        
        Args:
            role: Message role (user/assistant/tool)
            content: Message content
        """
        self.messages.append({
            "role": role,
            "content": content
        })
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """
        Get the current message history.
        
        Returns:
            List of message dictionaries
        """
        return self.messages
    
    def clear_messages(self):
        """Clear the message history."""
        self.messages = []
        self.displayed_message_count = 0  # Reset counter
    
    def display_response(self, response_data: Dict[str, Any]):
        """
        Display only the NEW messages from the server response.
        
        Args:
            response_data: Response dictionary from API
        """
        messages = response_data.get("messages", [])
        
        # Only display messages we haven't displayed yet
        new_messages = messages[self.displayed_message_count:]
        
        for msg in new_messages:
            role = msg.get("role")
            content = msg.get("content")
            tool_calls = msg.get("tool_calls")
            
            # Skip system messages (don't display them)
            if role == "system":
                continue
            
            if role == "user":
                # Display user message
                self.display_user_message(content)
            elif role == "assistant":
                if tool_calls:
                    # Display tool calls
                    for tc in tool_calls:
                        self.display_tool_call(tc["name"], tc["arguments"])
                if content:
                    # Display assistant message
                    self.display_assistant_message(content)
            elif role == "tool":
                # Optionally display tool results (currently hidden)
                # You could uncomment this to see tool results:
                # self.console.print(f"[dim]Tool result: {content[:100]}...[/dim]")
                pass
        
        # Update the displayed message count
        self.displayed_message_count = len(messages)
        
        # Display usage if available
        usage = response_data.get("usage")
        if usage:
            tokens = usage.get("total_tokens", 0)
            self.console.print(f"\n[dim italic]Tokens used: {tokens}[/dim italic]")