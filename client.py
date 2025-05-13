"""
Command-line client for the HPC RAG Chatbot - Manages message history client-side
"""
import os
import sys
import json
import requests
from typing import List, Dict, Any
import argparse
import tiktoken
import time


# Import chat formatting functions from your existing code
from chatformatting import print_streaming_response, format_message, ROLE_ASSISTANT
from config import SYSTEM_PROMPT  # Import system prompt from your config

# Server configuration
DEFAULT_SERVER_URL = "http://localhost:8000"
SERVER_URL = os.environ.get("CHATBOT_SERVER_URL", DEFAULT_SERVER_URL)

class ChatbotClient:
    def __init__(self, server_url: str, debug: bool = False, stream: bool = False, enable_logging: bool = True):
        self.server_url = server_url
        self.debug = debug
        self.stream = stream
        self.enable_logging = enable_logging
        self.headers = {
            "Content-Type": "application/json"
        }
        self.messages = []
        # Add system prompt message
        self.messages.append({
            "role": "system", 
            "content": SYSTEM_PROMPT
        })
        self.JWT = None
    
    def log(self, message: str):
        """Log messages if logging is enabled"""
        if self.enable_logging:
            print(f"[LOG] {message}")
    
    def debug_print(self, message: str):
        """Print debug messages if debug is enabled"""
        if self.debug:
            print(f"[DEBUG] {message}")

    def check_server_health(self) -> bool:
        """Check if the server is healthy before attempting to use it"""
        try:
            response = requests.get(f"{self.server_url}/health")
            if response.status_code == 200:
                self.log("Server health check passed")
                return True
            else:
                print(f"Server health check failed with status code {response.status_code}")
                return False
        except Exception as e:
            print(f"Error connecting to server: {e}")
            return False

    def start_session_server(self):
        """Send message to server to start session and receive JWT token"""
        try:
            username = os.getlogin()
            response = requests.post(f"{self.server_url}/start_session", json={ "username":username})
            if response.status_code == 200:
                self.JWT = response.json()['token']
            else:
                raise ValueError(f"Error connecting to server: {response.status_code}")
        except Exception as e:
            raise ValueError(f"Error connecting to server: {e}")

    def send_message(self, user_message: str, stream: bool = False) -> str:
        """Send a message to the chatbot server"""
        # Add user message to history
        self.messages.append({"role": "user", "content": user_message})
        
        # Context window is managed on the server side now
        
        # Prepare request
        request_data = {
            "messages": self.messages,
            "stream": stream,
            "token": self.JWT
        }
        
        self.debug_print(f"Sending request to {self.server_url}/chat")
        
        try:
            # Send request to server
            if stream:
                # Handle streaming response
                with requests.post(
                    f"{self.server_url}/chat",
                    headers=self.headers,
                    json=request_data,
                    stream=True
                ) as response:
                    
                    if response.status_code != 200:
                        print(f"Error: Server returned status code {response.status_code}")
                        print(response.text)
                        return ""
                    
                    # Process streaming response
                    assistant_message = ""
                    # Create a generator that yields each chunk in the format expected by print_streaming_response
                    def chunk_generator():
                        for line in response.iter_lines():
                            if line:
                                # Remove "data: " prefix and parse JSON
                                line_text = line.decode('utf-8')
                                if line_text.startswith("data: "):
                                    data = line_text[6:]
                                    if data == "[DONE]":
                                        return
                                    try:
                                        chunk = json.loads(data)
                                        if "content" in chunk and chunk["content"]:
                                            # Create an object with a structure similar to what print_streaming_response expects
                                            class ResponseChunk:
                                                def __init__(self, content):
                                                    self.choices = [type('obj', (object,), {
                                                        'delta': type('obj', (object,), {'content': content})
                                                    })]
                                            
                                            yield ResponseChunk(chunk["content"])
                                            # Also track the full message
                                            nonlocal assistant_message
                                            assistant_message += chunk["content"]
                                    except json.JSONDecodeError:
                                        self.debug_print(f"Failed to decode JSON: {data}")
                    
                    # Stream the response
                    print_streaming_response(chunk_generator())
                    
                    # Add assistant's response to message history
                    self.messages.append({"role": "assistant", "content": assistant_message})
                    return assistant_message
            else:
                # Handle regular response
                response = requests.post(
                    f"{self.server_url}/chat",
                    headers=self.headers,
                    json=request_data
                )
                
                if response.status_code != 200:
                    print(f"Error: Server returned status code {response.status_code}")
                    print(response.text)
                    return ""
                
                chat_response = response.json()
                assistant_message = chat_response["response"]
                
                # Add assistant's response to message history
                self.messages.append({"role": "assistant", "content": assistant_message})
                
                return assistant_message
                
        except Exception as e:
            print(f"Error communicating with server: {e}")
            return ""
    
    def run_chat_loop(self):
        """Run interactive chat loop"""
        print(format_message("Hello! I can help you with questions about the university's Shared Computing Cluster. You can ask specific questions like, \"How to run my Python script with 16 cores?\", but please do not include any sensitive data in your message! What would you like to know?", 
                           ROLE_ASSISTANT, 
                           terminal_width=os.get_terminal_size().columns))
        
        # Add initial greeting to message history
        self.messages.append({
            "role": "assistant", 
            "content": "Hello! I can help you with questions about the university's Shared Computing Cluster. You can ask specific questions like, \"How to run my Python script with 16 cores?\", but please do not include any sensitive data in your message! What would you like to know?"
        })
        
        while True:
            try:
                user_input = input("\nYou: ")
                print()
                if user_input.lower() in ['exit', 'quit']:
                    print("Goodbye!")
                    break
                
                # Send to server and get response
                start_time = time.time()
                self.debug_print("Sending message to server...")
                
                assistant_response = self.send_message(user_input, stream=self.stream)
                
                end_time = time.time()
                self.debug_print(f"Response received in {end_time - start_time:.2f} seconds")
                
                # Print formatted response
                if not assistant_response:
                    print("Error: No response received from server.")
                    continue
                
                if not self.stream:
                    print(format_message(assistant_response, ROLE_ASSISTANT, 
                                        terminal_width=os.get_terminal_size().columns))
                
            except KeyboardInterrupt:
                print("\nExiting!")
                sys.exit(0)
            except Exception as e:
                print(f"\nError: {e}")

def parse_args():
    parser = argparse.ArgumentParser(description="SCC RAG Chatbot Client")
    parser.add_argument("--server", default=SERVER_URL, help="Server URL")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--no-log", action="store_true", help="Disable logging (WIP)")
    parser.add_argument("--nostream", action="store_true", help="Disable streaming responses")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    client = ChatbotClient(
        server_url=args.server,
        debug=args.debug,
        stream=not args.nostream,
        enable_logging=not args.no_log
    )
    
    # Check server health before starting
    if client.check_server_health():
        client.start_session_server()
        client.run_chat_loop()
        
    else:
        print(f"Could not connect to server at {args.server}. Please check if the server is running.")
        sys.exit(1)