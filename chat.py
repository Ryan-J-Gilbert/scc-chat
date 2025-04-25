import os
from sys import exit
import json
from openai import OpenAI

from database import get_collection
from chatformatting import print_streaming_response, format_message, ROLE_ASSISTANT
from config import SYSTEM_PROMPT, ENDPOINT, MODEL_NAME, TEMPERATURE, TOP_P, MAX_TOKENS
from tools import retrieve_documents, RETRIEVAL_TOOL_DEFINITION

token = os.environ["GITHUB_LLM_TOKEN"]

collection = get_collection()

# Initialize OpenAI client
client = OpenAI(
    base_url=ENDPOINT,
    api_key=token,
)
print(f"Initialized client with model: {MODEL_NAME}")


def manage_context_window(messages, max_tokens=7000):
    # print(messages)
    """Estimate token count and trim messages if needed"""
    # Simple estimation: ~2.5 tokens per word
    total_tokens = sum(len(m["content"].split()) * 2.5 for m in messages if m.get("content"))
    total_tokens += sum(len(str(m["tool_calls"]).split()) * 2.5 for m in messages if m.get("tool_calls"))
    print("ESTIMATED TOKENS:", total_tokens)
    # If approaching limit, keep system prompt and most recent messages
    if total_tokens > max_tokens:
        # Always keep system prompt
        system_prompt = next((m for m in messages if m["role"] == "system"), None)
        # Keep only recent messages
        recent_messages = messages[-5:]  # Adjust number as needed
        messages = [system_prompt] + recent_messages if system_prompt else recent_messages
        print("[System: Context window limit approached. Some conversation history was summarized.]")
    
    return messages

def scc_chatbot():
    """Main chatbot loop using OpenAI API with streaming"""
        
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # print("SCC Assistant: Hello! I can help you with questions about the university's Shared Computing Cluster. What would you like to know?")
    print(format_message("Hello! I can help you with questions about the university's Shared Computing Cluster. You can ask specific questions like, \"How to run my Python script with 16 cores?\", but please do not include any sensitive data in your message! What would you like to know?", ROLE_ASSISTANT, terminal_width=os.get_terminal_size().columns))

    while True:
        try:
            user_input = input("\nYou: ")
        except KeyboardInterrupt:
            print("\nExiting!")
            exit(0)
        if user_input.lower() in ['exit', 'quit']:
            break

        # if user_input.lower() in ['/help']:
        #     print('Current tool capabilities:')

        
        # Add user message to history
        messages.append({"role": "user", "content": user_input})
        
        try:
            # First pass - decide if retrieval is needed
            messages = manage_context_window(messages)
            response = client.chat.completions.create(
                model=MODEL_NAME, # Using your specified model
                messages=messages,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                max_tokens=MAX_TOKENS,
                stream=False,
                tools=[RETRIEVAL_TOOL_DEFINITION]
            )
            # print(response)
            
            assistant_message = response.choices[0].message
            
            # Check if the model wants to use tools
            if assistant_message.tool_calls:
                tool_call = assistant_message.tool_calls[0]
                tool_args = json.loads(tool_call.function.arguments)
                query = tool_args.get("query")
                
                print(f"\n[System: Retrieving SCC documentation for: {query}]")
                
                # Get documents using hybrid retrieval
                retrieved_docs = retrieve_documents(collection,query)
                
                # Display retrieved documents for debugging
                print(f"Retrieved {len(retrieved_docs['qa_documents'])} Q&A documents and {len(retrieved_docs['article_documents'])} articles")
                print(f"JSON object has length {len(json.dumps(retrieved_docs))}")
                # print(retrieved_docs)
                # Add the assistant's tool call message to history
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                    ]
                })
                
                # Add tool response to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(retrieved_docs)
                })
                
                # Second pass - generate final response with retrieved documents using streaming
                # print("\nSCC Assistant: ", end="", flush=True)
                response_stream = client.chat.completions.create(
                    model=MODEL_NAME,
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    max_tokens=MAX_TOKENS,
                    messages=messages,
                    stream=True
                )
                
                # Process and display streaming response
                terminal_width = os.get_terminal_size().columns
                final_content = print_streaming_response(response_stream, terminal_width=terminal_width)
                messages.append({"role": "assistant", "content": final_content})
                
            else:
                # No need for tools, use direct response with streaming
                print("\nSCC Assistant: ", end="", flush=True)
                response_stream = client.chat.completions.create(
                    model=MODEL_NAME,
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    max_tokens=MAX_TOKENS,
                    messages=messages,
                    stream=True
                )
                
                # Process and display streaming response
                content = print_streaming_response(response_stream)
                messages.append({"role": "assistant", "content": content})
                
        except Exception as e:
            print(f"\nError: {e}")
            continue

if __name__ == "__main__":
    scc_chatbot()