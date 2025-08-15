# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Journal RAG System - a privacy-focused journal application with AI-powered semantic search and metadata analysis capabilities. The system uses local embeddings and vector databases to enable natural language queries over personal journal entries while keeping all data on the local machine.

## Architecture

### Core Components (Rust Implementation)

1. **RAG Search Tools** (`.tech/code/rust_scripts/rag_search/`)
   - `rag-index`: Indexes journal entries into LanceDB with BGE embeddings
   - `rag-search`: Semantic search over indexed journal content
   - Uses fastembed for efficient vector generation
   - LanceDB for vector storage (replacing ChromaDB)

2. **Frontmatter Query Tool** (`.tech/code/rust_scripts/frontmatter_query/`)
   - Analyzes YAML frontmatter in journal entries
   - Supports statistical analysis and multiple output formats
   - Efficient metadata extraction and aggregation

3. **Helper Scripts** (root directory)
   - `reindex-rag.sh`: Rebuilds the entire search index
   - `search-rag.sh`: Convenient wrapper for semantic search
   - `query-frontmatter.sh`: Convenient wrapper for metadata queries

### Data Storage
- Journal entries: `journal/` directory with YYYY/MM/DD.md structure
- Vector database: `.tech/data/lancedb/` (auto-created on first index)
- Embeddings: Generated using BGE-base-en-v1.5 model via fastembed

## Development Commands

### Building the Rust Tools

```bash
# Build all tools (from project root)
cd .tech/code/rust_scripts/rag_search && cargo build --release
cd ../frontmatter_query && cargo build --release

# Or build individually
cargo build --release --manifest-path .tech/code/rust_scripts/rag_search/Cargo.toml
cargo build --release --manifest-path .tech/code/rust_scripts/frontmatter_query/Cargo.toml
```

### Using the Tools

```bash
# Reindex all journal entries (required after adding new entries)
./reindex-rag.sh

# Search journal
./search-rag.sh "anxiety and sleep"
./search-rag.sh "productivity" --num-results 5
./search-rag.sh "meditation" --after 2025-01-01 --before 2025-12-31

# Query frontmatter
./query-frontmatter.sh --fields mood anxiety weight_kg
./query-frontmatter.sh --fields mood --stats
./query-frontmatter.sh --fields mood anxiety --format csv > data.csv
```

### Direct Binary Usage

```bash
# Index with options
.tech/code/rust_scripts/rag_search/target/release/rag-index \
  --journal-dir journal \
  --lance-dir .tech/data/lancedb \
  --rebuild  # Force full rebuild

# Search with all options
.tech/code/rust_scripts/rag_search/target/release/rag-search "query" \
  --num-results 10 \
  --after 2025-01-01 \
  --before 2025-12-31 \
  --format json \
  --files-only \
  --debug

# Frontmatter query with all options
.tech/code/rust_scripts/frontmatter_query/target/release/frontmatter-query \
  --path journal \
  --fields mood anxiety weight_kg \
  --start-date 2025-01-01 \
  --end-date 2025-12-31 \
  --stats \
  --format table \
  --include-files
```

## Key Implementation Details

### Rust Architecture
- Workspace structure with separate crates for indexing and searching
- Shared dependencies managed through workspace Cargo.toml
- Async/await patterns using tokio runtime
- Error handling with anyhow and proper Result types

### Journal File Structure
- Files located in `journal/` directory
- Expected path pattern: `journal/YYYY/MM/DD.md` or `journal/topics/*.md`
- Optional YAML frontmatter for metadata tracking
- Template noise automatically filtered during indexing

### Vector Database (LanceDB)
- Columnar storage format optimized for vector similarity search
- Automatic creation on first index
- BGE-base-en-v1.5 embeddings (768 dimensions)
- Efficient nearest neighbor search with cosine similarity

### Performance Characteristics
- Indexing: Slower than GPU-accelerated Python (but higher quality embeddings)
- Search: <20ms response times (blazing fast)
- Search quality: Superior relevance compared to Python implementation
- Binary sizes: ~190MB (includes embedded model weights)

## Important Notes

- First run will download embedding models (~400MB) to `.fastembed_cache/`
- LanceDB files are stored in `.tech/data/lancedb/` (excluded from git)
- Search operations are extremely fast (<20ms) with better relevance
- All processing happens locally - no external API calls
- Template boilerplate is automatically removed during indexing