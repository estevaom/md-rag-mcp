#!/bin/bash

# Script to set up Python environments and dependencies on macOS

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

# Install Python (includes pip and venv)
# Also install build tools that might be needed for Python packages
brew install python

# Ensure we have the latest pip
python3 -m pip install --upgrade pip

# --- 2. GPU/CUDA Check ---
print_message "Checking for GPU acceleration support..."

# Check for NVIDIA CUDA (rare on modern Macs, but possible on older Intel Macs with eGPUs)
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA CUDA detected via nvidia-smi."
    nvidia-smi
elif [[ $(uname -m) == "arm64" ]]; then
    echo "Apple Silicon Mac detected. GPU acceleration available through Metal Performance Shaders."
    echo "Many ML frameworks support Metal acceleration (PyTorch, TensorFlow, etc.)"
else
    echo "Intel Mac detected. GPU acceleration may be available through:"
    echo "- Metal Performance Shaders (for supported frameworks)"
    echo "- External NVIDIA GPU (eGPU) if connected"
fi

# --- 3. Project Paths ---
SCRIPTS_DIR=".tech/code/scripts"
MCP_DIR=".tech/code/mcp"
SCRIPTS_VENV_DIR="$SCRIPTS_DIR/.venv"
MCP_VENV_DIR="$MCP_DIR/.venv"

# --- 4. Setup for .tech/code/scripts ---
print_message "Setting up environment for $SCRIPTS_DIR..."
if [ -d "$SCRIPTS_DIR" ]; then
  if [ -f "$SCRIPTS_DIR/requirements.txt" ]; then
    echo "Creating Python virtual environment in $SCRIPTS_VENV_DIR..."
    python3 -m venv "$SCRIPTS_VENV_DIR"
    echo "Activating virtual environment for $SCRIPTS_DIR..."
    # shellcheck source=./.tech/code/scripts/.venv/bin/activate
    source "$SCRIPTS_VENV_DIR/bin/activate"
    echo "Upgrading pip in virtual environment..."
    pip install --upgrade pip
    echo "Installing dependencies from $SCRIPTS_DIR/requirements.txt..."
    pip install -r "$SCRIPTS_DIR/requirements.txt"
    deactivate
    echo "Setup for $SCRIPTS_DIR complete."
  else
    echo "WARNING: $SCRIPTS_DIR/requirements.txt not found. Skipping dependency installation for scripts."
  fi
else
  echo "WARNING: Directory $SCRIPTS_DIR not found. Skipping setup for scripts."
fi

# --- 5. Setup for .tech/code/mcp ---
print_message "Setting up environment for $MCP_DIR..."
if [ -d "$MCP_DIR" ]; then
  if [ -f "$MCP_DIR/requirements.txt" ]; then
    echo "Creating Python virtual environment in $MCP_VENV_DIR..."
    python3 -m venv "$MCP_VENV_DIR"
    echo "Activating virtual environment for $MCP_DIR..."
    # shellcheck source=./.tech/code/mcp/.venv/bin/activate
    source "$MCP_VENV_DIR/bin/activate"
    echo "Upgrading pip in virtual environment..."
    pip install --upgrade pip
    echo "Installing dependencies from $MCP_DIR/requirements.txt..."
    pip install -r "$MCP_DIR/requirements.txt"
    deactivate
    echo "Setup for $MCP_DIR complete."
  else
    echo "WARNING: $MCP_DIR/requirements.txt not found. Skipping dependency installation for MCP."
  fi
else
  echo "WARNING: Directory $MCP_DIR not found. Skipping setup for MCP."
fi

print_message "Environment setup script finished."
echo "To use the environments, navigate to the respective directories and run:"
echo "For scripts: cd $SCRIPTS_DIR && source .venv/bin/activate"
echo "For MCP:     cd $MCP_DIR && source .venv/bin/activate"
echo ""
echo "Note: If you encounter any issues with package installations, you may need to install"
echo "additional development tools with: xcode-select --install" 