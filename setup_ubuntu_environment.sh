#!/bin/bash

# Script to set up Python environments and dependencies on Ubuntu (including WSL)

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

# Install Python development tools and build essentials
sudo apt install -y python3-venv python3-full build-essential python3-dev

# Ensure we have the latest pip
python3 -m pip install --upgrade pip --user

# --- 2. NVIDIA CUDA Check ---
print_message "Checking for NVIDIA CUDA drivers..."
if ! command -v nvidia-smi &> /dev/null; then
  echo "nvidia-smi not found. GPU acceleration not available."
  echo "If you have an NVIDIA GPU:"
  echo "- On WSL: Install NVIDIA drivers on Windows host"
  echo "- On native Ubuntu: Install nvidia-driver-xxx package"
  echo "- Refer to NVIDIA documentation for your specific setup"
  echo "Continuing with CPU-only setup..."
else
  echo "NVIDIA drivers detected via nvidia-smi."
  nvidia-smi
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

# --- 6. Verify GPU Setup (if available) ---
if command -v nvidia-smi &> /dev/null; then
  print_message "Verifying GPU acceleration setup..."
  echo "Testing PyTorch CUDA detection..."
  source "$MCP_VENV_DIR/bin/activate"
  python3 -c "
import torch
print('CUDA available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('CUDA device count:', torch.cuda.device_count())
    print('CUDA device name:', torch.cuda.get_device_name(0))
else:
    print('CUDA not detected - running on CPU (slower but functional)')
" 2>/dev/null || echo "Note: PyTorch CUDA test failed - this is normal if PyTorch is still installing"
  deactivate
fi

print_message "Environment setup script finished."
echo "To use the environments, navigate to the respective directories and run:"
echo "For scripts: cd $SCRIPTS_DIR && source .venv/bin/activate"
echo "For MCP:     cd $MCP_DIR && source .venv/bin/activate"
echo ""
echo "Next steps:"
echo "1. Configure MCP servers with your AI agent"
echo "2. Add journal entries to the journal/ directory"
echo "3. Test the system with your AI agent or run:"
echo "   python $SCRIPTS_DIR/rag_search.py (if scripts environment was set up)"
echo ""
if command -v nvidia-smi &> /dev/null; then
  echo "Note: GPU acceleration should be available through PyTorch CUDA support"
else
  echo "Note: Running on CPU - consider installing NVIDIA drivers for better performance"
fi 