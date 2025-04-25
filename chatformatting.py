import re
import sys
import os

# Check if running in a compatible terminal
try:
    import pygments
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.formatters import TerminalFormatter
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

# Constants for roles
ROLE_SYSTEM = "system"
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"

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

def wrap_text(text, width, initial_indent="", subsequent_indent=""):
    """Wrap text to fit within specified width."""



    # NOT WRAPPING TEXT FOR DEBUG!!!
    return [text]




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

def parse_markdown_links(text):
    """Extract markdown links from text."""
    segments = []
    # Match [text](url) pattern
    link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    last_end = 0
    
    for match in re.finditer(link_pattern, text):
        # Add text before the link
        if match.start() > last_end:
            segments.append(("text", text[last_end:match.start()]))
        
        link_text = match.group(1)
        link_url = match.group(2)
        segments.append(("link", (link_text, link_url)))
        
        last_end = match.end()
    
    # Add any remaining text
    if last_end < len(text):
        segments.append(("text", text[last_end:]))
    
    return segments

def format_code_block(code, language=None, terminal_width=80):
    """Format a code block with syntax highlighting if available."""
    if not PYGMENTS_AVAILABLE:
        # Simple formatting without pygments
        header = f"{BOLD}{WHITE}Code"
        if language:
            header += f" ({language})"
        header += f":{RESET}\n"
        
        # Add simple indentation to code
        formatted_code = "\n".join(f"    {line}" for line in code.split("\n"))
        sep = "="*terminal_width
        return f"\n{header}{sep}\n{formatted_code}{sep}\n\n"
    
    # Use pygments for syntax highlighting
    try:
        if language:
            lexer = get_lexer_by_name(language, stripall=True)
        else:
            lexer = guess_lexer(code)
            
        formatter = TerminalFormatter(bg="dark")
        highlighted = pygments.highlight(code, lexer, formatter)
        
        # Add a header with the language
        header = f"{BOLD}{WHITE}Code"
        if language:
            header += f" ({language})"
        header += f":{RESET}\n"
        sep = "="*terminal_width
        return f"\n{header}{sep}\n{highlighted}{sep}\n"
    except Exception:
        # Fall back to plain formatting if anything goes wrong
        return f"{BOLD}Code:{RESET}\n{code}\n"

def format_text_with_markdown(text, terminal_width=80, indent="", hyperlinks_supported=True):
    """Format text with markdown-like formatting."""
    # Process links first and collect them for later rendering
    link_segments = parse_markdown_links(text)
    processed_text = ""
    
    for segment_type, content in link_segments:
        if segment_type == "text":
            # Process inline formatting for text parts
            processed_item = content
            # Bold: **text**
            processed_item = re.sub(r"\*\*(.*?)\*\*", f"{BOLD}\\1{RESET}", processed_item)
            # Italic: *text* or _text_
            processed_item = re.sub(r"(\*|_)(.*?)\1", f"{ITALIC}\\2{RESET}", processed_item)
            # Strikethrough: ~~text~~
            processed_item = re.sub(r"~~(.*?)~~", f"{STRIKETHROUGH}\\1{RESET}", processed_item)
            # Code: `text`
            processed_item = re.sub(r"`(.*?)`", f"{BG_BLACK}{WHITE}\\1{RESET}", processed_item)
            
            processed_text += processed_item
        elif segment_type == "link":
            link_text, link_url = content
            # Format as a clickable link if supported
            if hyperlinks_supported:
                processed_text += f"{LINK_START}{link_url}{LINK_MID}{UNDERLINE}{CYAN}{link_text}{RESET}{LINK_END}"
            else:
                processed_text += f"{UNDERLINE}{CYAN}{link_text}{RESET} ({link_url})"
    
    width = terminal_width - len(indent)
    wrapped_lines = wrap_text(processed_text, width, indent, indent)
    return "\n".join(wrapped_lines)

def parse_markdown_elements(text):
    """Parse text into various markdown elements."""
    elements = []
    lines = text.split("\n")
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for code blocks
        if line.strip().startswith("```"):
            code_start = i
            language = line.strip()[3:].strip()
            code_lines = []
            i += 1
            
            # Find the end of the code block
            while i < len(lines) and not lines[i].strip().endswith("```"):
                code_lines.append(lines[i])
                i += 1
                
            if i < len(lines):  # Found closing ```
                elements.append(("code", ("\n".join(code_lines), language)))
                i += 1
            else:  # No closing ```, treat as text
                elements.append(("text", "\n".join(lines[code_start:])))
                break
                
            continue
        
        # Check for headings
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            elements.append(("heading", (text, level)))
            i += 1
            continue
        
        # Check for list items
        list_match = re.match(r"^(\s*)([\*\+\-]|\d+[\.\)])\s+(.+)$", line)
        if list_match:
            indent = len(list_match.group(1))
            marker = list_match.group(2)
            text = list_match.group(3).strip()
            ordered = marker[0].isdigit()
            index = int(marker[:-1]) if ordered else None
            elements.append(("list_item", (text, indent//2, ordered, index)))
            i += 1
            continue
        
        # Check for block quotes
        quote_match = re.match(r"^>\s*(.*)$", line)
        if quote_match:
            text = quote_match.group(1).strip()
            elements.append(("blockquote", text))
            i += 1
            continue
        
        # Check for horizontal rules
        if re.match(r"^(\*{3,}|-{3,}|_{3,})\s*$", line):
            elements.append(("hr", None))
            i += 1
            continue
        
        # Regular text
        # Collect consecutive text lines
        text_lines = [line]
        j = i + 1
        while j < len(lines):
            next_line = lines[j]
            if (not re.match(r"^(#{1,6})\s+(.+)$", next_line) and
                not re.match(r"^(\s*)([\*\+\-]|\d+[\.\)])\s+(.+)$", next_line) and
                not re.match(r"^>\s*(.*)$", next_line) and
                not re.match(r"^(\*{3,}|-{3,}|_{3,})\s*$", next_line) and
                not next_line.strip().startswith("```")):
                text_lines.append(next_line)
                j += 1
            else:
                break
        
        text = "\n".join(text_lines)
        if text.strip():
            elements.append(("text", text))
        i = j
    
    return elements

def format_heading(text, level, indent="", terminal_width=80):
    """Format a heading with appropriate styling."""
    # Choose formatting based on heading level
    if level == 1:
        style = f"{BOLD}{UNDERLINE}{WHITE}"
    elif level == 2:
        style = f"{BOLD}{WHITE}"
    else:
        style = f"{BOLD}"
    
    # Format the heading text
    formatted = f"{indent}{style}{text}{RESET}"
    
    # Add underline for h1 and h2
    if level <= 2:
        width = min(len(text), terminal_width - len(indent) - 4)
        formatted += f"\n{indent}{'=' if level == 1 else '-' * width}"
    
    return formatted

def format_list_item(text, indent_level=0, ordered=False, index=None, base_indent="", terminal_width=80):
    """Format a list item with proper indentation and bullet style."""
    # Calculate indentation based on level
    list_indent = " " * (indent_level * 2)
    
    # Choose bullet style
    if ordered:
        bullet = f"{index or 1}."
    else:
        bullet = "•"
    
    # Format the item with proper indentation
    item_indent = f"{base_indent}{list_indent}{bullet} "
    subsequent_indent = f"{base_indent}{list_indent}  "
    
    # Process the text for inline formatting
    processed_text = text
    # Bold: **text**
    processed_text = re.sub(r"\*\*(.*?)\*\*", f"{BOLD}\\1{RESET}", processed_text)
    # Italic: *text* or _text_
    processed_text = re.sub(r"(\*|_)(.*?)\1", f"{ITALIC}\\2{RESET}", processed_text)
    
    # Wrap the text
    width = terminal_width - len(item_indent)
    wrapped_lines = wrap_text(processed_text, width, item_indent, subsequent_indent)
    
    return "\n".join(wrapped_lines)

def format_blockquote(text, indent="", terminal_width=80):
    """Format a blockquote with proper styling."""
    quote_indent = f"{indent}> "
    subsequent_indent = f"{indent}> "
    
    # Apply a distinct style for blockquotes
    processed_text = f"{ITALIC}{CYAN}{text}{RESET}"
    
    # Wrap the text
    width = terminal_width - len(quote_indent)
    wrapped_lines = wrap_text(processed_text, width, quote_indent, subsequent_indent)
    
    return "\n".join(wrapped_lines)

def format_horizontal_rule(indent="", terminal_width=80):
    """Format a horizontal rule."""
    width = terminal_width - len(indent) * 2
    return f"{indent}{'-' * width}"

def format_message(content, role, terminal_width=80, user_color=BLUE, assistant_color=GREEN, system_color=YELLOW, 
                  support_clickable_links=True, name=None):
    """Format a complete message with enhanced markdown support."""
    elements = parse_markdown_elements(content)
    
    # Set color and alignment based on role
    if role == ROLE_USER:
        role_color = user_color
        role_name = name or "User"
        base_indent = ""
    elif role == ROLE_ASSISTANT:
        role_color = assistant_color
        role_name = name or "Assistant"
        base_indent = ""
    else:  # SYSTEM
        role_color = system_color
        role_name = name or "System"
        base_indent = ""
    
    # Format the header
    header = f"{base_indent}{role_color}{BOLD}{role_name}:{RESET}\n"
    
    # Check if terminal supports hyperlinks
    hyperlinks_supported = False
    if support_clickable_links:
        term = os.environ.get("TERM", "")
        if "xterm" in term or "kitty" in term or "iterm" in term:
            hyperlinks_supported = True
    
    # Format the content
    formatted_content = []
    for element_type, element_data in elements:
        if element_type == "text":
            formatted_element = format_text_with_markdown(
                element_data, terminal_width, base_indent, hyperlinks_supported
            )
            formatted_content.append(formatted_element)
        elif element_type == "code":
            code, language = element_data
            formatted_element = format_code_block(code, language, terminal_width)
            formatted_content.append(formatted_element)
        elif element_type == "heading":
            text, level = element_data
            formatted_element = format_heading(text, level, base_indent, terminal_width)
            formatted_content.append(formatted_element)
        elif element_type == "list_item":
            text, indent_level, ordered, index = element_data
            formatted_element = format_list_item(
                text, indent_level, ordered, index, base_indent, terminal_width
            )
            formatted_content.append(formatted_element)
        elif element_type == "blockquote":
            formatted_element = format_blockquote(element_data, base_indent, terminal_width)
            formatted_content.append(formatted_element)
        elif element_type == "hr":
            formatted_element = format_horizontal_rule(base_indent, terminal_width)
            formatted_content.append(formatted_element)
    
    return header + "\n".join(formatted_content) + "\n"

def format_conversation(messages, terminal_width=80, user_color=BLUE, assistant_color=GREEN, system_color=YELLOW):
    """Format a complete conversation."""
    formatted_messages = []
    for message in messages:
        role = message.get("role", ROLE_USER)
        content = message.get("content", "")
        name = message.get("name")
        
        formatted_message = format_message(
            content, role, terminal_width, user_color, assistant_color, system_color, name=name
        )
        formatted_messages.append(formatted_message)
        formatted_messages.append("-" * terminal_width)  # Separator
    
    return "\n".join(formatted_messages)

def print_streaming_response(response_stream, terminal_width=80, assistant_color=GREEN):
    """Print streaming response tokens as they arrive with formatting.
    
    Args:
        response_stream: Iterator of response chunks from the API
        terminal_width: Width of the terminal
        assistant_color: Color to use for the assistant's messages
        
    Returns:
        str: The complete collected response
    """
    collected_content = ""
    buffer = ""
    formatted_header = f"{assistant_color}{BOLD}Assistant:{RESET}\n"
    
    # Print header first
    print(formatted_header, end="", flush=True)
    
    for chunk in response_stream:
        if hasattr(chunk, 'choices') and chunk.choices and len(chunk.choices) > 0:
            # Handle different API response formats
            if hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content
            elif hasattr(chunk.choices[0], 'text'):
                content = chunk.choices[0].text
            else:
                content = ""
                
            if content:
                buffer += content
                collected_content += content
                
                # Try to find complete markdown elements or sentences to format
                if '\n' in buffer or '. ' in buffer or '? ' in buffer or '! ' in buffer:
                    # Simple formatting for streaming output - handle basic markdown
                    formatted_buffer = buffer
                    # Bold
                    formatted_buffer = re.sub(r"\*\*(.*?)\*\*", f"{BOLD}\\1{RESET}", formatted_buffer)
                    # Italic
                    formatted_buffer = re.sub(r"(\*|_)(.*?)\1", f"{ITALIC}\\2{RESET}", formatted_buffer)
                    # Code
                    formatted_buffer = re.sub(r"`(.*?)`", f"{BG_BLACK}{WHITE}\\1{RESET}", formatted_buffer)
                    
                    print(formatted_buffer, end="", flush=True)
                    buffer = ""
                else:
                    print(content, end="", flush=True)
    
    # Print any remaining buffer content
    if buffer:
        print(buffer, end="", flush=True)
        
    print()  # Add a newline at the end
    return collected_content

def print_streaming_response(response_stream, terminal_width=80, assistant_color=GREEN):
    """Stream response tokens as they arrive, then format the entire response when complete.
    
    This function:
    1. Displays raw text as it streams in for immediate feedback
    2. Once streaming is complete, formats the entire text with markdown
    3. Erases the raw text and replaces it with the formatted version
    
    Args:
        response_stream: Iterator of response chunks from the API
        terminal_width: Width of the terminal
        assistant_color: Color to use for the assistant's messages
        
    Returns:
        str: The complete collected response
    """
    collected_content = ""
    formatted_header = "\n" # f"{assistant_color}{BOLD}Assistant:{RESET}\n"
    
    # Print header first
    # NOT PRINTING FOR NOW!
    # print(formatted_header, end="", flush=True)
    line_count = 1  # Header takes one line
    # line_count = 0
    
    # Stream in the raw content first
    for chunk in response_stream:
        if hasattr(chunk, 'choices') and chunk.choices and len(chunk.choices) > 0:
            # Handle different API response formats
            if hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content
            elif hasattr(chunk.choices[0], 'text'):
                content = chunk.choices[0].text
            else:
                content = ""
                
            if content:
                # Count newlines to track how much to erase later
                line_count += content.count('\n')
                print(content, end="", flush=True)
                collected_content += content
    
    # Add a newline at the end of the raw content
    print()
    line_count += 1
    
    # Now format the entire content
    formatted_message = format_message(
        collected_content, ROLE_ASSISTANT, 
        terminal_width=terminal_width, 
        assistant_color=assistant_color
    )
    
    # Count lines in the formatted message (for cursor positioning)
    formatted_lines = formatted_message.count('\n') + 1
    
    # Move cursor back up to overwrite the raw content
    for _ in range(line_count):
        print("\033[1A", end="", flush=True)  # Move up one line
        print("\033[2K", end="", flush=True)  # Clear the entire line
    
    # Print the formatted content
    print(formatted_message, end="", flush=True)
    
    return collected_content


# Example usage
if __name__ == "__main__":
    # Sample messages
    messages = [
        {
            "role": ROLE_USER,
            "content": "# Question about HTTP Libraries\n\nCan you explain how to use Python's `requests` library? I've heard it's good for API calls."
        },
        {
            "role": ROLE_ASSISTANT,
            "content": "# Python Requests Library\n\nThe `requests` library is one of the most popular HTTP libraries for Python.\n\n"
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
        }
    ]
    
    # Print the formatted conversation
    print(format_conversation(messages))