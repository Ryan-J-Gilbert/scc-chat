"""
FastAPI server for the HPC RAG Chatbot
"""

import os
import json
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from openai import OpenAI
import tiktoken
import uuid

from database import get_collection
from config import ENDPOINT, MODEL_NAME, TEMPERATURE, TOP_P, MAX_TOKENS
from tools import retrieve_documents, RETRIEVAL_TOOL_DEFINITION
from jwt_utils import create_token, decode_token
from event_logger import get_logger


# Initialize FastAPI app, db logger, document collection, token encoder, OpenAI client
app = FastAPI(title="SCC RAG Chatbot API")
logger = get_logger("chatbot_logs.db")
collection = get_collection()
encoding = tiktoken.encoding_for_model("gpt-4o")
client = OpenAI(
    base_url=ENDPOINT,
    api_key=os.environ.get("GITHUB_LLM_TOKEN"),
)

# TODO: ADD middleware, figure out SCC origins?
# Add CORS middleware to allow cross-origin requests
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Specify the allowed origins in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# Pydantic models for request/response
class ToolCall(BaseModel):
    id: str
    type: str
    function: Dict[str, Any]


class Message(BaseModel):
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None


class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]  # Accept plain dictionaries for flexibility
    stream: bool = False
    token: str


class ChatResponse(BaseModel):
    response: str


class SessionRequest(BaseModel):
    username: str


def process_stream(stream, chat_uuid):
    """Convert OpenAI stream to a format suitable for SSE"""
    complete_response = ""

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            content_chunk = chunk.choices[0].delta.content
            complete_response += content_chunk
            yield f"data: {json.dumps({'content': content_chunk})}\n\n"

    # Log the complete message after streaming is done
    token_count = len(encoding.encode(complete_response))
    logger.log_agent_response(chat_uuid, complete_response, token_count)

    yield "data: [DONE]\n\n"


def manage_context_window(messages, max_tokens=7000, model="gpt-4o"):
    """Estimate token count using tiktoken and trim messages if needed"""

    # Count tokens for each message and store with the message
    messages_with_tokens = []
    total_tokens = 0

    for m in messages:
        tokens = 0
        # Count tokens in content if present
        if m.get("content"):
            tokens += len(encoding.encode(m["content"]))

        # Count tokens in tool_calls if present
        if m.get("tool_calls"):
            tokens += len(encoding.encode(str(m["tool_calls"])))

        total_tokens += tokens
        messages_with_tokens.append((m, tokens))

    # If approaching limit, keep system prompt and drop older messages as needed
    if total_tokens > max_tokens:
        # Always keep system prompt
        system_prompt = next((m for m in messages if m["role"] == "system"), None)
        system_tokens = 0
        if system_prompt:
            # Find token count for system prompt
            for m, tokens in messages_with_tokens:
                if m["role"] == "system":
                    system_tokens = tokens
                    break

        # Start with system prompt if it exists
        kept_messages = [system_prompt] if system_prompt else []
        current_tokens = system_tokens

        # Add messages from newest to oldest until we approach the limit
        for m, tokens in reversed(messages_with_tokens):
            # Skip system message as we've already added it
            if m.get("role") == "system":
                continue

            # Check if adding this message would exceed our limit
            if current_tokens + tokens <= max_tokens:
                kept_messages.insert(1 if system_prompt else 0, m)
                current_tokens += tokens
            else:
                # Stop adding messages when we'd exceed the limit
                break

        return kept_messages

    return messages


# API endpoints
@app.post("/start_session")
def start_session(req: SessionRequest):
    """Returns a JWT given a usename and (generated) uuid"""

    username = req.username
    chat_id = str(uuid.uuid4())
    token = create_token(chat_id=chat_id, username=username)
    logger.log_event(chat_id, logger.USER_MESSAGE, {"event": "session_start"}, username)

    return {"token": token}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """/chat endpoint for client communication. Handles main logic of the program"""
    try:
        # verify token
        # TODO: better handling of potential jwt errors
        jwt = decode_token(request.token)

        logger.log_user_message(
            jwt["chat_id"],
            request.messages[-1].get("content", ""),
            jwt["username"],
            len(encoding.encode(request.messages[-1].get("content", ""))),
        )

        # Manage context window size
        messages_dict = manage_context_window(request.messages)

        # Check if system message exists - add logging in production
        system_message_exists = any(
            msg.get("role") == "system" for msg in messages_dict
        )
        if not system_message_exists:
            raise HTTPException(
                status_code=500, detail=f"WARNING: No system message found in request"
            )

        # First pass - determine if retrieval is needed
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages_dict,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_tokens=MAX_TOKENS,
            stream=False,
            tools=[RETRIEVAL_TOOL_DEFINITION],
        )

        assistant_message = response.choices[0].message

        # Check if the model wants to use tools
        if assistant_message.tool_calls:
            tool_call = assistant_message.tool_calls[0]
            tool_args = json.loads(tool_call.function.arguments)
            query = tool_args.get("query")
            # Get documents using hybrid retrieval
            retrieved_docs = retrieve_documents(collection, query)
            logger.log_tool_call(
                jwt["chat_id"],
                {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                },
            )
            reduced_docs = dict()
            for doc_type in retrieved_docs:
                values = [i["source"] for i in retrieved_docs[doc_type]]
                reduced_docs[doc_type] = values
            logger.log_retrieval(jwt["chat_id"], query, reduced_docs)
            # Add the assistant's tool call message to history
            messages_dict.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                    ],
                }
            )

            # Add tool response to messages
            messages_dict.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(retrieved_docs),
                }
            )

            # Manage context window again after adding tool responses
            messages_dict = manage_context_window(messages_dict)
            # Second pass - generate final response with retrieved documents
            if request.stream:
                # For streaming response, create a streaming response
                stream = client.chat.completions.create(
                    model=MODEL_NAME,
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    max_tokens=MAX_TOKENS,
                    messages=messages_dict,
                    stream=True,
                )

                # message logged in generator wrapper!

                return StreamingResponse(
                    process_stream(stream, jwt["chat_id"]),
                    media_type="text/event-stream",
                )
            else:
                final_response = client.chat.completions.create(
                    model=MODEL_NAME,
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    max_tokens=MAX_TOKENS,
                    messages=messages_dict,
                    stream=False,
                )
                content = final_response.choices[0].message.content

                token_count = len(encoding.encode(content))
                logger.log_agent_response(jwt["chat_id"], content, token_count)

                return {"response": content}

        else:
            # No need for tools, use direct response
            if request.stream:
                # For streaming response, create a streaming response
                stream = client.chat.completions.create(
                    model=MODEL_NAME,
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    max_tokens=MAX_TOKENS,
                    messages=messages_dict,
                    stream=True,
                )

                # message logged in generator wrapper!

                return StreamingResponse(
                    process_stream(stream, jwt["chat_id"]),
                    media_type="text/event-stream",
                )
            else:
                final_response = client.chat.completions.create(
                    model=MODEL_NAME,
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    max_tokens=MAX_TOKENS,
                    messages=messages_dict,
                    stream=False,
                )
                content = final_response.choices[0].message.content

                token_count = len(encoding.encode(content))
                logger.log_agent_response(jwt["chat_id"], content, token_count)

                return {"response": content}

    except Exception as e:
        logger.log_error(jwt["chat_id"], str(e))
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}"
        )


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Main entry point
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
