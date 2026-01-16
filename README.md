# SCC Chatbot & Knowledge Base System

A comprehensive RAG-powered (Retrieval-Augmented Generation) chatbot system for the Boston University Shared Computing Cluster (SCC). This project includes tools for data ingestion, knowledge base management, and an interactive chatbot interface.

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Components](#components)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## Overview

The SCC Chatbot system helps users navigate SCC resources, troubleshoot issues, and find answers to technical questions through:

- **Knowledge Base Ingestion**: Scripts to parse and ingest support tickets, Q&A pairs, and TechWeb articles
- **Vector Database**: ChromaDB-powered semantic search across SCC documentation
- **RAG Chatbot**: AI assistant with tool-calling capabilities to search the knowledge base
- **Terminal Interface**: Rich terminal-based chat interface for user interactions

### Key Features

- 🔍 Semantic search across multiple knowledge sources (tickets, documentation, articles)
- 🤖 LLM-powered responses with retrieval augmentation
- 🔧 Extensible tool system for different data sources
- 🎨 Clean, modular architecture with separation of concerns
- 📊 Support for multiple LLM providers (GitHub Models, OpenAI)
- 💬 Interactive terminal UI with syntax highlighting

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      DATA PIPELINE                          │
├─────────────────────────────────────────────────────────────┤
│  Ticket Parsing → JSON                                      │
│  TechWeb Scraping → Parsed Articles                         │
│  Q&A Extraction → Structured Pairs                          │
│                     ↓                                       │
│  ChromaDB Ingestion → Vector Embeddings                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     CHATBOT SYSTEM                          │
├─────────────────────────────────────────────────────────────┤
│  Terminal Client ←→ FastAPI Server ←→ LLM Service           │
│                          ↓                                  │
│                    Tool Services                            │
│                   (ChromaDB Search)                         │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Data Ingestion Pipeline

#### Ticket Parsing (`scripts/parse_tickets.py`)
- Parses SCC support ticket data
- Extracts Q&A pairs and metadata
- Outputs structured JSON

#### TechWeb Article Scraping (`scripts/scrape_techweb.py`)
- Scrapes SCC TechWeb documentation
- Parses articles and metadata
- Prepares content for ingestion

#### ChromaDB Ingestion (`scripts/ingest_chromadb.py`)
- Ingests parsed data into ChromaDB
- Creates vector embeddings
- Manages multiple collections (Q&A, documentation, etc.)

**Example Usage:**
```bash
python scripts/ingest_chromadb.py \
    --db-path ./chroma_db \
    --collection qa_collection \
    --json-path /path/to/qa_pairs.json
```

### 2. Chatbot Server

FastAPI-based server with modular service architecture:

- **Core Layer**: Configuration management, ChromaDB connections
- **Service Layer**: 
  - Tool services (ChromaDB search tools)
  - LLM services (GitHub Models, OpenAI)
- **API Layer**: REST endpoints for chat interactions

**Key Endpoints:**
- `POST /chat` - Main chat endpoint
- `GET /health` - Health check

### 3. Terminal Client

Rich terminal interface for chatbot interaction:

- Syntax highlighting and markdown rendering
- Tool call visualization
- Command system (quit, clear, help)
- Token usage tracking

## Installation

### Prerequisites

- Python 3.10+
- pip

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# API Keys
GITHUB_API_KEY=your_github_token_here
OPENAI_API_KEY=your_openai_key_optional

# ChromaDB Configuration
CHROMA_DB_PATH=./chroma_db
QA_COLLECTION_NAME=qa_collection
DOCS_COLLECTION_NAME=documentation_collection

# LLM Configuration
DEFAULT_MODEL=gpt-4o-mini
MAX_TOKENS=1500
TEMPERATURE=0.7

# System Prompt (optional)
SYSTEM_PROMPT="Your custom system prompt..."

# Server Configuration
SERVER_HOST=localhost
SERVER_PORT=8000

# Logging
LOG_LEVEL=INFO
```

### System Prompt

The default system prompt guides the chatbot's behavior. It can be customized via the `SYSTEM_PROMPT` environment variable or in `server/core/config.py`.

## Usage

### 1. Prepare Your Knowledge Base

#### Parse Support Tickets
```bash
python scripts/parse_tickets.py \
    --input /path/to/tickets \
    --output ./data/qa_pairs.json
```

#### Scrape TechWeb Articles
```bash
python scripts/scrape_techweb.py \
    --url https://scc.bu.edu/techweb \
    --output ./data/articles.json
```

#### Ingest into ChromaDB
```bash
python scripts/ingest_chromadb.py \
    --db-path ./chroma_db \
    --collection qa_collection \
    --json-path ./data/qa_pairs.json \
    --batch-size 32
```

### 2. Start the Server

```bash
python -m server.main
# Or with uvicorn directly:
uvicorn server.main:app --host localhost --port 8000 --reload
```

The server will start on `http://localhost:8000`. API documentation is available at `http://localhost:8000/docs`.

### 3. Run the Client

In a separate terminal:

```bash
python -m client.main
# Or specify a custom server URL:
python -m client.main --server http://localhost:8000
```

### 4. Interact with the Chatbot

```
You: How do I submit a job to the SCC?
