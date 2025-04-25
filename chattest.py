import re
import sys
import os
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Union, Tuple, Dict
from urllib.parse import urlparse

# Check if running in a compatible terminal
try:
    import pygments
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.formatters import TerminalFormatter
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

class Role(Enum):
    SYSTEM = auto()
    USER = auto()
    ASSISTANT = auto()

@dataclass
class ChatMessage:
    role: Role
    content: str
    name: Optional[str] = None

class ContentElement:
    """Base class for all content elements"""
    pass

class TextSegment(ContentElement):
    def __init__(self, text: str):
        self.text = text

class CodeBlock(ContentElement):
    def __init__(self, code: str, language: Optional[str] = None):
        self.code = code
        self.language = language

class Heading(ContentElement):
    def __init__(self, text: str, level: int):
        self.text = text
        self.level = level  # 1 for h1, 2 for h2, etc.

class ListItem(ContentElement):
    def __init__(self, text: str, indent_level: int = 0, ordered: bool = False, index: Optional[int] = None):
        self.text = text
        self.indent_level = indent_level
        self.ordered = ordered
        self.index = index

class Link(ContentElement):
    def __init__(self, text: str, url: str):
        self.text = text
        self.url = url

class Image(ContentElement):
    def __init__(self, alt_text: str, url: str):
        self.alt_text = alt_text
        self.url = url

class BlockQuote(ContentElement):
    def __init__(self, text: str):
        self.text = text

class HorizontalRule(ContentElement):
    pass

class ChatFormatter:
    """A library for formatting chat messages similar to LLM interfaces with enhanced Markdown support."""
    
    # ANSI color codes
    RESET = "\033[0m"
    BOLD = "\033[1m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    STRIKETHROUGH = "\033[9m"
    
    # Text colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    # Clickable link (OSC 8 terminal sequences)
    LINK_START = "\033]8;;"
    LINK_MID = "\033\\"
    LINK_END = "\033]8;;\033\\"
    
    def __init__(self, terminal_width: int = 80, 
                 user_color: str = BLUE,
                 assistant_color: str = GREEN,
                 system_color: str = YELLOW,
                 code_theme: str = "monokai",
                 support_clickable_links: bool = True):
        self.terminal_width = terminal_width
        self.user_color = user_color
        self.assistant_color = assistant_color
        self.system_color = system_color
        self.code_theme = code_theme
        self.support_clickable_links = support_clickable_links
        
        # Check if terminal supports hyperlinks
        self.hyperlinks_supported = False
        if support_clickable_links:
            term = os.environ.get("TERM", "")
            if "xterm" in term or "kitty" in term or "iterm" in term:
                self.hyperlinks_supported = True
    
    def _parse_markdown_links(self, text: str) -> List[Union[str, Link]]:
        """Extract markdown links from text."""
        segments = []
        # Match [text](url) pattern
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        last_end = 0
        
        for match in re.finditer(link_pattern, text):
            # Add text before the link
            if match.start() > last_end:
                segments.append(text[last_end:match.start()])
            
            link_text = match.group(1)
            link_url = match.group(2)
            segments.append(Link(link_text, link_url))
            
            last_end = match.end()
        
        # Add any remaining text
        if last_end < len(text):
            segments.append(text[last_end:])
        
        return segments
    
    def _parse_markdown_images(self, text: str) -> List[Union[str, Image]]:
        """Extract markdown images from text."""
        segments = []
        # Match ![alt text](url) pattern
        image_pattern = r"!\[([^\]]*)\]\(([^)]+)\)"
        last_end = 0
        
        for match in re.finditer(image_pattern, text):
            # Add text before the image
            if match.start() > last_end:
                segments.append(text[last_end:match.start()])
            
            alt_text = match.group(1)
            image_url = match.group(2)
            segments.append(Image(alt_text, image_url))
            
            last_end = match.end()
        
        # Add any remaining text
        if last_end < len(text):
            segments.append(text[last_end:])
        
        return segments
    
    def _parse_headings(self, line: str) -> Optional[Heading]:
        """Parse a line for markdown headings."""
        heading_pattern = r"^(#{1,6})\s+(.+)$"
        match = re.match(heading_pattern, line)
        if match:
            level = len(match.group(1))  # Number of # symbols
            text = match.group(2).strip()
            return Heading(text, level)
        return None
    
    def _parse_list_item(self, line: str) -> Optional[ListItem]:
        """Parse a line for markdown list items."""
        # Unordered list with *, +, or -
        unordered_pattern = r"^(\s*)([\*\+\-])\s+(.+)$"
        # Ordered list with numbers
        ordered_pattern = r"^(\s*)(\d+)[\.\)]\s+(.+)$"
        
        match = re.match(unordered_pattern, line)
        if match:
            indent = len(match.group(1))
            text = match.group(3).strip()
            return ListItem(text, indent_level=indent//2, ordered=False)
        
        match = re.match(ordered_pattern, line)
        if match:
            indent = len(match.group(1))
            index = int(match.group(2))
            text = match.group(3).strip()
            return ListItem(text, indent_level=indent//2, ordered=True, index=index)
        
        return None
    
    def _parse_block_quote(self, line: str) -> Optional[BlockQuote]:
        """Parse a line for markdown block quotes."""
        quote_pattern = r"^>\s*(.*)$"
        match = re.match(quote_pattern, line)
        if match:
            text = match.group(1).strip()
            return BlockQuote(text)
        return None
    
    def _parse_horizontal_rule(self, line: str) -> bool:
        """Parse a line for markdown horizontal rules."""
        hr_pattern = r"^(\*{3,}|-{3,}|_{3,})\s*$"
        return bool(re.match(hr_pattern, line))
    
    def parse_message(self, message: str) -> List[ContentElement]:
        """Parse a message into structured content elements."""
        # First, separate the message into blocks by double newlines (paragraphs)
        blocks = re.split(r"\n\n+", message)
        elements = []
        
        code_block_pattern = r"```([\w+-]*)\n([\s\S]*?)\n```"
        in_code_block = False
        code_language = None
        code_content = []
        
        for block in blocks:
            if in_code_block:
                # Check if this block ends the code block
                if "```" in block:
                    end_index = block.find("```")
                    code_content.append(block[:end_index])
                    elements.append(CodeBlock("\n".join(code_content), code_language))
                    in_code_block = False
                    
                    # Process any remaining content in the block
                    remaining = block[end_index + 3:].strip()
                    if remaining:
                        elements.extend(self.parse_message(remaining))
                else:
                    code_content.append(block)
                continue
            
            # Check for code blocks
            code_match = re.search(code_block_pattern, block)
            if code_match:
                language = code_match.group(1).strip() or None
                code = code_match.group(2)
                elements.append(CodeBlock(code, language))
                continue
            
            # Check if this block starts a code block that continues across blocks
            if "```" in block and block.count("```") % 2 == 1:
                start_index = block.find("```")
                code_starter = block[start_index:].strip()
                code_match = re.match(r"```([\w+-]*)", code_starter)
                if code_match:
                    code_language = code_match.group(1).strip() or None
                    code_content = [code_starter[code_match.end():].strip()]
                    in_code_block = True
                    
                    # Process any content before the code block
                    preceding = block[:start_index].strip()
                    if preceding:
                        elements.extend(self.parse_message(preceding))
                continue
            
            # Process the block line by line for various markdown elements
            lines = block.split("\n")
            i = 0
            while i < len(lines):
                line = lines[i]
                
                # Check for headings
                heading = self._parse_headings(line)
                if heading:
                    elements.append(heading)
                    i += 1
                    continue
                
                # Check for list items
                list_item = self._parse_list_item(line)
                if list_item:
                    elements.append(list_item)
                    i += 1
                    continue
                
                # Check for block quotes
                block_quote = self._parse_block_quote(line)
                if block_quote:
                    elements.append(block_quote)
                    i += 1
                    continue
                
                # Check for horizontal rules
                if self._parse_horizontal_rule(line):
                    elements.append(HorizontalRule())
                    i += 1
                    continue
                
                # If it's regular text, process inline elements
                text = line
                
                # Combine consecutive regular text lines
                text_lines = [text]
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if (not self._parse_headings(next_line) and 
                        not self._parse_list_item(next_line) and
                        not self._parse_block_quote(next_line) and
                        not self._parse_horizontal_rule(next_line)):
                        text_lines.append(next_line)
                        j += 1
                    else:
                        break
                
                i = j
                text = " ".join(text_lines)
                
                # Process inline markdown
                if text.strip():
                    elements.append(TextSegment(text))
        
        return elements
    
    def format_code_block(self, code_block: CodeBlock) -> str:
        """Format a code block with syntax highlighting if available."""
        if not PYGMENTS_AVAILABLE:
            # Simple formatting without pygments
            header = f"{self.BOLD}{self.WHITE}Code"
            if code_block.language:
                header += f" ({code_block.language})"
            header += f":{self.RESET}\n"
            
            # Add simple indentation to code
            formatted_code = "\n".join(f"    {line}" for line in code_block.code.split("\n"))
            
            return f"{header}{formatted_code}\n"
        
        # Use pygments for syntax highlighting
        try:
            if code_block.language:
                lexer = get_lexer_by_name(code_block.language, stripall=True)
            else:
                lexer = guess_lexer(code_block.code)
                
            formatter = TerminalFormatter(bg="dark")
            highlighted = pygments.highlight(code_block.code, lexer, formatter)
            
            # Add a header with the language
            header = f"{self.BOLD}{self.WHITE}Code"
            if code_block.language:
                header += f" ({code_block.language})"
            header += f":{self.RESET}\n"
            
            return f"{header}{highlighted}"
        except Exception:
            # Fall back to plain formatting if anything goes wrong
            return f"{self.BOLD}Code:{self.RESET}\n{code_block.code}\n"
    
    def _wrap_text(self, text: str, width: int, initial_indent: str = "", subsequent_indent: str = "") -> List[str]:
        """Wrap text to fit within specified width."""
        lines = []
        for paragraph in text.split("\n"):
            if not paragraph:
                lines.append("")
                continue
                
            current_line = initial_indent
            words = paragraph.split(" ")
            
            for word in words:
                if len(current_line) + len(word) + 1 <= width:
                    if current_line == initial_indent:
                        current_line += word
                    else:
                        current_line += " " + word
                else:
                    lines.append(current_line)
                    current_line = subsequent_indent + word
            
            if current_line:
                lines.append(current_line)
                
        return lines
    
    def format_text_segment(self, segment: TextSegment, role: Role, indent: str = "") -> str:
        """Format a text segment with markdown-like formatting."""
        text = segment.text
        
        # Process links first and collect them for later rendering
        link_segments = self._parse_markdown_links(text)
        processed_text = ""
        
        for item in link_segments:
            if isinstance(item, str):
                # Process inline formatting for text parts
                processed_item = item
                # Bold: **text**
                processed_item = re.sub(r"\*\*(.*?)\*\*", f"{self.BOLD}\\1{self.RESET}", processed_item)
                # Italic: *text* or _text_
                processed_item = re.sub(r"(\*|_)(.*?)\1", f"{self.ITALIC}\\2{self.RESET}", processed_item)
                # Strikethrough: ~~text~~
                processed_item = re.sub(r"~~(.*?)~~", f"{self.STRIKETHROUGH}\\1{self.RESET}", processed_item)
                # Code: `text`
                processed_item = re.sub(r"`(.*?)`", f"{self.BG_BLACK}{self.WHITE}\\1{self.RESET}", processed_item)
                
                processed_text += processed_item
            elif isinstance(item, Link):
                # Format as a clickable link if supported
                if self.hyperlinks_supported:
                    processed_text += f"{self.LINK_START}{item.url}{self.LINK_MID}{self.UNDERLINE}{self.CYAN}{item.text}{self.RESET}{self.LINK_END}"
                else:
                    processed_text += f"{self.UNDERLINE}{self.CYAN}{item.text}{self.RESET} ({item.url})"
        
        width = self.terminal_width - len(indent)
        wrapped_lines = self._wrap_text(processed_text, width, indent, indent)
        return "\n".join(wrapped_lines)
    
    def format_heading(self, heading: Heading, indent: str = "") -> str:
        """Format a heading with appropriate styling."""
        # Choose formatting based on heading level
        if heading.level == 1:
            style = f"{self.BOLD}{self.UNDERLINE}{self.WHITE}"
        elif heading.level == 2:
            style = f"{self.BOLD}{self.WHITE}"
        else:
            style = f"{self.BOLD}"
        
        # Add appropriate indentation for heading levels
        level_indent = indent
        
        # Format the heading text
        formatted = f"{level_indent}{style}{heading.text}{self.RESET}"
        
        # Add underline for h1 and h2
        if heading.level <= 2:
            width = min(len(heading.text), self.terminal_width - len(level_indent) - 4)
            formatted += f"\n{level_indent}{'=' if heading.level == 1 else '-' * width}"
        
        return formatted
    
    def format_list_item(self, item: ListItem, indent: str = "") -> str:
        """Format a list item with proper indentation and bullet style."""
        # Calculate indentation based on level
        list_indent = " " * (item.indent_level * 2)
        
        # Choose bullet style
        if item.ordered:
            bullet = f"{item.index or 1}."
        else:
            bullet = "•"
        
        # Format the item with proper indentation
        item_indent = f"{indent}{list_indent}{bullet} "
        subsequent_indent = f"{indent}{list_indent}  "
        
        # Process the text for inline formatting
        processed_text = item.text
        # Bold: **text**
        processed_text = re.sub(r"\*\*(.*?)\*\*", f"{self.BOLD}\\1{self.RESET}", processed_text)
        # Italic: *text* or _text_
        processed_text = re.sub(r"(\*|_)(.*?)\1", f"{self.ITALIC}\\2{self.RESET}", processed_text)
        
        # Wrap the text
        width = self.terminal_width - len(item_indent)
        wrapped_lines = self._wrap_text(processed_text, width, item_indent, subsequent_indent)
        
        return "\n".join(wrapped_lines)
    
    def format_block_quote(self, quote: BlockQuote, indent: str = "") -> str:
        """Format a blockquote with proper styling."""
        quote_indent = f"{indent}> "
        subsequent_indent = f"{indent}> "
        
        # Process the text for inline formatting
        processed_text = quote.text
        # Apply a distinct style for blockquotes
        processed_text = f"{self.ITALIC}{self.CYAN}{processed_text}{self.RESET}"
        
        # Wrap the text
        width = self.terminal_width - len(quote_indent)
        wrapped_lines = self._wrap_text(processed_text, width, quote_indent, subsequent_indent)
        
        return "\n".join(wrapped_lines)
    
    def format_horizontal_rule(self, rule: HorizontalRule, indent: str = "") -> str:
        """Format a horizontal rule."""
        width = self.terminal_width - len(indent) * 2
        return f"{indent}{'-' * width}"
    
    def format_image(self, image: Image, indent: str = "") -> str:
        """Format an image reference (as text in terminal)."""
        return f"{indent}[Image: {image.alt_text}] ({image.url})"
    
    def format_element(self, element: ContentElement, role: Role, indent: str = "") -> str:
        """Format any content element based on its type."""
        if isinstance(element, TextSegment):
            return self.format_text_segment(element, role, indent)
        elif isinstance(element, CodeBlock):
            return self.format_code_block(element)
        elif isinstance(element, Heading):
            return self.format_heading(element, indent)
        elif isinstance(element, ListItem):
            return self.format_list_item(element, indent)
        elif isinstance(element, BlockQuote):
            return self.format_block_quote(element, indent)
        elif isinstance(element, HorizontalRule):
            return self.format_horizontal_rule(element, indent)
        elif isinstance(element, Image):
            return self.format_image(element, indent)
        elif isinstance(element, Link):
            # Links should be processed within text segments
            pass
        return ""
    
    def format_chat_message(self, message: ChatMessage) -> str:
        """Format a complete chat message with enhanced markdown support."""
        elements = self.parse_message(message.content)
        
        # Set color and alignment based on role
        if message.role == Role.USER:
            role_color = self.user_color
            role_name = message.name or "User"
            # left aligned # Right-aligned for user messages
            base_indent = "" #" " * (self.terminal_width // 2)
        elif message.role == Role.ASSISTANT:
            role_color = self.assistant_color
            role_name = message.name or "Assistant"
            # Left-aligned for assistant
            base_indent = ""
        else:  # SYSTEM
            role_color = self.system_color
            role_name = message.name or "System"
            # Left-aligned for system
            base_indent = ""
        
        # Format the header
        if message.role == Role.USER:
            # Right-aligned header for user
            header_padding = "" #" " * (self.terminal_width - len(role_name) - 1)
            header = f"{header_padding}{role_color}{self.BOLD}{role_name}:{self.RESET}\n"
        else:
            # Left-aligned header for others
            header = f"{base_indent}{role_color}{self.BOLD}{role_name}:{self.RESET}\n"
        
        # Format the content
        formatted_content = []
        for element in elements:
            formatted_element = self.format_element(element, message.role, base_indent)
            if formatted_element:
                formatted_content.append(formatted_element)
        
        return header + "\n".join(formatted_content) + "\n"
    
    def format_conversation(self, messages: List[ChatMessage]) -> str:
        """Format a complete conversation."""
        formatted_messages = []
        for message in messages:
            formatted_messages.append(self.format_chat_message(message))
            formatted_messages.append("-" * self.terminal_width)  # Separator
        
        return "\n".join(formatted_messages)


# Example usage
if __name__ == "__main__":
    # Create a formatter
    formatter = ChatFormatter(terminal_width=80)
    
    # Create some messages
    conversation = [
        ChatMessage(
            role=Role.USER,
            content="# Question about HTTP Libraries\n\nCan you explain how to use Python's `requests` library? I've heard it's good for API calls."
        ),
        ChatMessage(
            role=Role.ASSISTANT,
            content="# Python Requests Library\n\nThe `requests` library is one of the most popular HTTP libraries for Python.\n\n"
                   "## Basic Usage\n\nHere's a basic example:\n\n"
                   "```python\n"
                   "import requests\n\n"
                   "# Make a GET request\n"
                   "response = requests.get('https://api.example.com/data')\n\n"
                   "# Check if the request was successful\n"
                   "if response.status_code == 200:\n"
                   "    # Access the response data\n"
                   "    data = response.json()\n"
                   "    print(data)\n"
                   "else:\n"
                   "    print(f'Request failed with status code {response.status_code}')\n"
                   "```\n\n"
                   "## Making POST Requests\n\n"
                   "You can also make POST requests:\n\n"
                   "```python\n"
                   "# Make a POST request with JSON data\n"
                   "response = requests.post(\n"
                   "    'https://api.example.com/submit',\n"
                   "    json={'name': 'John', 'age': 30}\n"
                   ")\n"
                   "```\n\n"
                   "## Additional Features\n\n"
                   "* **Headers**: Add custom headers to your requests\n"
                   "* **Authentication**: Support for various auth methods\n"
                   "* **Sessions**: Maintain cookies across requests\n"
                   "* **Timeouts**: Control how long to wait for responses\n\n"
                   "For more information, check out the [official documentation](https://docs.python-requests.org/).\n"
                   "1. test\n"
                   "2. test\n"
                   "3. test\n"
        )
    ]
    
    # Format and print the conversation
    print(formatter.format_conversation(conversation))