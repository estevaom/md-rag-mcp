# MD-RAG-MCP Project Enhancement Migration Plan

## Overview

This document outlines the comprehensive migration plan to upgrade the `md-rag-mcp` project with significant improvements from the `life` project. The goal is to transform this into a robust, user-friendly open-source journal RAG system while ensuring no personal data is included.

## 🎯 Key Improvements to Implement

### 1. **Project Structure Reorganization**
- **Current:** `/code` structure  
- **New:** `/.tech/code` structure (matches life project)
- **Rationale:** Better organization, separates technical components from user content

### 2. **Enhanced MCP Capabilities**
- **Journal RAG MCP:** Enhanced version (32KB vs current 22KB)
- **NEW Frontmatter MCP:** Analyze journal frontmatter data (mood, anxiety, weight, etc.)
- **Improved Error Handling:** Better logging and debugging capabilities

### 3. **Automated Environment Setup**
- **Mac Setup Script:** Complete macOS environment configuration
- **Windows Setup Instructions:** Complete Windows/WSL setup guide
- **Arch Linux Setup Script:** Complete Arch Linux environment configuration
- **Dependency Management:** Consolidated requirements.txt with optimized dependencies

### 4. **User Experience Improvements**
- **Generic Paths:** Remove hardcoded personal paths
- **Flexible Configuration:** User-configurable paths and settings
- **Better Documentation:** Comprehensive setup and usage guides

## 📋 Migration Steps

### Phase 1: Structure Reorganization

#### Step 1.1: Create New Directory Structure
```bash
mkdir -p .tech/code/mcp
mkdir -p .tech/code/scripts
mkdir -p .tech/docs
mkdir -p .tech/data
```

#### Step 1.2: Move Existing Code
- Move `code/mcp/journal_rag_mcp.py` → `.tech/code/mcp/journal_rag_mcp.py`
- Move `code/scripts/` → `.tech/code/scripts/`
- Move `code/requirements.txt` → **DELETE** (will be replaced with better version)

#### Step 1.3: Clean Up Old Structure
- Remove old `code/` directory
- Update any references to old paths
- **Note:** Leave `journal/` folder untouched - already contains generic examples

### Phase 2: Enhanced MCP Implementation

#### Step 2.1: Upgrade Journal RAG MCP
- **Source:** `life/.tech/code/mcp/journal_rag_mcp.py` (32KB version)
- **Target:** `.tech/code/mcp/journal_rag_mcp.py`
- **Key Improvements:**
  - Better error handling and logging
  - Enhanced query capabilities
  - Improved performance
  - More robust path handling

#### Step 2.2: Add Frontmatter MCP
- **Source:** `life/.tech/code/mcp/frontmatter_mcp.py` (19KB)
- **Target:** `.tech/code/mcp/frontmatter_mcp.py`
- **Functionality:**
  - Query frontmatter fields (mood, anxiety, weight_kg, etc.)
  - Date range filtering
  - Statistical analysis
  - Multiple output formats (JSON, CSV, table)

#### Step 2.3: Update Requirements
- **New requirements.txt content:**
```
chromadb
sentence-transformers
torch
torchvision
torchaudio
python-frontmatter
langchain-text-splitters
pyyaml
```

### Phase 3: Automated Setup Scripts

#### Step 3.1: Create Mac Setup Script
- **Source:** `life/setup_mac_environment.sh`
- **Target:** `setup_mac_environment.sh`
- **Modifications Required:**
  - Remove hardcoded `/Users/estevao/` paths
  - Make paths relative to project root
  - Add user guidance for path configuration

#### Step 3.2: Create Windows Setup Instructions
- **Source:** Extract Windows/WSL content from `install_instructions.md`
- **Target:** `setup_win_instructions.md`
- **Content:** Windows-specific setup instructions (PowerShell commands, WSL setup, etc.)

#### Step 3.3: Create Arch Linux Setup Script
- **Source:** `life/setup_arch_environment.sh`
- **Target:** `setup_arch_environment.sh`
- **Modifications Required:**
  - Remove personal path references
  - Add generic user setup instructions

#### Step 3.4: Review Remaining install_instructions.md Content
- **Action:** After extracting Windows content, review what remains in `install_instructions.md`
- **Decision:** Determine if remaining content should be integrated into README.md or kept as separate install guide
- **Goal:** Eliminate redundant documentation and ensure clear, non-overlapping setup instructions

#### Step 3.5: Update Scripts for Generic Usage
**Key Changes Needed:**
- Replace hardcoded paths with environment variables
- Add path detection logic
- Provide clear instructions for users to set their own paths

### Phase 4: Configuration Management

#### Step 4.1: Create Template MCP Configuration
- **Target:** `mcp.json.template`
- **Content:** Generic MCP configuration with placeholders
- **User Variables:**
  - `${PROJECT_ROOT}` - User's project directory
  - `${PYTHON_PATH}` - Path to Python executable in venv

#### Step 4.2: Update Path Handling in MCPs
**Critical Changes:**
- Remove hardcoded `/Users/estevao/Documents/Code/life/` paths
- Implement dynamic project root detection
- Add fallback path resolution
- Include user configuration validation

### Phase 5: Documentation Updates

#### Step 5.1: Enhanced README
- **New Sections:**
  - Quick Start Guide
  - System Requirements
  - Multiple OS Support (Mac, Windows/WSL, Arch Linux)
  - Troubleshooting Guide

#### Step 5.2: Comprehensive Install Guide
- **Replace:** `install_instructions.md`
- **New Content:**
  - OS-specific setup procedures
  - Automated vs manual setup options
  - MCP configuration instructions
  - Testing and validation steps

#### Step 5.3: User Configuration Guide
- **New File:** `CONFIGURATION.md`
- **Content:**
  - How to customize paths
  - MCP server setup for different editors
  - Frontmatter field customization
  - Performance optimization

### Phase 6: User Experience Improvements

#### Step 6.1: Path Abstraction
**Implementation Strategy:**
```python
# Instead of hardcoded paths:
PROJECT_ROOT = "/Users/estevao/Documents/Code/life"

# Use dynamic detection:
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

#### Step 6.2: Configuration Validation
- Add startup checks for required directories
- Validate journal directory structure
- Provide helpful error messages for misconfigurations

#### Step 6.3: User-Friendly Setup
- Interactive setup script option
- Automatic path detection
- Configuration file generation

### Phase 7: Testing and Quality Assurance

#### Step 7.1: Test Setup Scripts
- Test on clean macOS system
- Test on clean Arch Linux system
- Validate automated dependency installation

#### Step 7.2: Test MCP Functionality
- Journal RAG query testing
- Frontmatter analysis testing
- Error handling validation

#### Step 7.3: Documentation Testing
- Follow installation instructions exactly
- Test configuration examples
- Validate troubleshooting guides

### Phase 8: Rovo Dev Setup Integration

#### Step 8.1: Add Rovo Dev Documentation
- **New Section in README:** "Using with Rovo Dev"
- **Setup Instructions:**
  - How to install Rovo Dev (free)
  - How to configure MCP connections
  - Example queries and usage patterns

#### Step 8.2: Rovo Dev Configuration Templates
- **File:** `rovo-dev-mcp.json.template`
- **Content:** Ready-to-use MCP configuration for Rovo Dev
- **Instructions:** Step-by-step Rovo Dev integration guide

## 🔧 Technical Implementation Details

### Path Sanitization Strategy
1. **Environment Variable Approach:**
   ```bash
   export JOURNAL_ROOT="/path/to/your/journal"
   export PROJECT_ROOT="/path/to/md-rag-mcp"
   ```

2. **Runtime Detection:**
   ```python
   # Detect project root from script location
   SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
   PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
   ```

3. **User Configuration File:**
   ```json
   {
     "journal_directory": "./journal",
     "data_directory": "./.tech/data",
     "embedding_model": "all-MiniLM-L6-v2"
   }
   ```

### MCP Configuration Abstraction
```json
{
    "mcpServers": {
        "journal-rag-mcp": {
            "command": "${PROJECT_ROOT}/.tech/code/mcp/.venv/bin/python3",
            "args": ["${PROJECT_ROOT}/.tech/code/mcp/journal_rag_mcp.py"]
        },
        "frontmatter-mcp": {
            "command": "${PROJECT_ROOT}/.tech/code/mcp/.venv/bin/python3",
            "args": ["${PROJECT_ROOT}/.tech/code/mcp/frontmatter_mcp.py"]
        }
    }
}
```

## ⚠️ Critical Considerations

### Data Privacy
- **ZERO personal data in repository**
- **Journal folder already contains generic examples - NO CHANGES NEEDED**
- **Sanitized configuration examples**
- **Clear user data separation**

### Backwards Compatibility
- **Migration script for existing users**
- **Gradual deprecation of old structure**
- **Clear migration documentation**

### Cross-Platform Support
- **macOS (Intel + Apple Silicon):** Automated bash setup script
- **Ubuntu/Debian (including WSL):** Automated bash setup script
- **Arch Linux:** Automated bash setup script
- **Windows/WSL:** Uses Ubuntu script after WSL setup

## 📦 Expected Deliverables

1. **Restructured codebase** with `.tech/` organization
2. **Enhanced journal RAG MCP** with improved functionality
3. **New frontmatter analysis MCP** for journal insights
4. **Automated setup scripts/guides** for Mac, Ubuntu/Debian, Arch Linux, and Windows/WSL
5. **Comprehensive documentation** with user guides
6. **Generic configuration templates** for easy customization
7. **Rovo Dev integration guide** for free AI agent setup
8. **Migration utilities** for existing users
9. **Testing framework** for quality assurance
10. **Examples and tutorials** for quick start

## 🎯 Success Criteria

- [ ] New users can set up the system in under 10 minutes
- [ ] Zero manual path editing required for basic setup
- [ ] Both MCP servers work correctly with generic paths
- [ ] Setup scripts work on clean OS installations
- [ ] Documentation is clear and comprehensive
- [ ] Rovo Dev integration works out of the box
- [ ] No personal data present in any files
- [ ] Backwards compatibility maintained for existing users

## 📅 Estimated Timeline

- **Phase 1-2:** Structure & MCP upgrades (2-3 hours)
- **Phase 3:** Setup scripts (2-3 hours)
- **Phase 4:** Configuration management (1-2 hours)
- **Phase 5:** Documentation (2-3 hours)
- **Phase 6:** UX improvements (1-2 hours)
- **Phase 7:** Testing (2-3 hours)
- **Phase 8:** Rovo Dev integration (1 hour)

**Total Estimated Time:** 11-17 hours of focused development work

---

This migration plan will transform the `md-rag-mcp` project into a professional, user-friendly open-source journal RAG system that anyone can easily set up and use while maintaining complete data privacy. 