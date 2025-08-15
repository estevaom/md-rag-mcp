#!/bin/bash

# Script to set up Rust tools on macOS

# Function to print messages
print_message() {
  echo "----------------------------------------------------"
  echo "$1"
  echo "----------------------------------------------------"
}

# --- 1. System Dependencies ---
print_message "Checking and installing system dependencies..."

# Check for Homebrew, install if not present
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for the current session
    if [[ $(uname -m) == "arm64" ]]; then
        # Apple Silicon Mac
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        # Intel Mac
        echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/usr/local/bin/brew shellenv)"
    fi
    
    if ! command -v brew &> /dev/null; then
        echo "Failed to install Homebrew. Please install it manually and re-run the script."
        exit 1
    fi
fi

# Update Homebrew
brew update

# Install protobuf compiler (required for LanceDB)
brew install protobuf

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

# --- 5. Hardware Note ---
if [[ $(uname -m) == "arm64" ]]; then
    echo ""
    echo "Note: Apple Silicon Mac detected."
    echo "The tools are optimized for CPU performance and work great on M1/M2/M3 chips."
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