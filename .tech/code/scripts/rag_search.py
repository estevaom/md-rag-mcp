import os
import frontmatter  # For parsing Markdown YAML front matter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
import torch  # For GPU detection
from rich.console import Console  # For nice printing

# Initialize console for rich printing
console = Console()

# --- Configuration ---
# Get the project root directory (assuming script is in code/scripts/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Go up 3 levels
DATA_DIRECTORY = os.path.join(PROJECT_ROOT, "journal")
CHROMA_DB_PATH = os.path.join(PROJECT_ROOT, "code", "data", "chroma_db") # Adjusted path relative to new PROJECT_ROOT
CHROMA_COLLECTION_NAME = "life_journal_collection"
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
CHUNK_SIZE = 500  # Max characters per chunk
CHUNK_OVERLAP = 50  # Characters overlap between chunks


def load_markdown_docs(directory_path):
    """
    Recursively loads all Markdown files from the specified directory and its subdirectories,
    parsing YAML front matter.

    Args:
        directory_path (str): The path to the directory containing Markdown files.

    Returns:
        list: A list of frontmatter.Post objects, each containing metadata and content.
              Returns an empty list if the directory doesn't exist or contains no .md files.
    """
    documents = []
    if not os.path.isdir(directory_path):
        console.print(f"[bold red]Error: Directory not found:[/bold red] {directory_path}")
        return documents

    console.print(f"Scanning directory: [cyan]{directory_path}[/cyan]")
    found_files = False
    
    # Walk through directory and subdirectories
    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            if filename.endswith(".md"):
                found_files = True
                filepath = os.path.join(root, filename)
                # Get relative path from the base directory for better source identification
                rel_path = os.path.relpath(filepath, directory_path)
                
                try:
                    post = frontmatter.load(filepath)
                    # Add filename and path to metadata for later reference
                    if 'source' not in post.metadata:
                        post.metadata['source'] = rel_path
                    documents.append(post)
                    console.print(f"  [green]Loaded:[/green] {rel_path}")
                except Exception as e:
                    console.print(f"  [bold red]Error loading {rel_path}:[/bold red] {e}")

    if not found_files:
        console.print(f"[yellow]Warning: No .md files found in {directory_path} or its subdirectories[/yellow]")

    return documents


def split_docs(documents):
    """
    Splits the content of loaded documents into smaller chunks.

    Args:
        documents (list): A list of frontmatter.Post objects.

    Returns:
        list: A list of dictionaries, where each dictionary represents a chunk
              and contains 'text' and 'metadata' (including source).
    """
    console.print("\nSplitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
    )

    all_chunks = []
    for doc in documents:
        chunks = text_splitter.split_text(doc.content)
        for i, chunk_text in enumerate(chunks):
            # Create a unique ID for the chunk based on source and index
            chunk_id = f"{doc.metadata.get('source', 'unknown')}_{i}"
            chunk_metadata = doc.metadata.copy() # Start with original metadata
            chunk_metadata['chunk_index'] = i
            chunk_metadata['chunk_id'] = chunk_id # Store ID in metadata too

            all_chunks.append({
                "id": chunk_id, # ID for ChromaDB
                "text": chunk_text,
                "metadata": chunk_metadata
            })
            # console.print(f"  Created chunk {chunk_id} from {doc.metadata.get('source', 'unknown')}") # Can be verbose

    console.print(f"  Split into {len(all_chunks)} chunks.")
    return all_chunks


def initialize_embedding_model(model_name):
    """Initializes and returns the Sentence Transformer model with GPU support if available."""
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

def initialize_vector_store(db_path, collection_name):
    """Initializes and returns the ChromaDB client and collection."""
    console.print(f"\nInitializing vector store at: [cyan]{db_path}[/cyan]")
    try:
        chroma_client = chromadb.PersistentClient(path=db_path)
        
        # Get the collection if it exists, or create it if it doesn't
        collection = chroma_client.get_or_create_collection(name=collection_name)
        console.print(f"  [green]Ensured vector store collection '{collection_name}' exists.[/green]")
        return collection
    except Exception as e:
        console.print(f"[bold red]Error initializing vector store:[/bold red] {e}")
        return None

def index_chunks(collection, chunks, embedding_model):
    """Generates embeddings and indexes chunks in the vector store."""
    if not collection or not chunks or not embedding_model:
        console.print("[bold red]Error: Cannot index chunks due to missing components.[/bold red]")
        return False

    console.print(f"\nIndexing {len(chunks)} chunks...")
    # Prepare data for ChromaDB batch insertion
    ids = [chunk['id'] for chunk in chunks]
    documents = [chunk['text'] for chunk in chunks]
    
    # Process metadata to ensure all values are of compatible types (str, int, float, bool)
    processed_metadatas = []
    for chunk in chunks:
        processed_metadata = {}
        for key, value in chunk['metadata'].items():
            # Convert any non-compatible types to strings
            if isinstance(value, (str, int, float, bool)):
                processed_metadata[key] = value
            else:
                processed_metadata[key] = str(value)
        processed_metadatas.append(processed_metadata)
    
    metadatas = processed_metadatas

    try:
        console.print("  Generating embeddings (this may take a moment)...")
        embeddings = embedding_model.encode(documents, show_progress_bar=True)
        console.print("  Embeddings generated.")

        console.print(f"  Adding {len(ids)} items to collection '{collection.name}'...")
        # Use upsert to add new or update existing chunks by ID
        collection.upsert(
            ids=ids,
            embeddings=embeddings.tolist(), # Convert numpy array to list
            documents=documents,
            metadatas=metadatas
        )
        console.print("  [green]Chunks indexed successfully.[/green]")
        return True
    except Exception as e:
        console.print(f"[bold red]Error during indexing:[/bold red] {e}")
        return False


def query_rag(collection, embedding_model, query_text, n_results=3):
    """
    Queries the vector store for chunks similar to the query text.

    Args:
        collection: The ChromaDB collection object.
        embedding_model: The initialized Sentence Transformer model.
        query_text (str): The user's query.
        n_results (int): The number of results to retrieve.

    Returns:
        dict: A dictionary containing the query results (ids, documents, metadatas, distances),
              or None if an error occurs.
    """
    if not collection or not embedding_model or not query_text:
        console.print("[bold red]Error: Cannot query due to missing components.[/bold red]")
        return None

    try:
        console.print(f"\n  Generating embedding for query: '{query_text}'")
        # Ensure query_text is handled correctly if empty or invalid
        if not isinstance(query_text, str) or not query_text.strip():
             console.print("[yellow]Warning: Empty query provided.[/yellow]")
             return None
        query_embedding = embedding_model.encode([query_text.strip()]) # Encode expects a list, strip whitespace

        console.print(f"  Querying collection '{collection.name}' for {n_results} results...")
        results = collection.query(
            query_embeddings=query_embedding.tolist(), # Convert numpy array to list
            n_results=n_results,
            include=['documents', 'metadatas', 'distances'] # Include distances for relevance check
        )
        console.print("  [green]Query successful.[/green]")
        return results
    except Exception as e:
        # Log the full exception for debugging
        import traceback
        console.print(f"[bold red]Error during query:[/bold red]\n{traceback.format_exc()}")
        return None


# --- Main Execution ---
if __name__ == "__main__":
    console.print("[bold blue]=== Starting Journal RAG Search ===[/bold blue]")

    # 1. Load Documents
    loaded_docs = load_markdown_docs(DATA_DIRECTORY)
    if not loaded_docs:
        console.print("[bold red]No documents loaded. Exiting.[/bold red]")
        exit() # Exit if loading failed

    console.print(f"\n[bold green]Successfully loaded {len(loaded_docs)} documents.[/bold green]")

    # 2. Split Documents
    doc_chunks = split_docs(loaded_docs)
    if not doc_chunks:
        console.print("[bold red]Failed to split documents into chunks. Exiting.[/bold red]")
        exit() # Exit if splitting failed

    # 3. Initialize Models & Vector Store
    embed_model = initialize_embedding_model(EMBEDDING_MODEL_NAME)
    chroma_collection = initialize_vector_store(CHROMA_DB_PATH, CHROMA_COLLECTION_NAME)

    if not embed_model or not chroma_collection:
        console.print("[bold red]Failed to initialize models or vector store. Exiting.[/bold red]")
        exit() # Exit if initialization failed

    # 4. Index Chunks
    indexing_successful = index_chunks(chroma_collection, doc_chunks, embed_model)

    if indexing_successful:
        console.print("\n[bold green]Indexing complete.[/bold green]")

        # 5. Querying
        console.print("\n--- Query Test ---")
        while True:
            query = input("Enter your query (or type 'quit' to exit): ")
            if query.lower() == 'quit':
                break
            if not query:
                continue

            results = query_rag(chroma_collection, embed_model, query, n_results=3) # Call the function

            console.print("\n[bold magenta]Query Results:[/bold magenta]")
            # Check results structure carefully based on ChromaDB's actual return format
            # Check if results exist and have the expected keys/structure
            if results and results.get('ids') and results['ids'] and results['ids'][0]:
                if not results.get('documents') or not results['documents'][0]: # Handle case where query returns no documents
                     console.print("  No relevant results found.")
                     continue

                for i, res_doc in enumerate(results['documents'][0]):
                    # Safely access potentially missing keys/indices
                    distance = results.get('distances', [[None]])[0][i]
                    metadata = results.get('metadatas', [[{}]])[0][i]
                    source = metadata.get('source', 'N/A')

                    distance_str = f"{distance:.4f}" if distance is not None else "N/A"
                    console.print(f"  [cyan]Result {i+1} (Distance: {distance_str}):[/cyan]")
                    console.print(f"    [dim]Source: {source}[/dim]")
                    console.print(f"    {res_doc}")
            elif results is None:
                 console.print("  An error occurred during the query.")
            else:
                # This handles cases where results is not None, but 'ids' or 'documents' might be empty lists or missing
                console.print("  No relevant results found.")


    else:
        console.print("[bold red]Indexing failed. Check errors above.[/bold red]")


    console.print("\n[bold blue]=== Journal RAG Search Finished ===[/bold blue]")
