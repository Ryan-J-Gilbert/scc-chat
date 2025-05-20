import os
from sys import exit
import json
from openai import OpenAI
import tiktoken

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

print(
    f"""Config:
Endpoint: {ENDPOINT}
Model: {MODEL_NAME}
Temperature: {TEMPERATURE}
Top P: {TOP_P}
Max tokens: {MAX_TOKENS}
System prompt:
{SYSTEM_PROMPT}
"""
)

with open("evaluation.json") as file:
    data = json.load(file)

print(
    f"Loaded evaluation.json, version {data['version']}, with {len(data['prompts'])} prompts to evaluate"
)

for prompt in data["prompts"]:
    print("Evaluating:", prompt["question"])
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt["question"]},
    ]
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
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

        # Display retrieved documents for debugging
        # print(f"Retrieved {len(retrieved_docs['qa_documents'])} Q&A documents and {len(retrieved_docs['article_documents'])} articles")
        # print(f"JSON object has length {len(json.dumps(retrieved_docs))}")
        # print(retrieved_docs)
        # Add the assistant's tool call message to history
        messages.append(
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
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(retrieved_docs),
            }
        )

        # Second pass - generate final response with retrieved documents using streaming
        response = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_tokens=MAX_TOKENS,
            messages=messages,
            stream=False,
        )

        result = response.choices[0].message.content

    else:
        result = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_tokens=MAX_TOKENS,
            messages=messages,
            stream=False,
        )

        result = response.choices[0].message.content

    print("\n\n\n")
    print(
        f"Needed query? {prompt['should_query']} | Queried? {not not assistant_message.tool_calls}"
    )
    print(
        f"Good keywords: {prompt['good_keywords']} | Contained: {[keyword for keyword in prompt['good_keywords'] if keyword in result]}"
    )
    print(
        f"Bad keywords: {prompt['bad_keywords']} | Contained: {[keyword for keyword in prompt['bad_keywords'] if keyword in result]}"
    )
    print("\n\n\n")
