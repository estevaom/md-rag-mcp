# Journal RAG System: Setup Instructions

This document provides general setup instructions for the Journal RAG System. For platform-specific setup, see:
- **macOS:** Run `./setup_mac_environment.sh`
- **Ubuntu/Debian:** Run `./setup_ubuntu_environment.sh`
- **Arch Linux:** Run `./setup_arch_environment.sh`  
- **Windows/WSL:** Run `./setup_ubuntu_environment.sh` (after WSL setup)

## General Setup Process

### 1. Python Environment Setup

The project uses Python with virtual environments for dependency isolation. The recommended structure places virtual environments within the `.tech/code/mcp/` directory.

### 2. Project Dependencies

The project requires several Python packages including:
- PyTorch (for ML acceleration)
- ChromaDB (vector database)
- Sentence Transformers (embeddings)
- Python Frontmatter (markdown processing)
- Additional utilities

**Installation:**

**Use the automated setup scripts instead of manual installation:**

- **macOS:** `./setup_mac_environment.sh`
- **Ubuntu/Debian:** `./setup_ubuntu_environment.sh`
- **Arch Linux:** `./setup_arch_environment.sh`  
- **Windows/WSL:** `./setup_ubuntu_environment.sh` (after WSL setup)

These scripts automatically handle virtual environment creation, dependency installation, and GPU acceleration setup.

### 3. MCP Server Configuration

The project includes two MCP (Model Context Protocol) servers:

1. **Journal RAG MCP** (`journal_rag_mcp.py`) - Semantic search over journal entries
2. **Frontmatter MCP** (`frontmatter_mcp.py`) - Analysis of journal metadata (mood, weight, etc.)

#### Basic MCP Setup Template

Create your MCP configuration based on `mcp.json.template`:

```json
{
  "mcpServers": {
    "journal-rag-mcp": {
      "autoApprove": ["query_journal", "update_index"],
      "disabled": false,
      "timeout": 60,
      "command": "/path/to/your/project/.tech/code/mcp/.venv/bin/python3",
      "args": ["/path/to/your/project/.tech/code/mcp/journal_rag_mcp.py"],
      "env": {},
      "transportType": "stdio"
    },
    "frontmatter-mcp": {
      "autoApprove": ["query_frontmatter"],
      "disabled": false,
      "timeout": 30,
      "command": "/path/to/your/project/.tech/code/mcp/.venv/bin/python3",
      "args": ["/path/to/your/project/.tech/code/mcp/frontmatter_mcp.py"],
      "env": {},
      "transportType": "stdio"
    }
  }
}
```

Replace `/path/to/your/project/` with your actual project directory path.

### 4. Journal Structure

The system expects journal entries in the `journal/` directory:
```
journal/
├── 2025/
│   ├── 01/
│   │   ├── 01.md
│   │   └── 02.md
│   └── 02/
└── topics/
```

Each journal entry can include YAML frontmatter for metadata:
```yaml
---
date: 2025-01-01
mood: 7
anxiety: 3
weight_kg: 70
tags: ["reflection", "goals"]
---

# Today's Entry
Your journal content here...
```

### 5. Testing the Setup

After running one of the automated setup scripts:

1. **Test Journal RAG:**
   ```bash
   source .tech/code/mcp/.venv/bin/activate
   python .tech/code/scripts/rag_search.py
   ```

2. **Test MCP Servers:**
   The MCP servers should be configured in your AI agent (VS Code, Rovo Dev, etc.) and will be available for querying journal content and analyzing frontmatter data.

### 6. GPU Acceleration (Optional)

If you have an NVIDIA GPU:
1. Install appropriate NVIDIA drivers for your system
2. PyTorch should automatically detect and use CUDA when available
3. Verify GPU detection:
   ```bash
   python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
   ```

## Troubleshooting

### Virtual Environment Issues
- Ensure you're using the correct Python path in MCP configuration
- Verify virtual environment activation: `which python` should point to `.tech/code/mcp/.venv/bin/python`

### Path Detection Issues
- The MCP servers use dynamic path detection based on script location
- Ensure `.tech/` directory structure is maintained
- Check that journal entries are in the `journal/` directory

### MCP Connection Issues
- Verify paths in MCP configuration are absolute (not relative)
- Check that Python virtual environment is properly activated
- Ensure all dependencies are installed in the correct virtual environment

## Next Steps

1. **Configure your AI agent** with the MCP servers
2. **Add journal entries** to the `journal/` directory
3. **Test querying** through your AI agent
4. **Customize frontmatter fields** as needed for your use case

For detailed configuration options and advanced usage, see the main README.md file.
