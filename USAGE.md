```bash
cd /projectnb/scc-chat/research
module load python3/3.12.4  
module load sqlite3/3.44.2  
source ragenv/bin/activate
python chat.py
```

Ryan's recommended route for this app:
- Use what I have, with API. Make a clear message to not include any sensitive information
- Program can be called anywhere with a module import, pretty light to just do API handling, db querying
- potential issue exposing github token if done this way, will be a bit of an honor system
- can add some logging of the chat use for further refining and documents
- upsides are: fast to run, can run big models,  

Locally hosted route:
- not 100% sure, seems like vLLM may work and can serve as drop in w openai api
- a server to run this could be dynamically started and dropped ad hoc
- could fix issues with data privacy and github PAT exposure


Notes:  
- Currently using github models free tier! 10req/min 50/day gpt4o and 15req/min 150/day gpt4o mini
- Ticket chats: use llm to parse important details, discard personal names and info that are irrelevant
- tool use, e.g. see avail nodes with my command scc-techinfo
- setup github token env var in .bashrc
- need to organize all the files and whatnot, a bit of a mess
   - need to abstract tool usage
- rcs examples https://rcs.bu.edu/examples/ for documents?

- rough cost estimate for 4o-mini on azure https://azure.microsoft.com/en-us/pricing/calculator/:
average chat = 2 querying tool calls, 3 ish questions roughly 6000 total tokens 50 50 input/output,
100 a month = $0.22

- check my job status?
 
- telemetry disabled, will this be an issue? more info here: https://docs.trychroma.com/docs/overview/telemetry 
   - open source code also provided for above

- switch embeddings model cache? -> https://github.com/chroma-core/chroma/blob/3c827a4117bd6cbe903951948439f0886f9bf610/chromadb/utils/embedding_functions/onnx_mini_lm_l6_v2.py#L38
