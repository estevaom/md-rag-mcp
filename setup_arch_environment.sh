#!/bin/bash

# Script to set up Python environments and dependencies on Arch Linux

# Function to print messages
print_message() {
  echo "----------------------------------------------------"
  echo "$1"
  echo "----------------------------------------------------"
}

# --- 1. System Dependencies ---
print_message "Checking and installing system dependencies..."

# Check for yay (AUR helper), install if not present
if ! command -v yay &> /dev/null; then
    echo "yay (AUR helper) not found. Attempting to install..."
    # This is a common way to install yay, but might need user intervention or sudo password
    # Ensure base-devel and git are installed first
    sudo pacman -S --needed --noconfirm git base-devel
    git clone https://aur.archlinux.org/yay.git /tmp/yay
    (cd /tmp/yay && makepkg -si --noconfirm)
    rm -rf /tmp/yay
    if ! command -v yay &> /dev/null; then
        echo "Failed to install yay. Please install it manually and re-run the script."
        exit 1
    fi
fi

# Install Python, venv, and build essentials
# python-pip is often included with python, python-build replaces python3-full/build-essential
sudo pacman -S --needed --noconfirm python python-pip python-venv python-build

# --- 2. NVIDIA CUDA Check ---
print_message "Checking for NVIDIA CUDA drivers..."
if ! command -v nvidia-smi &> /dev/null; then
  echo "nvidia-smi not found. Please ensure NVIDIA drivers and CUDA toolkit are installed correctly."
  echo "You might need to install packages like 'nvidia', 'nvidia-utils', 'cuda'."
  echo "Refer to the Arch Wiki for CUDA installation: https://wiki.archlinux.org/title/CUDA"
  # exit 1 # Commenting out exit to allow script to proceed if user wants to setup CPU only for now
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
    python -m venv "$SCRIPTS_VENV_DIR"
    echo "Activating virtual environment for $SCRIPTS_DIR..."
    # shellcheck source=./.tech/code/scripts/.venv/bin/activate
    source "$SCRIPTS_VENV_DIR/bin/activate"
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
    python -m venv "$MCP_VENV_DIR"
    echo "Activating virtual environment for $MCP_DIR..."
    # shellcheck source=./.tech/code/mcp/.venv/bin/activate
    source "$MCP_VENV_DIR/bin/activate"
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
