# Journal RAG System

A powerful, privacy-focused journal system with AI-powered semantic search and metadata analysis. This system allows you to query your personal journal entries using natural language and analyze patterns in your mood, habits, and thoughts over time.

## ✨ Features

- **🔍 Semantic Search**: Query your journal entries using natural language with Rust-powered performance
- **📊 Frontmatter Analysis**: Track mood, anxiety, weight, and custom metrics over time
- **🦀 Rust Implementation**: High-performance indexing and search using native Rust
- **🏠 Local Processing**: Journal files and search indexing stay on your machine
- **⚡ Fast Embeddings**: Uses fastembed for efficient vector generation
- **📱 Cross-Platform**: Works on macOS, Linux, and Windows (via WSL)

## 🚀 Quick Start

### 1. Automated Setup

Choose your platform and run the setup script:

**macOS:**
```bash
./setup_mac_environment.sh
```

**Ubuntu/Debian (including WSL):**
```bash
./setup_ubuntu_environment.sh
```

**Arch Linux:**
```bash
./setup_arch_environment.sh
```

These scripts will:
- Install Rust (if needed)
- Install system dependencies
- Build all tools
- Set up convenience scripts

### 2. Manual Setup (Optional)

If you prefer manual setup:

**Install Rust:**
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

**Build the tools:**
```bash
# Build the RAG search tools
cd .tech/code/rust_scripts/rag_search
cargo build --release

# Build the frontmatter query tool
cd ../frontmatter_query
cargo build --release
```

### 3. Start Journaling

Add entries to the `journal/` directory using the provided templates:

**Daily Entry** (`template/daily.md`):
```
journal/2025/01/01.md
journal/2025/01/02.md
```

**Weekly Retrospective** (`template/weekly_retro.md`):
```
journal/2025/week_01_retro.md
```

Example frontmatter for tracking:
```yaml
---
date: 2025-01-01
mood: 7
energy: 8
sleep_hours: 7.5
tags: ["work", "learning", "reflection"]
---

# Today's thoughts
Your journal content here...
```

Templates are provided in the `template/` directory:
- `daily.md` - Daily journal template with sections for reflection
- `weekly_retro.md` - Weekly retrospective for reviewing progress
- `prompt.md` - Guide for configuring your AI assistant persona

## 🎯 Usage

### Convenient Shell Scripts

The project includes convenient shell scripts for common operations:

```bash
# Reindex journal entries (run after adding new entries)
./reindex-rag.sh

# Search your journal
./search-rag.sh "anxiety and sleep patterns"
./search-rag.sh "rust learning journey" -n 10
./search-rag.sh "relationship insights" --after 2025-06-01
./search-rag.sh "debugging professional" --files-only

# Query frontmatter metadata
./query-frontmatter.sh --fields mood anxiety weight_kg
./query-frontmatter.sh --fields mood --start-date 2025-07-01 --stats
./query-frontmatter.sh --fields weight_kg --format csv > weight_data.csv
```

### Direct Command Usage

You can also use the Rust binaries directly:

#### Index Your Journal Entries

```bash
# Index all journal files
.tech/code/rust_scripts/rag_search/target/release/rag-index \
  --journal-dir journal \
  --lance-dir .tech/data/lancedb

# Force rebuild the entire index
.tech/code/rust_scripts/rag_search/target/release/rag-index --rebuild

# Index only recent files (since a specific date)
.tech/code/rust_scripts/rag_search/target/release/rag-index --since 2025-01-01
```

#### Semantic Search

```bash
# Basic search
.tech/code/rust_scripts/rag_search/target/release/rag-search "productivity tips"

# Search with date filters
.tech/code/rust_scripts/rag_search/target/release/rag-search "anxiety" \
  --after 2025-01-01 \
  --before 2025-01-31

# Get more results
.tech/code/rust_scripts/rag_search/target/release/rag-search "meditation" --num-results 20

# Output as JSON
.tech/code/rust_scripts/rag_search/target/release/rag-search "goals" --format json
```

#### Frontmatter Analysis

```bash
# Query specific fields
.tech/code/rust_scripts/frontmatter_query/target/release/frontmatter-query \
  --fields mood anxiety weight_kg

# Calculate statistics
.tech/code/rust_scripts/frontmatter_query/target/release/frontmatter-query \
  --fields mood anxiety \
  --stats

# Export as CSV
.tech/code/rust_scripts/frontmatter_query/target/release/frontmatter-query \
  --fields mood weight_kg \
  --format csv > mood_weight.csv
```

## 📁 Directory Structure

```
markdown-journal-rust/
├── README.md                           # This file
├── CLAUDE.md                          # Instructions for Claude Code
├── setup_mac_environment.sh           # macOS setup script
├── setup_ubuntu_environment.sh        # Ubuntu/Debian setup script
├── setup_arch_environment.sh          # Arch Linux setup script
├── search-rag.sh                      # Convenient search script
├── reindex-rag.sh                     # Reindex journal script
├── query-frontmatter.sh               # Query metadata script
├── .claude/                           # Claude Code integration
│   ├── agents/                        # Custom AI agents
│   ├── commands/                      # Slash commands
│   └── settings.json                  # Claude Code settings
├── template/                          # Journal templates
│   ├── daily.md                      # Daily entry template
│   ├── weekly_retro.md               # Weekly review template
│   └── prompt.md                     # AI assistant configuration
├── journal/                           # Your journal entries
│   ├── 2025/01/01.md                 # Daily entries
│   └── topics/                       # Topic-based entries
└── .tech/                            # Technical components
    ├── code/
    │   ├── rust_scripts/             # Rust implementations (PRIMARY)
    │   │   ├── rag_search/           # RAG search workspace
    │   │   │   ├── rag-index/        # Indexing tool
    │   │   │   └── rag-search/       # Search tool
    │   │   └── frontmatter_query/    # Metadata analysis tool
    │   └── python_legacy/            # Python implementation (DEPRECATED)
    │       ├── mcp/                  # MCP servers
    │       ├── scripts/              # Python scripts
    │       └── LEGACY_README.md      # Legacy documentation
    └── data/                         # Generated data
        ├── lancedb/                  # Vector database (Rust)
        └── chroma_db/                # Vector database (Python legacy)
```

## 🔧 System Requirements

### Minimum Requirements
- **Rust 1.70+** (install via rustup)
- **4GB RAM** 
- **2GB free disk space**

### Recommended
- **8GB+ RAM** for better performance
- **SSD storage** for faster indexing

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

## 🤖 Claude Code Integration

This project includes enhanced Claude Code integration for a superior development experience:

### Features

- **Custom Agents** (`.claude/agents/`):
  - `journal-rag-search`: Automatically searches your journal when context is needed
  - `journal-field-completer`: Helps complete journal frontmatter fields
  - `weekly-retro-analyzer`: Analyzes weekly retrospectives

- **Slash Commands** (`.claude/commands/`):
  - `/start`: Initialize your journaling session
  - `/commit`: Smart git commits with context

- **Status Line**: Real-time token usage tracking (requires `bunx ccusage`)

- **Automatic Timestamps**: Each prompt includes current timestamp for context

### Setup (Optional)

1. Claude Code will automatically detect the `.claude` directory
2. For status line, install ccusage: `npm install -g ccusage`
3. Agents and commands are available immediately

### Usage Examples

With Claude Code:
- Ask about past events - the RAG agent will search automatically
- Use `/start` to begin a new session with context
- Use `/commit` for intelligent commit messages

These integrations are optional but recommended for the best experience.

## 🔍 Advanced Features

### Backup and Sync

Your journal is just markdown files - sync with any service:
- Git repositories
- Cloud storage (Dropbox, iCloud, etc.)
- Network drives

The LanceDB index (`.tech/data/lancedb/`) can be rebuilt anytime from your journal files.

## 📚 Documentation

- **Setup Scripts**: `setup_mac_environment.sh`, `setup_ubuntu_environment.sh`, `setup_arch_environment.sh`
- **Claude Code Guide**: `CLAUDE.md`

## 🆘 Support

### Common Issues

**"Command not found" errors:**
- Ensure Rust is installed: `rustc --version`
- Check if tools are built: `ls .tech/code/rust_scripts/*/target/release/`
- Use full paths or create aliases

**Indexing issues:**
- Ensure journal directory exists and contains .md files
- Check file permissions
- Try rebuilding with `--rebuild` flag

**Performance issues:**
- The first indexing might be slow as models are downloaded
- Subsequent runs use cached models and are much faster
- Consider using fewer results with `--num-results`

### Getting Help

1. Check the documentation files
2. Review the `--help` output for each tool
3. Open an issue on GitHub with system details

---

## 🔒 Privacy & Data Considerations

**What stays private (always local):**
- Your journal files and content
- Vector embeddings and search indexing
- Frontmatter analysis and statistics
- All file processing and storage

**Performance Note:** This Rust implementation offers superior search quality and blazing-fast search speeds (<20ms) compared to the Python version. While indexing is slower than the GPU-accelerated Python version, the search results are more accurate and retrieval is nearly instantaneous.

---

## 📦 Legacy Python Implementation

A Python implementation is available in `.tech/code/python_legacy/` for compatibility and educational purposes. This includes:

- Original MCP servers for AI agent integration
- ChromaDB-based semantic search
- Python-based frontmatter analysis

**Note:** The Python implementation is deprecated and not actively maintained. It's provided for:
- Users who need MCP protocol compatibility
- Educational comparison between implementations
- Fallback if Rust setup is problematic

For setup instructions, see [`.tech/code/python_legacy/LEGACY_README.md`](.tech/code/python_legacy/LEGACY_README.md).

**We strongly recommend using the Rust implementation for all new projects.**