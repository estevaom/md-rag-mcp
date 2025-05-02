#!/usr/bin/env python3
import sys
import json
import os
import time
import traceback
import frontmatter

# --- Early Startup Logging ---
print("[MCP Server Debug] Script starting up", file=sys.stderr, flush=True)
print(f"[MCP Server Debug] Python version: {sys.version}", file=sys.stderr, flush=True)
print(f"[MCP Server Debug] Current working directory: {os.getcwd()}", file=sys.stderr, flush=True)
print(f"[MCP Server Debug] Script directory: {os.path.dirname(os.path.abspath(__file__))}", file=sys.stderr, flush=True)

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    import torch
except ImportError as e:
    print(json.dumps({
        "jsonrpc": "2.0",
        "error": {
            "code": -32000, # Server error
            "message": f"Missing required Python package: {e}. Please install chromadb, sentence-transformers, and torch.",
        }
    }), file=sys.stderr)
    sys.exit(1)

# --- Configuration ---
# Calculate PROJECT_ROOT based on this script's location (code/mcp/journal_rag_mcp.py)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# PROJECT_ROOT is two directories up from SCRIPT_DIR
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

CHROMA_DB_PATH = os.path.join(PROJECT_ROOT, "code", "data", "chroma_db")
CHROMA_COLLECTION_NAME = "life_journal_collection"
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
DEFAULT_N_RESULTS = 3

# --- Global Variables ---
embedding_model = None
chroma_collection = None
is_initialized = False

# --- Logging ---
def log_error(message):
    """Logs an error message to stderr."""
    print(f"[MCP Server Error] {message}", file=sys.stderr, flush=True)

def log_info(message):
    """Logs an info message to stderr."""
    print(f"[MCP Server Info] {message}", file=sys.stderr, flush=True)

# --- Initialization Function ---
def initialize_resources():
    """Loads the embedding model and connects to ChromaDB."""
    global embedding_model, chroma_collection, is_initialized
    if is_initialized:
        return True

    log_info("Initializing resources...")
    try:
        # 1. Initialize Embedding Model
        log_info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        log_info(f"Using device: {device}")
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)
        log_info("Embedding model loaded.")

        # 2. Initialize ChromaDB
        log_info(f"Connecting to ChromaDB at: {CHROMA_DB_PATH}")
        if not os.path.exists(CHROMA_DB_PATH):
             log_info(f"ChromaDB path does not exist: {CHROMA_DB_PATH}. Creating it now.")
             try:
                 os.makedirs(CHROMA_DB_PATH, exist_ok=True)
                 log_info(f"Created ChromaDB directory: {CHROMA_DB_PATH}")
             except Exception as e:
                 log_error(f"Failed to create ChromaDB directory: {e}")
                 log_error(traceback.format_exc())
                 return False # Indicate initialization failure

        chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        log_info(f"Getting/Creating collection: {CHROMA_COLLECTION_NAME}")
        chroma_collection = chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)
        log_info("ChromaDB collection ready.")

        is_initialized = True
        log_info("Resources initialized successfully.")
        return True

    except Exception as e:
        log_error(f"Initialization failed: {e}")
        log_error(traceback.format_exc())
        embedding_model = None
        chroma_collection = None
        is_initialized = False
        return False

# --- Timestamp Tracking Functions ---
def get_last_indexed_time():
    """Gets the timestamp of the last indexing operation."""
    timestamp_file = os.path.join(PROJECT_ROOT, "code", "data", "last_indexed_time.txt")

    if not os.path.exists(timestamp_file):
        return 0  # Return 0 if file doesn't exist (never indexed)
        
    try:
        with open(timestamp_file, 'r') as f:
            timestamp = float(f.read().strip())
        return timestamp
    except:
        return 0  # Return 0 if there's an error reading the file

def update_last_indexed_time():
    """Updates the timestamp of the last indexing operation to current time."""
    timestamp_file = os.path.join(PROJECT_ROOT, "code", "data", "last_indexed_time.txt")

    try:
        # Create directory if it doesn't exist
        timestamp_dir = os.path.dirname(timestamp_file)
        log_info(f"Ensuring directory exists: {timestamp_dir}")
        os.makedirs(timestamp_dir, exist_ok=True)
        
        # Write current timestamp
        current_time = time.time()
        log_info(f"Writing timestamp {current_time} to {timestamp_file}")
        with open(timestamp_file, 'w') as f:
            f.write(str(current_time))
        log_info(f"Timestamp updated successfully")
        return True
    except Exception as e:
        log_error(f"Error updating timestamp: {e}")
        log_error(traceback.format_exc())
        return False

def load_markdown_docs_since(directory_path, timestamp):
    """
    Loads only markdown files that have been modified since the given timestamp.
    
    Args:
        directory_path (str): The path to the directory containing Markdown files.
        timestamp (float): Unix timestamp to compare against file modification times.
        
    Returns:
        list: A list of frontmatter.Post objects for files modified since timestamp.
    """
    documents = []
    if not os.path.isdir(directory_path):
        log_error(f"Error: Directory not found: {directory_path}")
        return documents

    log_info(f"Scanning directory for modified files: {directory_path}")
    found_files = False
    
    # Walk through directory and subdirectories
    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            if filename.endswith(".md"):
                filepath = os.path.join(root, filename)
                
                # Check if file was modified after the timestamp
                if os.path.getmtime(filepath) > timestamp:
                    found_files = True
                    # Get relative path from the base directory for better source identification
                    rel_path = os.path.relpath(filepath, directory_path)
                    
                    try:
                        post = frontmatter.load(filepath)
                        # Add filename and path to metadata for later reference
                        if 'source' not in post.metadata:
                            post.metadata['source'] = rel_path
                        documents.append(post)
                        log_info(f"  Loaded modified file: {rel_path}")
                    except Exception as e:
                        log_error(f"  Error loading {rel_path}: {e}")

    if not found_files:
        log_info(f"No modified .md files found since {time.ctime(timestamp)}")

    return documents

# --- Index Update Function ---
def update_journal_index(full_reindex=False):
    """
    Updates the journal index with new or modified entries.
    
    Args:
        full_reindex (bool): Whether to reindex all entries or only new/modified ones.
        
    Returns:
        tuple: (success, message) where success is a boolean and message is a status message.
    """
    try:
        # Import functions from rag_search.py
        sys.path.append(os.path.join(PROJECT_ROOT, "code", "scripts"))
        try:
            from rag_search import (
                load_markdown_docs, split_docs, initialize_embedding_model,
                initialize_vector_store, index_chunks
            )
        except ImportError as e:
            log_error(f"Error importing from rag_search.py: {e}")
            log_error(f"sys.path: {sys.path}")
            return False, f"Error importing from rag_search.py: {e}"
        
        # Define data directory (same as in rag_search.py)
        DATA_DIRECTORY = os.path.join(PROJECT_ROOT, "journal")
        
        # Track stats for reporting
        files_processed = 0
        chunks_indexed = 0
        
        # Load documents (all or only new/modified)
        if full_reindex:
            # Process all documents
            log_info("Performing full reindex of all journal entries")
            documents = load_markdown_docs(DATA_DIRECTORY)
            files_processed = len(documents)
        else:
            # Get last indexing timestamp
            last_indexed_time = get_last_indexed_time()
            log_info(f"Performing incremental index update since {time.ctime(last_indexed_time)}")
            
            # Process only new or modified documents
            documents = load_markdown_docs_since(DATA_DIRECTORY, last_indexed_time)
            files_processed = len(documents)
            
            if not documents:
                return True, "No new or modified journal entries found."
        
        log_info(f"Found {files_processed} files to process")
        
        # Split documents into chunks
        chunks = split_docs(documents)
        chunks_indexed = len(chunks)
        
        if not chunks:
            return True, f"No chunks generated from {files_processed} files."
        
        log_info(f"Split into {chunks_indexed} chunks")
        
        # Initialize embedding model and vector store
        embed_model = initialize_embedding_model(EMBEDDING_MODEL_NAME)
        chroma_collection = initialize_vector_store(CHROMA_DB_PATH, CHROMA_COLLECTION_NAME)
        
        if not embed_model or not chroma_collection:
            return False, "Failed to initialize embedding model or vector store."
        
        # Index chunks
        log_info(f"Indexing {chunks_indexed} chunks")
        indexing_successful = index_chunks(chroma_collection, chunks, embed_model)
        
        if indexing_successful:
            # Update last indexed time
            update_last_indexed_time()
            return True, f"Successfully indexed {chunks_indexed} chunks from {files_processed} files."
        else:
            return False, "Indexing failed."
            
    except Exception as e:
        log_error(f"Error updating index: {str(e)}")
        log_error(traceback.format_exc())
        return False, f"Error updating index: {str(e)}"

# --- RAG Query Function ---
def perform_rag_query(query_text: str, n_results: int = DEFAULT_N_RESULTS):
    """Executes a semantic search query."""
    if not is_initialized or embedding_model is None or chroma_collection is None:
        log_error("Query attempted before resources were initialized.")
        return None, "Resources not initialized"

    try:
        log_info(f"Encoding query: '{query_text}'")
        query_embedding = embedding_model.encode([query_text.strip()])

        log_info(f"Querying collection '{chroma_collection.name}' for {n_results} results...")
        results = chroma_collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        log_info("Query successful.")

        # Format results
        formatted_results = []
        if results and results.get('ids') and results['ids'][0]:
            for i, doc_text in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {}
                distance = results['distances'][0][i] if results['distances'] and results['distances'][0] else None
                formatted_results.append({
                    "source": metadata.get('source', 'N/A'),
                    "text": doc_text,
                    "distance": distance
                })
        return formatted_results, None # Results, No error message

    except Exception as e:
        log_error(f"Error during query: {e}")
        log_error(traceback.format_exc())
        return None, str(e) # No results, Error message

# --- MCP Response Formatting ---
def create_mcp_response(request_id, result=None, error=None):
    """Creates a JSON-RPC 2.0 response dictionary."""
    response = {"jsonrpc": "2.0", "id": request_id}
    if error:
        response["error"] = error
    else:
        response["result"] = result
    return response

def create_mcp_error(code, message):
    """Creates an MCP error object."""
    return {"code": code, "message": message}

# --- Main Server Loop ---
def main():
    """Reads MCP requests from stdin, processes them, writes responses to stdout."""
    if not initialize_resources():
        # Send an error response if init fails, although the process might exit before this
        init_error_response = create_mcp_response(
            request_id=None, # No request ID available yet
            error=create_mcp_error(-32000, "Server initialization failed. Check stderr logs.")
        )
        # Cannot reliably send this if init fails early, stderr log is primary indicator
        # print(json.dumps(init_error_response), flush=True)
        log_error("Exiting due to initialization failure.")
        sys.exit(1) # Exit if resources can't be loaded

    log_info("MCP server started. Waiting for requests on stdin...")

    for line in sys.stdin:
        request_id = None # Reset for each request
        try:
            log_info(f"Received request line: {line.strip()}")
            request = json.loads(line)
            request_id = request.get("id")
            method = request.get("method")
            params = request.get("params", {})
            log_info(f"Processing method: {method} for request ID: {request_id}")

            response = None

            if method == "initialize":
                log_info("Handling 'initialize' method.")
                # Handle the initial handshake from Cline
                # Respond with basic server info (can be expanded later if needed)
                # Respond with required server info and protocol version
                response = create_mcp_response(request_id, result={
                    "protocolVersion": "2024-11-05", # Specify MCP protocol version
                    "serverInfo": {
                        "name": "journal-rag-mcp-server", # Required server name
                        "displayName": "Journal RAG Server",
                        "version": "0.1.0",
                        # Add other server info if needed
                    },
                    "capabilities": {
                        "tools": {
                            "listChanged": False # We don't support notifications for tool list changes
                        }
                        # We don't support resources, but we'll handle the methods
                    }
                })
            elif method == "notifications/initialized":
                # This is just a notification, no response needed
                log_info("Received initialized notification")
                response = None  # No response needed for notifications
                
            elif method == "tools/list":
                log_info("Handling 'tools/list' method.")
                response = create_mcp_response(request_id, result={
                    "tools": [
                        {
                            "name": "query_journal",
                            "description": "Queries the personal journal entries using semantic search.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "The search query text."
                                    },
                                    "n_results": {
                                        "type": "number",
                                        "description": f"Number of results to return (default: {DEFAULT_N_RESULTS}).",
                                        "minimum": 1
                                    }
                                },
                                "required": ["query"]
                            }
                        },
                        {
                            "name": "update_index",
                            "description": "Updates the journal index with new or modified entries",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "full_reindex": {
                                        "type": "boolean",
                                        "description": "Whether to reindex all journal entries (true) or only new/modified ones (false)",
                                        "default": False
                                    }
                                }
                            }
                        }
                    ]
                })

            elif method == "resources/list":
                log_info("Handling 'resources/list' method.")
                # Return empty list if we don't have resources
                response = create_mcp_response(request_id, result={
                    "resources": []
                })
                
            elif method == "resources/templates/list":
                log_info("Handling 'resources/templates/list' method.")
                # Return empty list if we don't have resource templates
                response = create_mcp_response(request_id, result={
                    "templates": []
                })
                
            elif method == "tools/call":
                log_info("Handling 'tools/call' method.")
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                log_info(f"Tool name: {tool_name}, Arguments: {arguments}")

                if tool_name == "query_journal":
                    query = arguments.get("query")
                    n_results = arguments.get("n_results", DEFAULT_N_RESULTS)

                    if not query or not isinstance(query, str):
                        response = create_mcp_response(request_id, error=create_mcp_error(-32602, "Invalid params: 'query' argument is missing or not a string."))
                    elif not isinstance(n_results, int) or n_results < 1:
                         response = create_mcp_response(request_id, error=create_mcp_error(-32602, f"Invalid params: 'n_results' must be a positive integer (default: {DEFAULT_N_RESULTS})."))
                    else:
                        results, error_msg = perform_rag_query(query, n_results)
                        if error_msg:
                            response = create_mcp_response(request_id, error=create_mcp_error(-32000, f"Query execution failed: {error_msg}"))
                        else:
                            # Embed the list of results as a JSON string within the text content
                            response = create_mcp_response(request_id, result={
                                "content": [{
                                    "type": "text",
                                    "text": json.dumps(results, indent=2) # Pretty print for readability if needed
                                }]
                            })
                elif tool_name == "update_index":
                    full_reindex = arguments.get("full_reindex", False)
                    log_info(f"Updating index with full_reindex={full_reindex}")
                    
                    success, message = update_journal_index(full_reindex)
                    
                    if success:
                        response = create_mcp_response(request_id, result={
                            "content": [{
                                "type": "text",
                                "text": message
                            }]
                        })
                    else:
                        response = create_mcp_response(
                            request_id, 
                            error=create_mcp_error(-32000, f"Index update failed: {message}")
                        )
                else:
                    log_error(f"Unknown tool called: {tool_name}")
                    response = create_mcp_response(request_id, error=create_mcp_error(-32601, f"Method not found: Unknown tool '{tool_name}'"))

            else:
                 log_error(f"Unknown method received: {method}")
                 response = create_mcp_response(request_id, error=create_mcp_error(-32601, f"Method not found: Unknown method '{method}'"))

            if response:
                response_json = json.dumps(response)
                log_info(f"Prepared response for ID {request_id}: {response_json[:200]}...") # Log truncated response
                print(response_json, flush=True)
                log_info(f"Successfully sent response for request ID: {request_id}")
            elif method == "notifications/initialized":
                # This is expected for notifications that don't require responses
                log_info(f"No response needed for notification: {method}")
            else:
                log_error(f"No response generated for request ID: {request_id}, method: {method}")

        except json.JSONDecodeError:
            log_error(f"JSONDecodeError: Failed to decode JSON request: {line.strip()}")
            error_response = create_mcp_response(request_id, error=create_mcp_error(-32700, "Parse error: Invalid JSON received."))
            print(json.dumps(error_response), flush=True)
        except Exception as e:
            log_error(f"Unexpected error processing request: {e}")
            log_error(traceback.format_exc())
            error_response = create_mcp_response(request_id, error=create_mcp_error(-32000, f"Internal server error: {e}"))
            print(json.dumps(error_response), flush=True)

# --- Script Execution Guard ---
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_info("Server stopped by KeyboardInterrupt.")
    except Exception as e:
        log_error(f"Unhandled exception in main execution: {e}")
        log_error(traceback.format_exc())
        sys.exit(1) # Ensure non-zero exit code on unhandled error
    finally:
        log_info("Server process ending.")
