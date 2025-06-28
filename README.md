# Journal RAG System

A powerful, privacy-focused journal system with AI-powered semantic search and metadata analysis. This system allows you to query your personal journal entries using natural language and analyze patterns in your mood, habits, and thoughts over time.

## ✨ Features

- **🔍 Semantic Search**: Query your journal entries using natural language  
- **📊 Frontmatter Analysis**: Track mood, anxiety, weight, and custom metrics over time
- **🤖 AI Agent Integration**: Connect to AI assistants like Rovo Dev, VS Code, etc.
- **🏠 Local Processing**: Journal files and search indexing stay on your machine
- **🚀 GPU Acceleration**: Optional NVIDIA GPU support for faster embeddings
- **📱 Cross-Platform**: macOS, Ubuntu/Debian, Arch Linux, and Windows/WSL with automated setup

## 🚀 Quick Start

### 1. Choose Your Setup Method

**macOS (Automated):**
```bash
./setup_mac_environment.sh
```

**Ubuntu/Debian (Automated):**
```bash
./setup_ubuntu_environment.sh
```

**Arch Linux (Automated):**
```bash
./setup_arch_environment.sh
```

**Windows/WSL (Automated):**
```bash
# After setting up WSL with Ubuntu, run:
./setup_ubuntu_environment.sh
```

For detailed Windows/WSL setup, see `setup_win_instructions.md`.

### 2. Configure MCP Servers

1. Copy the template: `cp mcp.json.template mcp.json`
2. Replace `${PROJECT_ROOT}` with your actual project path
3. Configure your AI agent to use the MCP servers

### 3. Start Journaling

Add entries to the `journal/` directory:
```
journal/2025/01/01.md
journal/2025/01/02.md
```

With optional frontmatter for tracking:
```yaml
---
date: 2025-01-01
mood: 7
anxiety: 3
weight_kg: 70
---

# Today's thoughts
Your journal content here...
```

## 📁 Directory Structure

```
md-rag-mcp/
├── README.md                           # This file
├── setup_mac_environment.sh           # macOS automated setup
├── setup_ubuntu_environment.sh        # Ubuntu/Debian automated setup
├── setup_arch_environment.sh          # Arch Linux automated setup
├── setup_win_instructions.md          # Windows/WSL setup guide
├── install_instructions.md            # General setup guide
├── mcp.json.template                  # MCP configuration template
├── journal/                           # Your journal entries
│   ├── 2025/01/01.md                 # Daily entries
│   └── topics/                       # Topic-based entries
└── .tech/                            # Technical components
    ├── code/
    │   ├── mcp/                      # MCP servers
    │   │   ├── journal_rag_mcp.py    # Semantic search server
    │   │   ├── frontmatter_mcp.py    # Metadata analysis server
    │   │   ├── requirements.txt      # Python dependencies
    │   │   └── .venv/               # Virtual environment
    │   └── scripts/
    │       └── rag_search.py         # Standalone search script
    ├── data/                         # Generated data
    │   └── chroma_db/               # Vector database
    └── docs/                        # Additional documentation
```

## 🔧 System Requirements

### Minimum Requirements
- **Python 3.8+**
- **4GB RAM** 
- **2GB free disk space**

### Recommended (for GPU acceleration)
- **NVIDIA GPU** with CUDA support
- **8GB+ GPU VRAM** for large embedding models
- **16GB+ system RAM**

### Supported Platforms
- **macOS** (Intel & Apple Silicon) - Automated setup
- **Ubuntu/Debian** (including WSL) - Automated setup
- **Arch Linux** - Automated setup
- **Windows** (via WSL2 with Ubuntu) - Automated setup

## 🎯 Usage

### Semantic Search
Query your journal entries using natural language:

```bash
# Via standalone script
source .tech/code/mcp/.venv/bin/activate
python .tech/code/scripts/rag_search.py

# Via AI agent (after MCP setup)
"What did I write about productivity last month?"
"Show me entries where I felt anxious"
```

### Frontmatter Analysis
Analyze patterns in your journal metadata:

```bash
# Via AI agent (after MCP setup)
"What's my average mood this month?"
"Show me my weight trend over the last 3 months"
"Plot my anxiety levels vs sleep quality"
```

## 🤖 AI Agent Integration

### Rovo Dev (Free) - Recommended!
Rovo Dev is a free AI agent built by Atlassian that works excellently with this journal system.

**Setup Steps:**
1. **Install Rovo Dev CLI**: Follow the complete setup guide at the [official Atlassian Community post](https://community.atlassian.com/forums/Rovo-for-Software-Teams-Beta/Introducing-Rovo-Dev-CLI-AI-Powered-Development-in-your-terminal/ba-p/3043623)
2. **Configure MCP Integration**:
   ```bash
   # Open Rovo Dev's MCP configuration file
   acli rovodev mcp
   
   # Copy the contents from mcp.json.template
   # Replace ${PROJECT_ROOT} with your actual path, e.g.:
   # /Users/yourname/Documents/md-rag-mcp
   ```
3. **Create .agent.md**: Create a custom persona that defines how Rovo Dev should interact with your journal. This persona can help with thoughtful questioning, pattern recognition across entries, balanced reflection prompts, and contextual analysis of your journaling themes and personal growth over time.
4. **Start Rovo Dev**:
   ```bash
   acli rovodev
   ```
5. **Start Querying**: Try commands like:
   - "What did I write about yesterday?"
   - "Show me my mood trends this month"
   - "Find entries where I mentioned productivity"

### Other Agents
**Cloud-based options:**
- **Cursor**: MCP-compatible, all conversations sent to cloud
- **GitHub Copilot**: If MCP-compatible, cloud-based

**Local privacy options:**
- **Cline** (VS Code extension): Can connect to local LLMs (Ollama, LM Studio)
- **Roo Code** (VS Code extension): Can connect to local LLMs for complete privacy

Any MCP-compatible AI agent can connect using the provided configuration.

## 📊 Frontmatter Fields

Track various metrics in your journal entries:

```yaml
---
date: 2025-01-01          # Entry date (required)
mood: 7                   # 1-10 scale
anxiety: 3                # 1-10 scale  
energy: 8                 # 1-10 scale
sleep_hours: 7.5          # Hours of sleep
weight_kg: 70             # Weight in kg
exercise_minutes: 30      # Exercise duration
weather: "sunny"          # Weather description
tags: ["work", "family"]  # Custom tags
---
```

You can customize these fields based on what you want to track.

## 🔍 Advanced Features

### GPU Acceleration
If you have an NVIDIA GPU, the system will automatically use it for faster embedding generation:

```bash
# Check GPU status
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

### Backup and Sync
Your journal is just markdown files - sync with any service:
- Git repositories
- Cloud storage (Dropbox, iCloud, etc.)
- Network drives

## 📚 Documentation

- **Setup Instructions**: `install_instructions.md`
- **Windows Setup**: `setup_win_instructions.md`  
- **Migration Plan**: `MIGRATION_PLAN.md` (development)

## 🤝 Contributing

This is an open-source project! Contributions welcome:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is open source. See LICENSE file for details.

## 🆘 Support

### Common Issues

**"Module not found" errors:**
- Ensure virtual environment is activated
- Verify requirements are installed in correct venv

**MCP connection issues:**
- Check paths in mcp.json are absolute, not relative
- Verify Python executable path is correct

**Slow performance:**
- Check if GPU acceleration is working
- Consider using a smaller embedding model
- Ensure sufficient RAM available

### Getting Help

1. Check the troubleshooting section in `install_instructions.md`
2. Review the setup guides for your platform
3. Open an issue on GitHub with system details

---

## 🔒 Privacy & Data Considerations

**What stays private (always local):**
- Your journal files and content
- RAG embeddings and search indexing
- Frontmatter analysis and statistics
- All file processing and storage

**What gets exposed with cloud-based AI agents (Rovo Dev, Cursor - both 100% cloud-based):**
- Your conversations about journal content
- AI-generated insights and analysis
- Personal reflections and patterns discussed
- Any journal excerpts shared during conversations

**For complete privacy:** Use VS Code extensions like Cline or Roo Code with local LLMs (Ollama, LM Studio, etc.). These extensions can connect to local models while keeping all conversations on your machine.

**Bottom line:** Your raw journal data stays local, but if you use cloud AI agents to analyze it, those conversations are not private.
