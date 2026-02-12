import os
import requests
from pathlib import Path
import chromadb
# from docling.document_converter import DocumentConverter

# Configuration
OLLAMA_API_BASE = "http://localhost:11434"
EMBEDDING_MODEL = "granite-embedding:30m"  # Small, fast embedding model
CHROMA_DB_PATH = "./chromadb_storage"

def get_embedding(text: str) -> list:
    """Get embeddings from Ollama"""
    try:
        response = requests.post(
            f"{OLLAMA_API_BASE}/api/embeddings",
            json={"model": EMBEDDING_MODEL, "prompt": text}
        )
        response.raise_for_status()
        return response.json()["embedding"]
    except Exception as e:
        print(f"Error getting embedding: {e}")
        raise

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """Simple chunking by character count with overlap"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        
        if chunk:  # Only add non-empty chunks
            chunks.append(chunk)
        
        start = end - overlap  # Move forward with overlap
    
    return chunks

def convert_to_markdown(file_path: str) -> str:
    """Extract text using PyMuPDF (fast and efficient)"""
    import fitz  # PyMuPDF
    
    print("  → Extracting text from document...")
    
    file_ext = Path(file_path).suffix.lower()
    
    # For plain text files
    if file_ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        print(f"  ✓ Extracted text ({len(text)} characters)")
        return text
    
    # For PDF files using PyMuPDF
    elif file_ext == '.pdf':
        text = ""
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text += page.get_text()
        doc.close()
        print(f"  ✓ Extracted text ({len(text)} characters)")
        return text
    
    # For other formats, fallback to Docling
    else:
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        result = converter.convert(file_path)
        markdown_text = result.document.export_to_markdown()
        print(f"  ✓ Converted to markdown ({len(markdown_text)} characters)")
        return markdown_text

def process_document(file_path: str):
    """
    Main indexing pipeline:
    1. Convert to markdown using PyMuPDF or Docling
    2. Chunk the text
    3. Generate embeddings with Ollama
    4. Store in ChromaDB
    """
    print(f"\n{'='*60}")
    print(f"Processing: {Path(file_path).name}")
    print(f"{'='*60}")
    
    # Step 1: Convert to markdown
    markdown_text = convert_to_markdown(file_path)
    
    # Step 2: Chunk the text
    print("  → Chunking text...")
    chunks = chunk_text(markdown_text)
    print(f"  ✓ Created {len(chunks)} chunks")
    
    # Step 3: Check if embedding model is available
    print(f"  → Checking embedding model ({EMBEDDING_MODEL})...")
    check_model = os.popen(f"ollama list | grep {EMBEDDING_MODEL}").read()
    if not check_model:
        print(f"  → Pulling {EMBEDDING_MODEL} model (first time only)...")
        os.system(f"ollama pull {EMBEDDING_MODEL}")
    
    # Step 4: Generate embeddings
    print("  → Generating embeddings...")
    embeddings = []
    for i, chunk in enumerate(chunks):
        if (i + 1) % 10 == 0 or i == 0:
            print(f"    Embedding chunk {i+1}/{len(chunks)}")
        embedding = get_embedding(chunk)
        embeddings.append(embedding)
    print(f"  ✓ Generated {len(embeddings)} embeddings")
    
    # Step 5: Store in ChromaDB
    print("  → Storing in ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection(name="documents")
    
    # Create unique IDs for each chunk
    doc_name = Path(file_path).stem
    ids = [f"{doc_name}_chunk_{i}" for i in range(len(chunks))]
    
    # Add to collection
    collection.add(
        embeddings=embeddings,
        documents=chunks,
        ids=ids,
        metadatas=[{"source": doc_name, "chunk_id": i} for i in range(len(chunks))]
    )
    
    print(f"  ✓ Stored {len(chunks)} chunks in database")
    print(f"\n{'='*60}")
    print(f"✓ Successfully indexed: {Path(file_path).name}")
    print(f"{'='*60}\n")

# For standalone testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python index.py <path_to_document>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File not found - {file_path}")
        sys.exit(1)
    
    process_document(file_path)