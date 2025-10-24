## Testing: setup ollama serving for 2 hours:
Submit job:
`qsub /projectnb/scc-chat/research/ticketparsing/serverspawner.sh`
Check job:
`qstat -u ryanjg` -> replace with your email
Extract node name:
e.g. `scc-x06`
Set host
`export OLLAMA_HOST=scc-x06:11434`
Go to directory to run ollama bin if testing model chat:
`/projectnb/scc-chat/ollama/bin`

For running python script, load env:
```
module load miniconda
mamba activate myenv
```

Next step: Both ollama server setup and parsing can be combined into one job that exits when finished.

## LLM Parsing
- Note we can use batching to speed up the overall process
- Steps:
    1. First, we classify and reason why tickets with the LLM into one of: 
        - 'beneficial': clearly contains a problem with steps to resolution
        - 'unbeneficial': may contain a problem, but the ticket does not clearly show steps to resolution
        - 'spam': ticket is spam/scam, e.g. asking to confirm a payment, viruses, or other irrelevant material
        - 'administrative': ticket is for internal use, such as routing a ticket, but does not contain steps to resolve any issue

    2. Then we extract relevant information from the ticket with the LLM:
        - category (string): short, broad categorization of the issue
        - technical_summary (string): technical summary of the ticket, anonymized with PII removed
        - resolution_steps (list of string): resolution steps

Notes:
Models llama3.2 3b and qwen 3 8b (nothink) struggle to classify unbeneficial, thinking is able to determine
maybe better to have thinking mode and just fill out entire process, and mark if unbeneficial

Try to refine prompt, seems like its better to skip the initial classficiation, and just have it output skipped or something if its useless. Otherwise extract useful info. Some tickets arent fully resolved, but still have some info!
 

