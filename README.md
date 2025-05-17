# HPC RAG Chatbot

A RAG (Retrieval-Augmented Generation) chatbot system for helping users with questions about the university's Shared Computing Cluster (SCC). The system consists of a client-server architecture where:

- The server handles document retrieval, LLM inference, and conversation logging
- The client manages the user interface and conversation history

## System Architecture

### Server
- Built with FastAPI and Uvicorn
- Connects to a vector database for document retrieval
- Uses OpenAI-compatible API for LLM inference (via GitHub models or Azure)
- Implements JWT authentication for session management
- Logs all interactions in a SQLite database

### Client
- Command-line interface for interacting with the chatbot
- Manages message history and conversation context
- Handles streaming responses for real-time interaction
- Formats messages for better readability in the terminal


## Configuration

### Server Configuration
- Set up LLM API access:
  - For development, set the `GITHUB_LLM_TOKEN` environment variable in your `.bashrc` file
  - For production, consider using a `.env` file (implementation pending)
- JWT secret configuration in `jwt_utils.py` (ensure this is properly secured for production)
- Model and retrieval parameters in `config.py`

### Client Configuration
- Default server URL can be configured in the client code or set via environment variable:
  ```bash
  export CHATBOT_SERVER_URL="http://your-server:port"
  ```

## Usage

### Starting the Server
```bash
cd /projectnb/scc-chat/research
module load python3/3.12.4
module load sqlite3/3.44.2
source ragenv/bin/activate
python server.py
```

The server will start on port 8000 by default (http://0.0.0.0:8000).

### Running the Client
```bash
cd /projectnb/scc-chat/research
module load python3/3.12.4
source ragenv/bin/activate
python client.py
```

### Client Command-Line Options
```
Options:
  --server URL     Server URL (default: http://localhost:8000)
  --debug          Enable debug output
  --no-log         Disable logging
  --nostream       Disable streaming responses
```

Example:
```bash
python client.py --server http://hpc-server:8000 --debug
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/start_session` | POST | Initiates a new chat session and returns a JWT token |
| `/chat` | POST | Processes chat messages and returns responses (supports streaming) |
| `/health` | GET | Returns server health status |

## Authentication

The system uses JWT tokens for authentication:
1. Client requests a new session via `/start_session` with a username
2. Server generates a unique chat ID and returns a JWT token
3. Client includes this token with each subsequent request
4. Server validates the token before processing requests

## Logging

The system logs various events to a SQLite database:
- User messages
- Agent responses
- Tool calls
- Retrieval queries and results
- Errors

## Retrieval System

The RAG system uses a vector database to store and retrieve relevant documents:
1. User query is analyzed to determine if retrieval is needed
2. If needed, the query is used to retrieve relevant documents
3. Retrieved documents are included in the context for the LLM's response

## Development Roadmap

### High Priority
- [ ] Deploy to production
  - [ ] Set up CORS middleware (currently commented out)
  - [ ] Implement `.env` file for secure token management
  - [ ] Configure JWT secret properly
- [ ] Improve error handling, especially with JWT validation
- [ ] Fix formatting issues with ordered lists and bold text
- [ ] DB analysis scripts
- [ ] Optimize document storage and chunking

### Medium Priority
- [ ] Refine system prompt to focus responses on SCC information
- [ ] Improve tool call result formatting
- [ ] Develop visual interface (Gradio integration previously attempted)

### Future Features
- [ ] IT ticket parsing and analysis
- [ ] Additional tools for user job management
  - [ ] View queued jobs
  - [ ] Module availability checking
- [ ] Make usage intuitive scraper.py (for collecting and formatting TechWeb pages)
- [ ] Modifying scraper to use an LLM to parse webpages, with optimal chunking

## Resource Usage

- Currently using GitHub models free tier
  - GPT-4o: 10 requests/min, 50/day
  - GPT-4o mini: 15 requests/min, 150/day
- Estimated Azure cost: ~$0.24 per 100 simple chats

