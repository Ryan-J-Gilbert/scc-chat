from pydantic import BaseModel, Field
from typing import Optional, List
import ollama
import pandas as pd
import time
import json
import asyncio
from tqdm.asyncio import tqdm_asyncio
from tqdm import tqdm


class QuestionAnswerPair(BaseModel):
    question: str = Field(..., description="A natural question a user might ask")
    answer: str = Field(..., description="Clear, actionable answer to the question")
    category: str = Field(..., description="Technical category for this Q&A pair")


class TicketExtraction(BaseModel):
    thinking: str = Field(..., description="Internal reasoning about what valuable Q&A pairs can be extracted from this ticket")
    skip: bool = Field(..., description="True if ticket should be skipped (spam/admin/incomplete), otherwise False")
    qa_pairs: Optional[List[QuestionAnswerPair]] = Field(None, description="List of question-answer pairs extracted from the ticket, or None if skipping")


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
You are an expert IT support analyst extracting knowledge from university SCC (Shared Computing Cluster) support tickets.

Your task: Analyze support tickets and extract multiple question-answer (Q&A) pairs that will help END USERS through a self-service knowledge base.

**Critical Context:**
- These Q&A pairs will be used in a RAG system where users ask natural language questions
- Extract MULTIPLE Q&A pairs from each ticket - think about different ways users might ask about the same information
- Include Q&A pairs about: technical solutions, system limitations, policies, workarounds, and clarifications
- Questions should be natural and varied - the way real users would ask them
- Answers should be clear, specific, and actionable
- Each Q&A pair should stand alone and be independently useful

**PII Removal Requirements:**
Remove ALL personally identifiable information from Q&A pairs:
- Usernames, user IDs, email addresses
- Specific file paths (replace with generic patterns like `/home/[user]/project`)
- Node names (replace with generic `scc-node-XX` or just "compute node")
- Queue/partition names (replace with generic descriptions like "GPU partition" or "standard partition")
- Phone numbers, employee IDs, ticket numbers
- Any other identifying information

**When to Skip (set skip=true):**
- Spam, phishing, or irrelevant content
- Purely administrative requests with no technical context or learning value
- Incomplete tickets with insufficient information to extract meaningful Q&A pairs
- Pure social/pleasantries with no technical content

**When NOT to Skip:**
- Any ticket with technical information, even if just clarifications or policies
- Tickets about system limitations or what's not allowed
- Requests that were denied with technical reasoning
- Any information that would help users understand the system better

**Response format schema:**
{{
  "thinking": "Brief analysis of what valuable Q&A pairs can be extracted, considering different ways users might ask about this information",
  "skip": true | false,
  "qa_pairs": [
    {{
      "question": "string",
      "answer": "string",
      "category": "string"
    }},
    ...
  ] or null
}}

**Examples**

Example 1 – Containerization (Docker/Singularity)
Original Ticket:
Short Description: Can I use Docker containers?
Description: I have Docker containers for my workflows. How do I run them on SCC? User: researcher99
Comments:
Support: Docker is not supported on SCC due to security restrictions
User: What should I use instead?
Support: Use Singularity - it can run Docker containers and is fully supported
Support: You can convert Docker images: singularity pull docker://ubuntu:latest
User: Thanks, will try Singularity

Ideal JSON:
{{
  "thinking": "This ticket contains information about Docker support, Singularity as an alternative, and how to convert Docker images. Users might ask about Docker support in different ways, or ask what containerization options exist, or how to convert their existing Docker containers. Should extract multiple Q&A pairs covering these angles.",
  "skip": false,
  "qa_pairs": [
    {{
      "question": "Can I use Docker on SCC?",
      "answer": "No, Docker is not supported on SCC due to security restrictions. Use Singularity instead, which can run Docker containers.",
      "category": "Containerization"
    }},
    {{
      "question": "Is Docker supported on the cluster?",
      "answer": "Docker is not supported on SCC for security reasons. Singularity is the supported container runtime.",
      "category": "Containerization"
    }},
    {{
      "question": "What container system should I use on SCC?",
      "answer": "Use Singularity for containerization on SCC. It's fully supported and can run Docker containers.",
      "category": "Containerization"
    }},
    {{
      "question": "How do I run my Docker containers on SCC?",
      "answer": "Convert your Docker containers to Singularity format using: singularity pull docker://[image-name]. Singularity can directly run Docker images.",
      "category": "Containerization"
    }},
    {{
      "question": "Can Singularity run Docker images?",
      "answer": "Yes, Singularity can directly pull and run Docker images using the docker:// prefix. For example: singularity pull docker://ubuntu:latest",
      "category": "Containerization"
    }}
  ]
}}

Example 2 – Job time limit extension
Original Ticket:
Short Description: Can I extend my running job's time limit?
Description: My job will hit the 12 hour limit soon. Can you extend it to 24 hours? Job 12345
Comments:
Support: Unfortunately, we cannot extend time limits for running jobs. This is a scheduler limitation.
User: What should I do?
Support: You'll need to implement checkpointing in your code so you can resume from where it left off.
User: Ok, thanks

Ideal JSON:
{{
  "thinking": "Important information about a system limitation and the workaround. Users might ask if extensions are possible, why they can't extend, what to do instead, or about checkpointing. Multiple perspectives on the same core issue.",
  "skip": false,
  "qa_pairs": [
    {{
      "question": "Can I extend the time limit of a running job?",
      "answer": "No, time limits cannot be extended for jobs that are already running. This is a fundamental limitation of the batch scheduler.",
      "category": "Job Scheduling"
    }},
    {{
      "question": "My job is about to hit the time limit, what can I do?",
      "answer": "Unfortunately, running jobs cannot have their time limits modified. You'll need to let it finish or cancel it. For future jobs, implement checkpointing so you can resume progress.",
      "category": "Job Scheduling"
    }},
    {{
      "question": "What is checkpointing and why do I need it?",
      "answer": "Checkpointing means saving your application's progress at regular intervals. This allows you to resume from the last checkpoint if a job hits the time limit, rather than starting over.",
      "category": "Job Scheduling"
    }},
    {{
      "question": "How do I handle long-running jobs that exceed time limits?",
      "answer": "Implement checkpointing in your code to save progress periodically. When the job hits the time limit, resubmit it with the checkpoint file to resume where it left off.",
      "category": "Job Scheduling"
    }}
  ]
}}

Example 3 – GPU memory vs CPU memory
Original Ticket:
Short Description: Job killed with exit code 137
Description: PyTorch training job keeps getting killed. I requested 128GB memory.
Comments:
Support: Exit code 137 means out-of-memory. You're hitting GPU memory limits, not CPU memory.
User: What's the difference?
Support: The 128GB you requested is CPU RAM. GPUs have separate memory - typically 40GB per GPU. Your batch size is too large for GPU memory.
User: Reduced batch size, working now

Ideal JSON:
{{
  "thinking": "Explains a common misconception about GPU vs CPU memory, the exit code meaning, and the solution. Users might ask about exit code 137, GPU memory errors, the difference between memory types, or how to fix OOM issues.",
  "skip": false,
  "qa_pairs": [
    {{
      "question": "What does exit code 137 mean?",
      "answer": "Exit code 137 means your job was killed due to out-of-memory (OOM). The process exceeded available memory limits.",
      "category": "Job Failure"
    }},
    {{
      "question": "Why is my GPU job getting killed with OOM errors?",
      "answer": "GPU memory is separate from CPU memory. If you're running out of GPU memory, you need to reduce your batch size, enable mixed precision training, or use gradient accumulation.",
      "category": "GPU Computing"
    }},
    {{
      "question": "What's the difference between GPU memory and CPU memory?",
      "answer": "GPU memory and CPU memory are completely separate. When you request 128GB in a job, that's CPU RAM. GPUs have their own memory (typically 40GB per GPU) which is used for model parameters and batch data.",
      "category": "GPU Computing"
    }},
    {{
      "question": "How do I fix GPU out-of-memory errors?",
      "answer": "Reduce your batch size, enable mixed precision training (fp16/bf16), use gradient accumulation, or request multiple GPUs with model parallelism.",
      "category": "GPU Computing"
    }},
    {{
      "question": "My PyTorch job keeps crashing, why?",
      "answer": "If you see exit code 137, it's likely an out-of-memory error. Check if you're exceeding GPU memory limits by reducing batch size or enabling mixed precision training.",
      "category": "GPU Computing"
    }}
  ]
}}

Example 4 – Compute nodes and external network
Original Ticket:
Short Description: Can't connect to external database
Description: My script can't reach our lab database at external-db.example.com. Works from my laptop.
Comments:
User: Getting connection timeout
Support: Compute nodes don't have external network access for security reasons
Support: You need to download data on login nodes first, then process on compute nodes
User: That worked, thanks

Ideal JSON:
{{
  "thinking": "Important architectural limitation. Users might ask about external connectivity, why connections fail, network access, or how to download data. Should cover both the problem and the solution workflow.",
  "skip": false,
  "qa_pairs": [
    {{
      "question": "Can compute nodes access external websites or databases?",
      "answer": "No, compute nodes do not have external network access for security reasons. Only login nodes can connect to external resources.",
      "category": "Network"
    }},
    {{
      "question": "Why can't my job connect to external servers?",
      "answer": "Compute nodes have restricted external network access for security. You need to download data on login nodes first, then transfer it for processing on compute nodes.",
      "category": "Network"
    }},
    {{
      "question": "How do I download data from external sources for my jobs?",
      "answer": "Use login nodes to download data from external databases or websites. Save the data to your project directory, then submit compute jobs that read from those local files.",
      "category": "Network"
    }},
    {{
      "question": "Where should I run scripts that need internet access?",
      "answer": "Run scripts requiring external network access on login nodes. Compute nodes are isolated from external networks for security.",
      "category": "Network"
    }}
  ]
}}

Example 5 – Python dependency conflicts
Original Ticket:
Short Description: ImportError with markupsafe
Description: Flask app crashes: cannot import name 'soft_unicode' from 'markupsafe'. Works on my laptop.
Comments:
Support: This is a version compatibility issue - newer markupsafe doesn't work with older Flask
User: How do I fix it?
Support: Create a conda environment with compatible versions: conda create -n myenv python=3.9 && conda install flask=2.3
User: Working now

Ideal JSON:
{{
  "thinking": "Common dependency conflict issue. Users might ask about the specific error, why local vs cluster differs, how to fix dependency conflicts, or best practices for Python environments. Cover the error, cause, and solution approach.",
  "skip": false,
  "qa_pairs": [
    {{
      "question": "What does 'cannot import name soft_unicode from markupsafe' mean?",
      "answer": "This is a version compatibility error between markupsafe and Flask/Jinja2. Newer versions of markupsafe (≥2.1.0) removed 'soft_unicode', breaking compatibility with older Flask versions.",
      "category": "Python Dependencies"
    }},
    {{
      "question": "Why does my code work locally but fail on SCC with import errors?",
      "answer": "Local and cluster environments have different package versions installed. Create isolated conda or virtualenv environments to ensure consistent dependencies across systems.",
      "category": "Python Dependencies"
    }},
    {{
      "question": "How do I fix Python package version conflicts?",
      "answer": "Create an isolated environment: 'module load miniconda && conda create -n myenv python=3.9' then install compatible versions together: 'conda install flask=2.3'. This ensures all packages work together.",
      "category": "Python Dependencies"
    }},
    {{
      "question": "Should I use conda or pip on SCC?",
      "answer": "Use conda environments (or virtualenv) rather than installing directly to user site-packages. This prevents conflicts and ensures reproducibility: 'conda create -n myenv' then 'conda activate myenv'.",
      "category": "Python Dependencies"
    }}
  ]
}}

Example 6 – X11 forwarding for GUI
Original Ticket:
Short Description: Can't open MATLAB GUI
Description: Getting "cannot open display" error when launching MATLAB GUI
Comments:
User: The graphical interface won't launch
Support: You need X11 forwarding enabled. Did you connect with ssh -X?
User: No, just regular ssh
Support: Reconnect with ssh -X and try again
User: Works now!

Ideal JSON:
{{
  "thinking": "Common GUI application issue. Users might ask about the specific error, how to run GUIs, what X11 is, or how to fix display errors. Cover different phrasings of the same problem.",
  "skip": false,
  "qa_pairs": [
    {{
      "question": "How do I run GUI applications on SCC?",
      "answer": "Enable X11 forwarding when connecting: 'ssh -X username@scc-address'. This allows graphical applications to display on your local machine.",
      "category": "Remote Access"
    }},
    {{
      "question": "What does 'cannot open display' error mean?",
      "answer": "This error means X11 forwarding is not enabled. Reconnect to SCC using 'ssh -X' to enable graphical application support.",
      "category": "Remote Access"
    }},
    {{
      "question": "Why won't MATLAB GUI launch?",
      "answer": "GUI applications require X11 forwarding. Connect with 'ssh -X username@scc-address' instead of regular ssh. On Windows, install an X server like VcXsrv first. On Mac, install XQuartz.",
      "category": "Remote Access"
    }},
    {{
      "question": "What is X11 forwarding?",
      "answer": "X11 forwarding allows graphical applications running on remote systems to display on your local machine. Enable it with 'ssh -X' when connecting to SCC.",
      "category": "Remote Access"
    }}
  ]
}}

Example 7 – MPI with SLURM
Original Ticket:
Short Description: MPI job fails - not enough slots
Description: Getting "not enough slots available" when running mpirun -np 48. Job requests 2 nodes with 24 cores each.
Comments:
Support: Your mpirun command bypasses SLURM's resource management
User: How should I run it?
Support: Use srun instead of mpirun, or configure mpirun to use SLURM: mpirun -np $SLURM_NTASKS
User: Changed to srun, working now

Ideal JSON:
{{
  "thinking": "Important distinction between mpirun and srun in SLURM. Users might ask about the error, which command to use, difference between mpirun and srun, or how to run parallel jobs properly.",
  "skip": false,
  "qa_pairs": [
    {{
      "question": "Should I use mpirun or srun for parallel jobs?",
      "answer": "Use 'srun' for parallel jobs in SLURM environments. SLURM automatically handles process distribution with srun. If you must use mpirun, configure it to respect SLURM: 'mpirun -np $SLURM_NTASKS'.",
      "category": "Parallel Computing"
    }},
    {{
      "question": "What does 'not enough slots available' mean in MPI jobs?",
      "answer": "This error occurs when mpirun bypasses SLURM's resource allocation. Use 'srun ./my_program' instead of mpirun, or configure mpirun to use SLURM variables.",
      "category": "Parallel Computing"
    }},
    {{
      "question": "How do I run MPI programs on SCC?",
      "answer": "Use 'srun ./my_program' in your job script. SLURM automatically distributes processes based on your --nodes and --ntasks-per-node settings. Don't use mpirun directly unless configured for SLURM.",
      "category": "Parallel Computing"
    }},
    {{
      "question": "What's the difference between srun and mpirun?",
      "answer": "In SLURM environments, srun is aware of your resource allocation and distributes processes correctly. mpirun bypasses SLURM unless explicitly configured with SLURM environment variables.",
      "category": "Parallel Computing"
    }}
  ]
}}

Example 8 – Home directory disk quota
Original Ticket:
Short Description: Disk quota exceeded in home directory
Description: Can't save files - getting quota exceeded error. User abc123.
Comments:
User: Can I get more space?
Support: Home directory limit is 50GB and cannot be increased. Use project space for large files.
User: Where is project space?
Support: /projectnb/[project-name]/ - quotas there are set by your PI

Ideal JSON:
{{
  "thinking": "Storage quota policy information. Users might ask about quota limits, getting more space, differences between storage areas, or where to store data. Important to emphasize the non-negotiable limit.",
  "skip": false,
  "qa_pairs": [
    {{
      "question": "How much storage space do I have in my home directory?",
      "answer": "Home directories have a fixed 50GB quota that cannot be increased. This is a cluster-wide policy to ensure fair resource distribution.",
      "category": "Storage"
    }},
    {{
      "question": "Can I increase my home directory storage quota?",
      "answer": "No, home directory quotas are fixed at 50GB and cannot be increased. Move large files to project space at /projectnb/[project]/ which has larger quotas.",
      "category": "Storage"
    }},
    {{
      "question": "Where should I store large data files?",
      "answer": "Store large files in project space (/projectnb/[project]/) rather than home directory. Home directories are limited to 50GB, while project space has much larger quotas set by your PI.",
      "category": "Storage"
    }},
    {{
      "question": "What's the difference between home directory and project space?",
      "answer": "Home directory (/home/[user]/) has a fixed 50GB limit for personal files and configs. Project space (/projectnb/[project]/) has larger quotas for data and is shared among research group members.",
      "category": "Storage"
    }},
    {{
      "question": "How do I check my disk quota usage?",
      "answer": "Check home directory usage with 'quota -s' or 'du -sh ~'. For project space, use 'du -sh /projectnb/[project]/'. To find large files: 'du -h ~ --max-depth=1 | sort -hr | head -20'.",
      "category": "Storage"
    }}
  ]
}}

Example 9 – Administrative request (SKIP)
Original Ticket:
Short Description: Need password reset
Description: Hi, forgot my password. Can you reset it? User jsmith
Comments: [None]

Ideal JSON:
{{
  "thinking": "Pure administrative request with no technical content or learning value. No Q&A pairs to extract. Skip=true.",
  "skip": true,
  "qa_pairs": null
}}

Example 10 – Spam (SKIP)
Original Ticket:
Short Description: Claim your prize now!!!
Description: You've won! Click here: http://suspicious-site.com
Comments: [None]

Ideal JSON:
{{
  "thinking": "Obvious spam with no legitimate content. Skip=true.",
  "skip": true,
  "qa_pairs": null
}}

**Output Requirements:**
- Start with your thinking process in the "thinking" field
- Extract 3-8 Q&A pairs per ticket when not skipping (more for information-rich tickets)
- Think about different ways users might phrase the same question
- Make sure each answer is complete and actionable on its own
- Respond ONLY with valid JSON matching the schema above
- Do NOT include any text before or after the JSON object
- Do NOT wrap JSON in markdown code blocks

Ticket Info:
---------
{full_text}
---------
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
    output_file = "/projectnb/scc-chat/research/ticketparsing/classified_tickets_qna.jsonl"

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