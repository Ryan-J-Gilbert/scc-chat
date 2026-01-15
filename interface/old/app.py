from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TextArea, Static, MarkdownViewer, Button
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
from textual import events
from datetime import datetime
import asyncio


class ChatInput(TextArea):
    """Custom TextArea that sends message on Ctrl+Enter."""
    
    BINDINGS = [
        Binding("ctrl+j", "send", "Send", show=False),
    ]
    
    def action_send(self) -> None:
        """Send the message."""
        self.post_message(self.Submitted(self))
    
    class Submitted(TextArea.Changed):
        """Message posted when send is triggered."""
        pass


class ChatMessage(Horizontal):
    """A single chat message widget."""
    
    def __init__(self, sender: str, message: str, timestamp: str, metadata: dict = None) -> None:
        self.sender = sender
        self.message = message
        self.timestamp = timestamp
        self.metadata = metadata or {}
        super().__init__()
    
    def compose(self) -> ComposeResult:
        if self.sender == "user":
            yield Static("", classes="spacer")
            header = Static(f"[bold cyan]You[/] [dim]{self.timestamp}[/]", classes="message-header")
            formatted_message = self.message.replace('\n', '\n\n')
            content = MarkdownViewer(formatted_message, classes="user-message-content", show_table_of_contents=False)
            yield Vertical(header, content, classes="user-message")
        else:
            header = Static(f"[bold green]Bot[/] [dim]{self.timestamp}[/]", classes="message-header")
            content = MarkdownViewer(self.message, classes="bot-message-content", show_table_of_contents=False)
            
            # Add metadata footer if present
            meta_parts = []
            if self.metadata.get("loading"):
                meta_parts.append("⏳ Typing...")
            else:
                if "model" in self.metadata:
                    meta_parts.append(f"Model: {self.metadata['model']}")
                if "response_time" in self.metadata:
                    meta_parts.append(f"Time: {self.metadata['response_time']:.2f}s")
                if "tokens" in self.metadata:
                    meta_parts.append(f"Tokens: {self.metadata['tokens']}")
            
            meta_text = " • ".join(meta_parts) if meta_parts else ""
            metadata_widget = Static(f"[dim italic]{meta_text}[/]", classes="message-metadata")
            
            yield Vertical(header, content, metadata_widget, classes="bot-message")
            yield Static("", classes="spacer")
    
    def update_metadata(self, metadata: dict) -> None:
        """Update the metadata and refresh the message."""
        self.metadata = metadata
        # Remove old content and remount
        self.remove_children()
        self.mount(*self.compose())


class ChatDisplay(Vertical):
    """Container for chat messages."""
    
    def add_message(self, sender: str, message: str, metadata: dict = None) -> ChatMessage:
        """Add a new message to the chat and return it."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        msg = ChatMessage(sender, message, timestamp, metadata)
        self.mount(msg)
        self.scroll_end(animate=False)
        return msg


class SupportChatbot(App):
    """A support chatbot TUI application."""
    
    CSS = """
    Screen {
        background: #1a1b26;
    }
    
    #chat-container {
        height: 1fr;
        border: round #7aa2f7;
        background: #16161e;
        padding: 1 2;
    }
    
    #chat-display {
        height: 1fr;
        overflow-y: auto;
        padding: 1;
    }
    
    ChatMessage {
        width: 100%;
        height: auto;
        margin: 1 0;
    }
    
    .spacer {
        width: 1fr;
    }
    
    .message-header {
        padding: 0 2;
        height: 1;
    }
    
    .message-metadata {
        padding: 0 2 1 2;
        height: 1;
        color: #565f89;
    }
    
    .user-message {
        background: #2d3f5f;
        border: round #7aa2f7;
        width: auto;
        max-width: 80%;
        height: auto;
        padding: 0 0 1 0;
    }
    
    .user-message-content {
        background: #2d3f5f;
        color: #c0caf5;
        padding: 0 2;
        height: auto;
        overflow: hidden;
        scrollbar-background: #2d3f5f;
    }
    
    .bot-message {
        background: #1f2937;
        border: round #9ece6a;
        width: auto;
        max-width: 80%;
        height: auto;
        padding: 0;
    }
    
    .bot-message-content {
        background: #1f2937;
        color: #c0caf5;
        padding: 0 2;
        height: auto;
        overflow: hidden;
        scrollbar-background: #1f2937;
    }
    
    MarkdownViewer {
        background: transparent;
        padding: 0;
        height: auto;
        overflow: hidden;
    }
    
    MarkdownViewer > * {
        background: transparent;
    }
    
    #input-container {
        height: 8;
        padding: 0;
        background: #16161e;
        border: round #bb9af7;
    }
    
    #message-input {
        width: 1fr;
        height: 1fr;
        border: solid #414868;
        background: #1a1b26;
        color: #c0caf5;
        margin: 1;
    }
    
    #message-input:focus {
        border: solid #7aa2f7;
    }
    
    #send-button {
        width: 8;
        height: 3;
        margin: 1 1 1 0;
        min-width: 8;
    }
    
    Header {
        background: #1f2335;
        color: #7aa2f7;
    }
    
    Footer {
        background: #1f2335;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+j", "send_message", "Send", show=True, key_display="^J"),
        Binding("ctrl+d", "clear", "Clear Chat", show=True),
        Binding("ctrl+c", "quit", "Quit", show=True),
    ]
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        
        with Container(id="chat-container"):
            yield ChatDisplay(id="chat-display")
        
        with Horizontal(id="input-container"):
            yield ChatInput(id="message-input", language="markdown")
            yield Button("Send", id="send-button", variant="success")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app starts."""
        self.chat_display = self.query_one("#chat-display", ChatDisplay)
        self.message_input = self.query_one("#message-input", ChatInput)
        
        self.theme = "textual-dark"
        
        # Welcome message with metadata
        self.chat_display.add_message(
            "bot",
            "👋 Welcome to Support Chat! How can I help you today?\n\n*Press **Ctrl+J** or click **Send** button to send your message*",
            metadata={"model": "demo-bot", "version": "1.0"}
        )
        
        self.message_input.focus()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle send button click."""
        if event.button.id == "send-button":
            await self.send_message()
    
    async def on_chat_input_submitted(self, event: ChatInput.Submitted) -> None:
        """Handle when user presses Ctrl+J in the input."""
        await self.send_message()
    
    async def action_send_message(self) -> None:
        """Handle sending a message via binding."""
        await self.send_message()
    
    async def send_message(self) -> None:
        """Common method to handle message sending."""
        message = self.message_input.text.strip()
        
        if not message:
            return
        
        # Clear input
        self.message_input.clear()
        
        # Add user message
        self.chat_display.add_message("user", message)
        
        # Add loading message
        loading_msg = self.chat_display.add_message(
            "bot", 
            "*Thinking...*",
            metadata={"loading": True}
        )
        
        # Track response time
        start_time = asyncio.get_event_loop().time()
        
        # Simulate bot processing
        await asyncio.sleep(1)
        
        # Generate bot response
        bot_response = self.generate_response(message)
        
        # Calculate response time
        response_time = asyncio.get_event_loop().time() - start_time
        
        # Update the loading message with actual response and metadata
        loading_msg.message = bot_response
        loading_msg.metadata = {
            "model": "demo-chatbot-v1",
            "response_time": response_time,
            "tokens": len(bot_response.split())  # Simple token estimation
        }
        loading_msg.update_metadata(loading_msg.metadata)
    
    def generate_response(self, user_message: str) -> str:
        """
        Generate a response to the user's message.
        Replace this with your actual chatbot logic/API calls.
        """
        message_lower = user_message.lower()
        
        if "hello" in message_lower or "hi" in message_lower:
            return "Hello! How can I assist you today?"
        elif "code" in message_lower or "python" in message_lower:
            return """Here's a simple Python example:

```python
def greet(name):
    return f"Hello, {name}!"

# Usage
message = greet("World")
print(message)
```

This function takes a name and returns a **greeting message**."""
        elif "help" in message_lower:
            return """I'm here to help! You can ask me about:

- **Account issues**
- **Technical support** 
- **Billing questions**
- **General inquiries**

Just type your question and I'll do my best to assist you!"""
        elif "thanks" in message_lower or "thank you" in message_lower:
            return "You're welcome! Is there anything else I can help you with? 😊"
        elif "bye" in message_lower or "goodbye" in message_lower:
            return "Goodbye! Have a great day! Feel free to come back if you need help."
        else:
            return f"I understand you said: *'{user_message}'*. Let me help you with that.\n\n(This is a demo response - integrate your actual chatbot here!)"
    
    def action_clear(self) -> None:
        """Clear all chat messages."""
        self.chat_display.remove_children()
        self.chat_display.add_message(
            "bot",
            "Chat cleared. How can I help you?",
            metadata={"model": "demo-bot", "tokens":120}
        )


def main():
    app = SupportChatbot()
    app.run()


if __name__ == "__main__":
    main()