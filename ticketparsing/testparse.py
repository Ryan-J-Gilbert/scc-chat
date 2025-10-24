from pydantic import BaseModel, Field
from typing import Optional, Literal, List
import ollama
import pandas as pd
import time
import json
import asyncio



class TicketExtraction(BaseModel):
    skip: bool = Field(..., description="True if ticket should be skipped (spam/admin/incomplete), otherwise False")
    category: Optional[str] = Field(None, description="Broad category of the technical issue, highlighting a specific SCC component if available or None if skipping")
    technical_summary: Optional[str] = Field(None, description="Anonymized technical summary or None if skipping")
    resolution_steps: Optional[List[str]] = Field(None, description="Resolution steps or None if skipping")



def classify_ticket(ticket: dict) -> TicketExtraction:    
    # Combine description and comments for comprehensive analysis
    full_text = f"""Short Description:
{ticket.get('short_description'),""}

Description:
{ticket.get('description', '')}

Comments:
{ticket.get('comments', '')}"""
    
    # Detailed prompt for classification
    prompt = f"""
You are an expert IT support analyst working with university shared computing cluster (SCC) support tickets.

You will analyze the following ticket text to provide a concise structured summary as a JSON object, with relevant steps the user can take to resolve their problem.

For this ticket, do the following:

- If the ticket contains a meaningful technical issue with actionable resolution or insights, provide:
  1. A broad category of the technical issue. If possible, specify the SCC component involved.
  2. A technical summary of the issue, anonymized to remove any personally identifiable information (names, emails, IP addresses).
  3. Resolution steps or guidance taken to address the issue, highlighting any relevant specifics.

- If the ticket is spam, purely administrative, or very incomplete such that meaningful information cannot be extracted, respond with the skip set to true.

**Guidelines:**

- Remove ALL personally identifiable information.
- Remove any specific links
- Avoid using specific queue names that might belong to a user
- Use general file paths, and avoid using specific file paths that might belong to a user
- Provide actionable insights on technical content that can assist a user with a similar issue.
- Always respond with JSON matching the requested schema exactly.

Ticket Info:
---------
{full_text}
---------


You must ONLY respond with this response format (JSON):
{{
  "skip": true | false,
  "category": "string or null",
  "technical_summary": "string or null",
  "resolution_steps": ["string", "..."] or null
}}
"""

    try:
        # Use Ollama to classify the ticket

        # response = ollama.chat(
        #     model='qwen3:14b',
        #     messages=[{'role': 'user', 'content': prompt}],
        #     options={"temperature": 0.0},
        #     # format=TicketExtraction.model_json_schema(),
        #     think=True
        # )
        # response = ollama.chat(
        #     model='qwen3',
        #     messages=[{'role': 'user', 'content': prompt}],
        #     options={"temperature": 0.0},
        #     format=TicketExtraction.model_json_schema(),
        #     think=False
        # )
        response = ollama.chat(
            model='qwen3:14b',
            messages=[{'role': 'user', 'content': prompt}],
            options={"temperature": 0.0},
            format=TicketExtraction.model_json_schema(),
            think=False
        )
        
        # Parse the JSON response
        response = TicketExtraction.model_validate_json(response['message']['content'])
        return response

    except Exception as e:
        print(f"Error classifying ticket {ticket.get('number', 'Unknown')}: {e}")
        

async def async_classify_ticket(client, ticket: dict, sem) -> TicketExtraction:    
    # Combine description and comments for comprehensive analysis
    full_text = f"""Short Description:
{ticket.get('short_description'),""}

Description:
{ticket.get('description', '')}

Comments:
{ticket.get('comments', '')}"""
    
    # Detailed prompt for classification
    prompt = f"""
You are an expert IT support analyst working with university shared computing cluster (SCC) support tickets.

You will analyze the following ticket text to provide a concise structured summary as a JSON object, with relevant steps the user can take to resolve their problem.

For this ticket, do the following:

- If the ticket contains a meaningful technical issue with actionable resolution or insights, provide:
  1. A broad category of the technical issue. If possible, specify the SCC component involved.
  2. A technical summary of the issue, anonymized to remove any personally identifiable information (names, emails, IP addresses).
  3. Resolution steps or guidance taken to address the issue, highlighting any relevant specifics.

- If the ticket is spam, purely administrative, or very incomplete such that meaningful information cannot be extracted, respond with the skip set to true.

**Guidelines:**

- Remove ALL personally identifiable information.
- Remove any specific links
- Avoid using specific queue names that might belong to a user
- Use general file paths, and avoid using specific file paths that might belong to a user
- Provide actionable insights on technical content that can assist a user with a similar issue.
- Always respond with JSON matching the requested schema exactly.

Ticket Info:
---------
{full_text}
---------


You must ONLY respond with this response format (JSON):
{{
  "skip": true | false,
  "category": "string or null",
  "technical_summary": "string or null",
  "resolution_steps": ["string", "..."] or null
}}
"""

    try:
        # Use Ollama to classify the ticket
        async with sem:
            start = time.time()
            response = await client.chat(
                model='qwen3:14b',
                messages=[{'role': 'user', 'content': prompt}],
                options={"temperature": 0.0},
                format=TicketExtraction.model_json_schema(),
                think=False
            )
            
            # Parse the JSON response
            response = TicketExtraction.model_validate_json(response['message']['content'])
            end = time.time()
            print(f"Started at: {start}, ended at: {end} | {(end-start):.2f} seconds")
            return response

    except Exception as e:
        print(f"Error classifying ticket {ticket.get('number', 'Unknown')}: {e}")
        

async def main(tickets):
    N = 4  # maximum concurrency
    sem = asyncio.Semaphore(N)
    client = ollama.AsyncClient()  # Re-use for efficiency

    tasks = [async_classify_ticket(client, msg, sem) for msg in tickets]
    results = await asyncio.gather(*tasks)
    print("All done:", results)




if __name__ == "__main__":
    import pandas as pd
    # from tqdm import tqdm

    file_name = "/projectnb/scv/akamble/ServiceNow/output_251010.json"

    with open(file_name, 'r') as file:
        data = json.load(file)

    # reconfigure some nested values
    # assigned_to value to just assigned_to.display_value
    # assignment_group to just assignment_group.display_value
    for i in data['result']:
        if i['assigned_to']:
            i['assigned_to'] = i['assigned_to']['display_value']
        else:
            i['assigned_to'] = ''

        if i['assignment_group']:
            i['assignment_group'] = i['assignment_group']['display_value']
        else:
            i['assignment_group'] = ''

    df = pd.DataFrame(data['result'])
    # tickets = df.head(20).to_dict(orient='records')
    tickets = df.head.to_dict(orient='records')

    asyncio.run(main(tickets))