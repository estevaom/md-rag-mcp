# Journal RAG System

This repository contains the code for a journal Retrieval-Augmented Generation (RAG) system. This code was used for the journal published at https://dev.to/lord_magus/supercharging-my-vs-code-ai-agent-with-local-rag-25n8.

## Directory Structure

The project is organized with a focus on journaling, with technical components hidden:

```
/
├── README.md                 # Project overview
├── journal/                  # Journal entries
│   ├── 2025/                 # Organized by year
│   │   └── 04/               # Month
│   │       ├── 18.md         # Daily entries
│   │       └── 19.md
│   └── topics/               # Topic-based entries (future use)
├── code/                     # Code and scripts
│   ├── mcp/                  # MCP server code
│   │   └── journal_rag_mcp.py
│   ├── scripts/              # Python scripts
│   │   └── rag_search.py
│   └── data/                 # Data storage (e.g., vector DB)
│       └── chroma_db/        # Vector database (example)
└── .venv/                    # Python virtual environment
```

## Usage

### Journaling

Add daily journal entries in the `journal/YYYY/MM/` directory structure.
Note: The `.md` files currently present in the `journal/` directory are AI-generated examples provided for testing the indexing and querying functionality.

### RAG Search

To search your journal using semantic search:

```bash
source .venv/bin/activate
python .tech/code/scripts/rag_search.py
```

This will index all your journal entries recursively and allow you to search them semantically using natural language queries. For detailed setup steps, please refer to `install_instructions.md`.

## MCP Server

This repository also includes the code for an MCP server. This server allows you to connect your journal RAG system to an AI agent for enhanced interaction. Detailed instructions for setting up and connecting the MCP server can be found in `install_instructions.md`.
