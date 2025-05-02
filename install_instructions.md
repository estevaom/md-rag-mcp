# Project Life: Environment Setup Instructions

This document outlines the complete setup process for the Project Life development environment, including WSL (Windows Subsystem for Linux), Python, and CUDA configuration for GPU acceleration.

## 1. WSL Installation and Setup

### Prerequisites
- Windows 10 version 2004 or higher (Build 19041 or higher) or Windows 11
- A computer with virtualization capabilities enabled in BIOS/UEFI

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

## 3. NVIDIA Driver Setup

1. Install the latest NVIDIA drivers on Windows:
   - Download the appropriate driver for RTX 4090 from [NVIDIA's website](https://www.nvidia.com/Download/index.aspx)
   - Run the installer and follow the prompts
   - Restart your computer if required

2. Verify NVIDIA driver installation in WSL:
   ```bash
   nvidia-smi
   ```
   This should display information about your GPU if the drivers are properly installed

## 4. Python Environment Setup

1. Update Ubuntu packages:
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

2. Install Python development tools:
   ```bash
   sudo apt install -y python3-venv python3-full build-essential
   ```

4. Create a Python virtual environment:
   ```bash
   python3 -m venv .venv
   ```

5. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```
   You should see `(.venv)` at the beginning of your prompt

## 5. PyTorch and CUDA Installation

1. With the virtual environment activated, install PyTorch with CUDA support:
   ```bash
   pip install torch torchvision torchaudio
   ```
   
   Note: The default installation will detect and use CUDA if available. If you need a specific CUDA version, you can use:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

2. Verify CUDA is detected by PyTorch:
   ```bash
   python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('CUDA device count:', torch.cuda.device_count()); print('CUDA device name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
   ```
   
   Expected output:
   ```
   CUDA available: True
   CUDA device count: 1
   CUDA device name: NVIDIA GeForce RTX 4090
   ```

## 6. Project Dependencies Installation

1. Install the project requirements:
   ```bash
   pip install -r code/requirements.txt
   ```

## 7. RAG Script Configuration

To ensure the RAG script leverages the GPU for embedding generation and uses the correct paths, check or update the `code/scripts/rag_search.py` file:

1. Add torch import (if missing):
   ```python
   import torch
   ```

2. Update the embedding model initialization function:
   ```python
   def initialize_embedding_model(model_name):
       """Initializes and returns the Sentence Transformer model with GPU support."""
       console.print(f"\nInitializing embedding model: [cyan]{model_name}[/cyan]")
       try:
           # Check if CUDA is available
           device = "cuda" if torch.cuda.is_available() else "cpu"
           if device == "cuda":
               console.print(f"  [green]CUDA is available! Using GPU: {torch.cuda.get_device_name(0)}[/green]")
           else:
               console.print("  [yellow]CUDA not available. Using CPU for embeddings (slower).[/yellow]")
           
           # Load model with device specification
           model = SentenceTransformer(model_name, device=device)
           console.print("  [green]Embedding model loaded successfully.[/green]")
           return model
       except Exception as e:
           console.print(f"[bold red]Error initializing embedding model:[/bold red] {e}")
           return None
   ```

3. Verify path configuration:
   Ensure the paths correctly point to your journal data and the desired database location within the project. The script should calculate `PROJECT_ROOT` relative to its location (`code/scripts/`).
   ```python
   # --- Configuration ---
   import os
   from rich.console import Console # Added for printing

   # Initialize console for rich printing (if not already done)
   console = Console()

   # Get the project root directory (assuming script is in code/scripts/)
   PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Go up 3 levels
   DATA_DIRECTORY = os.path.join(PROJECT_ROOT, "journal")
   CHROMA_DB_PATH = os.path.join(PROJECT_ROOT, "code", "data", "chroma_db") # Adjusted path relative to new PROJECT_ROOT
   CHROMA_COLLECTION_NAME = "life_journal_collection" # Ensure this matches
   EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2' # Ensure this matches
   CHUNK_SIZE = 500  # Example value
   CHUNK_OVERLAP = 50  # Example value
   ```

## 8. Running the RAG Proof-of-Concept

1. Activate the virtual environment (if not already activated):
   ```bash
   source .venv/bin/activate
   ```

2. Run the script:
   ```bash
   python code/scripts/rag_search.py
   ```

3. The script should now:
   - Detect and use your RTX 4090 for embedding generation
   - Load and process the markdown files
   - Create embeddings and store them in the vector database
   - Allow you to query the database

## 9. MCP Server Setup (Optional)

This section describes how to set up the Model Context Protocol (MCP) server, which allows the AI assistant (like Roo in VS Code) to interact with your local journal data.

### Step 1: Install MCP Dependencies

The MCP server has its own set of Python dependencies. Ensure your virtual environment (`.venv`) is activated before running this command:

```bash
pip install -r code/mcp/requirements.txt
```

### Step 2: Configure VS Code

You need to tell VS Code how to find and run the MCP server script.

1.  Open VS Code Settings:
    *   Go to `File > Preferences > Settings` (or use the shortcut `Ctrl+,`).
2.  Search for "MCP Servers":
    *   In the search bar, type `mcp servers`.
3.  Add Server Configuration:
    *   Find the "Model Context Protocol: Servers" setting and click "Edit in settings.json".
    *   Add the following JSON object to the `mcpServers` configuration. If `mcpServers` doesn't exist, create it.

    ```json
    {
      "mcpServers": {
        "journal-rag-mcp": {
          "command": "${workspaceFolder}/.venv/bin/python3",
          "args": [
            "./code/mcp/journal_rag_mcp.py" // Path relative to workspaceFolder
          ],
          "env": {},
          "disabled": false,
          "alwaysAllow": [],
          "autoApprove": [
            "query_journal" // Automatically approve journal queries
          ]
        }
      }
    }
    ```

4.  **Explanation:**
    *   `${workspaceFolder}` is a VS Code variable representing the root directory of your project (`md-rag-mcp`).
    *   The `command` points to the Python interpreter within your virtual environment.
    *   The `args` specify the MCP server script to run.
    *   `autoApprove` allows the specified tool (`query_journal`) to run without prompting you each time.
5.  Restart VS Code:
    *   It's often a good idea to restart VS Code after changing this setting to ensure the server is recognized.

## Troubleshooting

### CUDA Not Detected
If PyTorch doesn't detect CUDA:
1. Verify NVIDIA drivers are installed: `nvidia-smi`
2. Check WSL 2 is being used: `wsl --status`
3. Ensure PyTorch CUDA version is compatible with installed drivers

### Python Package Installation Issues
If you encounter "externally-managed-environment" errors:
1. Ensure you've activated the virtual environment: `source .venv/bin/activate`
2. Verify you're using the virtual environment's Python: `which python`

### Performance Issues
If embedding generation is slow despite GPU detection:
1. Monitor GPU usage: `nvidia-smi -l 1` (updates every second)
2. Check batch size settings in the script
3. Consider using a smaller embedding model if memory is limited
