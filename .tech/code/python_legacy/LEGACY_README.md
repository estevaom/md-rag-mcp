# Legacy Python Implementation

**⚠️ DEPRECATED: This Python implementation is maintained for compatibility and educational purposes only. Please use the [Rust implementation](../rust_scripts/) for better performance and active development.**

## Overview

This is the original Python implementation of the Journal RAG System. It provides:
- Semantic search using ChromaDB and sentence-transformers
- Frontmatter analysis for journal metadata
- MCP (Model Context Protocol) servers for AI agent integration

## Why This is Legacy

The Python implementation has been replaced with a Rust version that offers:
- **Superior search quality** with better embeddings (BGE-base-en-v1.5)
- **Blazing fast search speeds** (<20ms vs seconds)
- **Better error handling** and reliability
- **More efficient vector storage** with LanceDB
- **Template filtering** for cleaner results

## When to Use This Version

Consider using the Python implementation if:
- You need MCP protocol compatibility for specific AI agents
- You're more comfortable modifying Python code
- You're studying the implementation differences
- You have issues setting up Rust on your system
- You have NVIDIA GPU and prioritize fast indexing over search quality
- You're frequently reindexing large journals

## Setup Instructions

### 1. Create Virtual Environment

```bash
cd .tech/code/python_legacy/mcp
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Usage

#### Standalone RAG Search
```bash
source .tech/code/python_legacy/mcp/.venv/bin/activate
python .tech/code/python_legacy/scripts/rag_search.py
```

#### MCP Servers

For MCP integration, update your `mcp.json` to point to these Python scripts:

```json
{
  "mcpServers": {
    "journal-rag-mcp": {
      "command": "/path/to/project/.tech/code/python_legacy/mcp/.venv/bin/python3",
      "args": ["/path/to/project/.tech/code/python_legacy/mcp/journal_rag_mcp.py"]
    },
    "frontmatter-mcp": {
      "command": "/path/to/project/.tech/code/python_legacy/mcp/.venv/bin/python3",
      "args": ["/path/to/project/.tech/code/python_legacy/mcp/frontmatter_mcp.py"]
    }
  }
}
```

## Components

### MCP Servers (`mcp/`)
- `journal_rag_mcp.py`: Semantic search MCP server
- `frontmatter_mcp.py`: Metadata analysis MCP server
- `requirements.txt`: Python dependencies

### Scripts (`scripts/`)
- `rag_search.py`: Interactive CLI for semantic search

## Data Storage

- **Vector Database**: `.tech/data/chroma_db/` (ChromaDB)
- **Embedding Model**: all-MiniLM-L6-v2 (via sentence-transformers)

## Platform Setup Scripts

The automated setup scripts in the root directory can still set up the Python environment:
- `setup_mac_environment.sh`
- `setup_ubuntu_environment.sh`
- `setup_arch_environment.sh`

## Migration to Rust

To migrate to the Rust implementation:
1. Build the Rust tools (see main README)
2. Run `./reindex-rag.sh` to rebuild the index with LanceDB
3. Update any scripts to use the new Rust binaries

## Known Limitations

- Slower search operations compared to Rust
- Lower quality search results (uses simpler embeddings)
- ChromaDB can have stability issues with large datasets
- No template filtering (includes boilerplate in search results)
- Search response times in seconds rather than milliseconds

## Support

This implementation is provided as-is for compatibility. For new features and bug fixes, please use the Rust implementation.