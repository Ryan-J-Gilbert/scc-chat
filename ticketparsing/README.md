# QA Pair Extraction Pipeline

## Overview

This document describes the process used to extract, curate, and prepare question-answer (QA) pairs from support tickets for use in a Retrieval-Augmented Generation (RAG) system.

## Pipeline Stages

### 1. Initial LLM Processing

**Objective**: Parse support tickets to identify and extract relevant QA pairs.

**Process**:
- Each support ticket was processed using a Large Language Model (LLM)
- The LLM analyzed ticket content to determine if it contained information suitable for QA pair extraction
- When relevant information was found, the LLM generated structured QA pairs capturing:
  - Common user questions
  - Clear, actionable answers
  - Categorical classifications

**Output Format**: JSONL file with the following structure:
```jsonl
{
  "ticket_number": "INCXXXXXXXX",
  "result": {
    "thinking": "Analysis thoughts",
    "skip": false,
    "qa_pairs": [
      {
        "question": "...",
        "answer": "...",
        "category": "..."
      }
    ]
  },
  "elapsed": 48.83
}
```

### 2. Extraction to JSON

**Objective**: Consolidate all QA pairs into a single, structured JSON file.

**Tool**: `extract_qa.py`

**Usage**:
```bash
python extract_qa.py input.jsonl -o qa_pairs.json -v 1.0
```

**Process**:
- Reads through all JSONL entries
- Skips entries marked with `"skip": true`
- Extracts all valid QA pairs
- Assigns unique IDs to each pair
- Generates metadata (timestamp, version, source file, counts)
- Outputs prettified JSON for easy manual review

**Output Structure**:
```json
{
  "metadata": {
    "generated_at": "2026-01-10T14:30:45.123456",
    "version": "1.0",
    "source_file": "input.jsonl",
    "total_pairs": 123,
    "skipped_entries": 5
  },
  "qa_pairs": [
    {
      "id": 0,
      "question": "Why am I getting 'no suitable queues' when submitting jobs?",
      "answer": "This warning appears when your requested job time exceeds..."
    }
  ]
}
```

### 3. Manual Curation

**Objective**: Remove sensitive information and low-quality pairs.

**Process**:
Manual review of the prettified JSON file to remove:

**Sensitive Information**:
- Email addresses
- Project file paths (e.g., `/project/username/...`)
- Usernames and account identifiers
- Any personally identifiable information (PII)

**Quality Issues**:
- Overly specific pairs that don't generalize well
- Duplicate or near-duplicate content
- Incomplete or unclear answers
- Pairs that reference specific tickets or users

**Method**:
- Open the JSON file in a text editor
- Scroll through the `qa_pairs` array
- Delete entire QA pair objects (including their enclosing `{...}`) that contain:
  - Sensitive information
  - Poor quality content
  - Non-generalizable information

Note: for v1 generation to minimize manual review labor: a plain text of Q&A pairs was generated and only pairs with the sensitive info were selected for removal.  

### 4. Final QA Dataset

**Output**: A curated JSON file ready for RAG system integration.

**Characteristics**:
- Clean, generalized QA pairs
- No sensitive or private information
- Unique sequential IDs for reference
- Metadata for versioning and tracking
- Human-reviewed for quality and relevance

## Tools

### extract_qa.py

**Purpose**: Extract and consolidate QA pairs from JSONL to JSON format.

**Features**:
- Handles malformed JSON gracefully
- Skips entries marked for exclusion
- Generates metadata automatically
- Produces prettified output for manual review
- Robust error handling

**Arguments**:
- `input_file`: Path to JSONL file with LLM-extracted QA pairs
- `--output, -o`: Output JSON file path (default: `input.qa.json`)
- `--version, -v`: Version string for metadata (default: `1.0`)

## Best Practices

1. **Version Control**: Increment version numbers when creating new extractions
2. **Backup**: Keep copies of both raw JSONL and curated JSON files
3. **Documentation**: Note any major changes or filtering decisions in commit messages
4. **Privacy First**: When in doubt, remove the QA pair rather than risk exposing sensitive info
5. **Quality Over Quantity**: Better to have fewer high-quality pairs than many mediocre ones

## Integration with RAG System

The final curated JSON file can be ingested into the RAG system by:
1. Loading the JSON file
2. Extracting the `qa_pairs` array
3. Creating embeddings for questions (and optionally answers)
4. Indexing in a vector database
5. Using for semantic search and retrieval during user queries

## File Naming Convention

Recommended naming pattern:
- Raw JSONL: `tickets_raw_YYYYMMDD.jsonl`
- Extracted JSON: `qa_pairs_v{version}_YYYYMMDD.json`
- Curated JSON: `qa_pairs_curated_v{version}_YYYYMMDD.json`

## Changelog

Track major changes to the dataset:
- **v1.0** (2026-01-10): Initial finalized dataset of ~half available tickets 
- **vX.X** (YYYY-MM-DD):
