from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, Markdown
from textual.containers import HorizontalGroup, VerticalGroup, VerticalScroll


class ChatMessage(VerticalGroup):
    def __init__(self, text: str, **kwargs):
        super().__init__(**kwargs)
        self.text = text

    def compose(self) -> ComposeResult:
        yield Markdown(self.text)

class ChatHistory(VerticalGroup):
    def compose(self) -> ComposeResult:
        yield ChatMessage("## Hello there!", classes="bot")
        yield ChatMessage("**Hi!** How are you?", classes="bot")
        yield ChatMessage("- This is a list item", classes="bot")

class InputBox(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield Input(
            placeholder="What's the issue?",
            id="chat_input",
        )

class ChatBotApp(App):

    CSS_PATH = "styling.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        with VerticalScroll(id="chat_scroll"):
            yield ChatHistory()
        yield InputBox()

    def on_mount(self) -> None:
        self.title = "SCC Chatbot"
        self.sub_title = "Careful! Responses may be inaccurate. Do not send sensitive info."

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        message = event.value.strip()
        if not message:
            return

        # Add message to chat history
        chat_history = self.query_one(ChatHistory)
        chat_history.mount(ChatMessage(message, classes="user"))
        self.query_one("#chat_scroll", VerticalScroll).scroll_end(animate=False)


        # Clear input
        event.input.value = ""


if __name__ == "__main__":
    app = ChatBotApp()
    app.run()