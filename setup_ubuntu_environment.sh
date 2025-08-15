#!/bin/bash

# Script to set up Rust tools on Ubuntu/Debian (including WSL)

# Function to print messages
print_message() {
  echo "----------------------------------------------------"
  echo "$1"
  echo "----------------------------------------------------"
}

# --- 1. System Dependencies ---
print_message "Checking and installing system dependencies..."

# Update package lists
sudo apt update

# Install build essentials and protobuf (for LanceDB)
sudo apt install -y build-essential protobuf-compiler

# --- 2. Rust Installation ---
print_message "Checking and installing Rust via rustup..."
if ! command -v rustc &> /dev/null; then
  echo "Rust not found. Installing via rustup..."
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
  source "$HOME/.cargo/env"
  echo "Rust installed successfully!"
  rustc --version
  cargo --version
else
  echo "Rust is already installed:"
  rustc --version
  cargo --version
fi

# --- 3. Build Rust Tools ---
print_message "Building Rust CLI tools..."

# Build frontmatter query tool
FRONTMATTER_DIR=".tech/code/rust_scripts/frontmatter_query"
if [ -d "$FRONTMATTER_DIR" ]; then
  echo "Building frontmatter query tool..."
  (cd "$FRONTMATTER_DIR" && cargo build --release)
  if [ $? -eq 0 ]; then
    echo "✅ Frontmatter query tool built successfully"
  else
    echo "❌ Failed to build frontmatter query tool"
  fi
else
  echo "WARNING: $FRONTMATTER_DIR not found"
fi

# Build RAG search tools
RAG_DIR=".tech/code/rust_scripts/rag_search"
if [ -d "$RAG_DIR" ]; then
  echo "Building RAG search tools..."
  echo "Note: First build will download embedding models (~400MB)"
  (cd "$RAG_DIR" && cargo build --release)
  if [ $? -eq 0 ]; then
    echo "✅ RAG search tools built successfully"
    echo "   - rag-index: For indexing journal entries"
    echo "   - rag-search: For semantic search"
  else
    echo "❌ Failed to build RAG search tools"
  fi
else
  echo "WARNING: $RAG_DIR not found"
fi

# --- 4. Create convenience scripts ---
print_message "Creating convenience scripts..."

# Ensure scripts are executable
chmod +x search-rag.sh 2>/dev/null || true
chmod +x query-frontmatter.sh 2>/dev/null || true
chmod +x reindex-rag.sh 2>/dev/null || true

# --- 5. WSL Note ---
if grep -qi microsoft /proc/version 2>/dev/null; then
    echo ""
    echo "Note: WSL environment detected."
    echo "The tools work great in WSL. For best performance, keep your journal files"
    echo "within the WSL filesystem rather than on Windows drives."
fi

# --- 6. Initial Index ---
print_message "Setup complete!"
echo ""
echo "To get started:"
echo "1. Add your journal entries to the 'journal/' directory"
echo "2. Run './reindex-rag.sh' to build the search index"
echo "3. Use './search-rag.sh \"your query\"' to search"
echo "4. Use './query-frontmatter.sh --fields mood anxiety' to analyze metadata"
echo ""
echo "First indexing will download embedding models (~400MB) to .fastembed_cache/"
echo "This is a one-time download that will be cached for future use."