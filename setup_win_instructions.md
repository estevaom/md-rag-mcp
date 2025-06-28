# Windows/WSL Setup Instructions

This document outlines the complete setup process for the Journal RAG System on Windows using WSL (Windows Subsystem for Linux), including Python and CUDA configuration for GPU acceleration.

## Prerequisites
- Windows 10 version 2004 or higher (Build 19041 or higher) or Windows 11
- A computer with virtualization capabilities enabled in BIOS/UEFI
- NVIDIA GPU (optional, for GPU acceleration)

## 1. WSL Installation and Setup

### Install WSL 2
1. Open PowerShell as Administrator and run:
   ```powershell
   wsl --install
   ```

2. If WSL is already installed but you need to upgrade to WSL 2:
   ```powershell
   wsl --set-default-version 2
   wsl --set-version Ubuntu 2
   ```

3. Verify WSL version:
   ```powershell
   wsl --status
   ```

### Install Ubuntu on WSL
1. If Ubuntu wasn't installed automatically:
   ```powershell
   wsl --install -d Ubuntu
   ```

2. Set up your Ubuntu username and password when prompted

## 2. VSCode Configuration

1. Install the VSCode WSL extension:
   - Open VSCode
   - Go to Extensions (Ctrl+Shift+X)
   - Search for "WSL"
   - Install "Remote - WSL" extension by Microsoft

2. Connect to WSL:
   - Click on the green remote button in the bottom-left corner
   - Select "Connect to WSL"
   - VSCode will reopen connected to your WSL environment

## 3. NVIDIA Driver Setup (Optional - for GPU acceleration)

1. Install the latest NVIDIA drivers on Windows:
   - Download the appropriate driver for your GPU from [NVIDIA's website](https://www.nvidia.com/Download/index.aspx)
   - Run the installer and follow the prompts
   - Restart your computer if required

2. Verify NVIDIA driver installation in WSL:
   ```bash
   nvidia-smi
   ```
   This should display information about your GPU if the drivers are properly installed

## 4. Automated Environment Setup

### Quick Setup (Recommended)
1. **Clone/download the project and navigate to it:**
   ```bash
   cd /path/to/your/md-rag-mcp
   ```

2. **Run the automated Ubuntu setup script:**
   ```bash
   ./setup_ubuntu_environment.sh
   ```
   
   This script will automatically:
   - Update system packages
   - Install Python development tools
   - Create both MCP and Scripts virtual environments
   - Install all dependencies (including PyTorch with CUDA support)
   - Verify GPU setup if available
   - Provide usage instructions

### Manual Setup (Alternative)
If you prefer manual control or the automated script fails, you can follow the manual steps below, but the automated script is recommended for most users.

## 5. Running the System

### Test the Journal RAG System
1. **Test standalone scripts** (if scripts environment was set up):
   ```bash
   # Navigate to scripts directory and activate its environment
   cd .tech/code/scripts
   source .venv/bin/activate
   python rag_search.py
   deactivate
   cd ../../../  # Return to project root
   ```

2. **Test MCP servers** (for AI agent integration):
   ```bash
   # MCP servers will be tested through your AI agent configuration
   # Make sure .tech/code/mcp/.venv/bin/python3 path is correct in your mcp.json
   ```

### Set Up MCP Servers (for AI Integration)
1. Configure your AI agent (VS Code, Rovo Dev, etc.) to use the MCP servers
2. Use the template configuration in `mcp.json.template` 
3. Replace placeholder paths with your actual project paths

## 6. Troubleshooting

### CUDA Not Detected
If PyTorch doesn't detect CUDA:
1. Verify NVIDIA drivers are installed: `nvidia-smi`
2. Check WSL 2 is being used: `wsl --status`
3. Ensure PyTorch CUDA version is compatible with installed drivers

### Python Package Installation Issues
If you encounter "externally-managed-environment" errors:
1. Ensure you've activated the correct virtual environment:
   - For MCP: `source .tech/code/mcp/.venv/bin/activate`
   - For Scripts: `source .tech/code/scripts/.venv/bin/activate`
2. Verify you're using the virtual environment's Python: `which python`
3. Update pip if needed: `pip install --upgrade pip`
4. If packages fail to install, you may need: `sudo apt install build-essential python3-dev`

### WSL Performance Issues
1. Ensure WSL 2 is being used (not WSL 1)
2. Place project files within WSL file system for better performance
3. Consider increasing WSL memory allocation in `.wslconfig` file

### Virtual Environment Issues
1. **Wrong environment activated**: Make sure you're using the right environment:
   - MCP servers need: `.tech/code/mcp/.venv/bin/python3`
   - Scripts need: `.tech/code/scripts/.venv/bin/python3`
2. **Missing dependencies**: If modules are not found, reinstall in the correct environment:
   ```bash
   source .tech/code/mcp/.venv/bin/activate
   pip install -r .tech/code/mcp/requirements.txt
   ```
3. **Environment not found**: Ensure you completed the setup steps and both environments exist

### Path Issues
1. Use Unix-style paths within WSL (forward slashes)
2. Project root should be detected automatically by the scripts
3. Check that all `.tech/` directory structure is properly created
4. Verify both virtual environments exist:
   - `.tech/code/mcp/.venv/` (required)
   - `.tech/code/scripts/.venv/` (optional)

## Next Steps

After completing this setup:
1. Review the main README.md for usage instructions
2. Check out the configuration guide for customizing the system
3. Set up your preferred AI agent integration (Rovo Dev instructions included)

---

**Note:** This setup creates a Linux environment within Windows. All commands after WSL installation should be run within the WSL Ubuntu terminal, not Windows Command Prompt or PowerShell. 