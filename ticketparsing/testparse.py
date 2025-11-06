from pydantic import BaseModel, Field
from typing import Optional, List
import ollama
import pandas as pd
import time
import json
import asyncio
from tqdm.asyncio import tqdm_asyncio
from tqdm import tqdm


class TicketExtraction(BaseModel):
    skip: bool = Field(..., description="True if ticket should be skipped (spam/admin/incomplete), otherwise False")
    category: Optional[str] = Field(None, description="Broad category of the technical issue, highlighting a specific SCC component if available or None if skipping")
    technical_summary: Optional[str] = Field(None, description="Anonymized technical summary or None if skipping")
    resolution_steps: Optional[List[str]] = Field(None, description="Resolution steps or None if skipping")


def load_processed_tickets(output_path):
    """Load already processed ticket numbers from the output file."""
    processed = set()
    if os.path.exists(output_path):
        try:
            with open(output_path, "r") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        ticket_num = data.get("ticket_number")
                        if ticket_num:
                            processed.add(ticket_num)
        except Exception as e:
            print(f"Warning: Error loading processed tickets: {e}")
    return processed


async def async_classify_ticket(client, ticket: dict, sem) -> dict:
    full_text = f"""Short Description:
{ticket.get('short_description', '')}

Description:
{ticket.get('description', '')}

Comments:
{ticket.get('comments', '')}"""

    prompt = f"""
You are an expert IT support analyst for university SCC support tickets.

Your task: Analyze the ticket text below and respond ONLY with a structured JSON object:
- If the ticket contains an actionable technical issue, summarize it for a technical audience.
- If it is spam, purely administrative, or missing technical info, set "skip" to true.

**Guidelines:**
- Remove ALL personally identifiable information (PII): names, emails, user IDs, phone numbers, links, file paths, etc.
- Respond only with a JSON object matching the schema below. Never add commentary.

Ticket Info:
---------
{full_text}
---------

**Response format schema:**
{{
  "skip": true | false,
  "category": "string or null",
  "technical_summary": "string or null",
  "resolution_steps": ["string", "..."] or null
}}

**Examples**

Example 1 – Actionable technical ticket with full support conversation  
Original Ticket:  
Short Description: Can't access folder /home/jdoe/myproject  
Description: When I try to cd into my folder, I get "Permission denied".  
Comments: Help! I'm jdoe, using node scc-n27.

Support Conversation:
Analyst: Hello, I've reviewed your ticket about access issues to your project folder.  
User: Yes, when I try to access /home/jdoe/myproject from the terminal, I get "Permission denied".  
Analyst: Understood. First, let's check if your account is part of the correct group for that folder.  
User: How do I check that?  
Analyst: You can run `groups` in the terminal to see your group memberships, and `ls -ld /home/[redacted]/myproject` to check permissions.  
User: The group is correct, but permissions seem restricted.  
Analyst: It may be an ownership issue. If this is a shared folder, you might need to contact the folder owner or support to request access.  
User: Okay, thanks!

Ideal JSON:
{{
  "skip": false,
  "category": "File System Permissions",
  "technical_summary": "User unable to access project folder due to permission denial.",
  "resolution_steps": [
    "Verify group membership and folder access rights for the affected directory.",
    "Check ownership and permissions using file system commands.",
    "If folder ownership is incorrect, coordinate with support or the owner to adjust permissions."
  ]
}}

Example 2 – Administrative/Spam/Incomplete with conversation  
Original Ticket:  
Short Description: Invoice request  
Description: Hello, an invoice has been sent! Please click the paypal link to continue.  
Comments: [None]


Ideal JSON:
{{
  "skip": true,
  "category": null,
  "technical_summary": null,
  "resolution_steps": null
}}

Example 3 – Technical issue, removes PII, shows full troubleshooting steps  
Original Ticket:  
Short Description: My script crashes  
Description: I'm running my script at /home/jane/doe/myscript.sh on node scc-node12 and it fails with exit code 1. My email is jane@univ.edu  
Comments: I also see "module not found" in the error logs.

Support Conversation:
Analyst: I see your script is failing with exit code 1. The log indicates a "module not found" error.  
User: Yes, it works on my laptop but fails on SCC.  
Analyst: SCC nodes may not have all modules installed by default. You should try loading the correct software module using the `module load` command, or check the documentation for required dependencies.  
User: How do I know which module to load?  
Analyst: Look at the error output, which should mention the missing module. Then, try `module avail` to see what's available and `module load <module_name>` to add it.  
User: That solved it, thank you!

Ideal JSON:
{{
  "skip": false,
  "category": "Job Submission / Software Modules",
  "technical_summary": "User's script fails due to missing software module.",
  "resolution_steps": [
    "Review error logs for missing module or dependency details.",
    "Use module management commands to load required modules before running the script.",
    "Consult SCC software documentation for instructions on available environments."
  ]
}}

**When to 'skip':**
- The ticket is spam or irrelevant.
- It has only administrative requests (account unlocks, password resets, etc).
- The ticket is incomplete or missing technical details.

**Output ONLY valid JSON as in examples above. Do NOT include extra text.**
"""
    try:
        async with sem:
            start = time.time()
            # response = await client.chat(
            #     model='qwen3:14b',
            #     messages=[{'role': 'user', 'content': prompt}],
            #     options={"temperature": 0.0},
            #     format=TicketExtraction.model_json_schema(),
            #     think=False
            # )
            # response = await client.chat(
            #     model='llama3.2',
            #     messages=[{'role': 'user', 'content': prompt}],
            #     options={"temperature": 0.0},
            #     format=TicketExtraction.model_json_schema(),
            # )

            response = await client.chat(
                model='qwen3:30b',
                messages=[{'role': 'user', 'content': prompt}],
                options={"temperature": 0.0},
                format=TicketExtraction.model_json_schema(),
                think=False
            )
            parsed = TicketExtraction.model_validate_json(response['message']['content'])
            end = time.time()
            return {
                "ticket_number": ticket.get("number", ""),
                "result": parsed.model_dump(),
                "elapsed": round(end - start, 2)
            }
    except Exception as e:
        return {
            "ticket_number": ticket.get("number", ""),
            "error": str(e)
        }


async def process_batch(batch_tickets, output_path, sem, progress_bar):
    """Process a batch of tickets and append results to file after each batch."""
    client = ollama.AsyncClient()
    tasks = [async_classify_ticket(client, t, sem) for t in batch_tickets]
    results = []
    for coro in tqdm_asyncio.as_completed(tasks):
        res = await coro
        results.append(res)
        progress_bar.update(1)

    # Append to output file
    with open(output_path, "a") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    return results


async def main(df, output_path, batch_size=10):
    """Process the dataframe in batches with tqdm progress bar."""
    N = 4  # max concurrency
    sem = asyncio.Semaphore(N)

    total = len(df)
    with tqdm(total=total, desc="Processing tickets", unit="ticket") as pbar:
        for start_idx in range(0, total, batch_size):
            end_idx = min(start_idx + batch_size, total)
            batch = df.iloc[start_idx:end_idx].to_dict(orient='records')
            await process_batch(batch, output_path, sem, pbar)


if __name__ == "__main__":
    import os

    file_name = "/projectnb/scv/akamble/ServiceNow/output_251010.json"
    output_file = "/projectnb/scc-chat/research/ticketparsing/classified_tickets.jsonl"

    accepted_file = "/projectnb/scc-chat/research/ticketparsing/accepted_tickets.txt"
    rejected_file = "/projectnb/scc-chat/research/ticketparsing/rejected_tickets.txt"

    # Load JSON data
    with open(file_name, 'r') as f:
        data = json.load(f)

    # Normalize nested fields
    for i in data['result']:
        i['assigned_to'] = i['assigned_to']['display_value'] if i.get('assigned_to') else ''
        i['assignment_group'] = i['assignment_group']['display_value'] if i.get('assignment_group') else ''

    df = pd.DataFrame(data['result'])
    print(f"Loaded {len(df)} tickets")
    
    remove_names = ["Aaron Fuegi", "Wayne Gilmore", "Laura Giannitrapani", "Charles Janke", "Jack Chan", "Manny Ruiz", "David Taylor", "Michael Dugan"]
    df = df[~df['assigned_to'].isin(remove_names)]
    print(f"Removed tickets assigned to {', '.join(remove_names[:3])}..., {len(df)} tickets remaining")

    # Load already processed tickets
    processed_tickets = load_processed_tickets(output_file)
    print(f"Found {len(processed_tickets)} already processed tickets")
    
    # Filter out already processed tickets
    df = df[~df['number'].isin(processed_tickets)]
    print(f"Skipping already processed tickets, {len(df)} tickets remaining to process")

    if len(df) == 0:
        print("No new tickets to process!")
    else:
        # Ensure output file exists
        if not os.path.exists(output_file):
            open(output_file, "w").close()

        asyncio.run(main(df, output_file, batch_size=20))
        print(f"Processing complete! Results appended to {output_file}")