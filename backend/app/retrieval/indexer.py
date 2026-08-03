# backend/app/retrieval/indexer.py

from backend.app.database.db import SessionLocal
from backend.app.database.models import Page
from backend.app.retrieval.embedder import embed_text
from backend.app.retrieval.vector_store import VectorStore
from backend.app.retrieval.chunker import chunk_text
import numpy as np

def build_index():
    """
    ### Purpose: The "Bridge" between your Database and the AI Search.
    ### It reads the clean text, chunks it, converts it to math (vectors), 
    ### and saves it into the FAISS index files.
    """
    db = SessionLocal()

    # ### Pull every page we just scraped from the SQLite database.
    pages = db.query(Page).all()

    if not pages:
        print("No pages found in database. Run the scraper first!")
        return

    print(f"Found {len(pages)} pages. Creating embeddings...")

    # ### We create a "test" embedding to see how big the math vectors need to be.
    sample_vector = embed_text("test")
    dimension = len(sample_vector)

    # ### Initialize our VectorStore (FAISS) with the correct dimensions.
    store = VectorStore(dimension)

    vectors = []
    metadatas = []

    for page in pages:
        # ### Step 1: Break the page into smart chunks using our new chunker.
        chunks = chunk_text(page.content)

        for chunk_data in chunks:
            # Extract chunk content and metadata
            chunk = chunk_data["content"] if isinstance(chunk_data, dict) else chunk_data
            metadata = chunk_data.get("metadata", {}) if isinstance(chunk_data, dict) else {}
            
            # ### REMOVED: The < 50 character limit. 
            # ### We now keep small chunks so we don't lose room numbers or times.
            if not chunk.strip():
                continue

            # ### Step 2: Turn the text chunk into a list of numbers (Embedding).
            vector = embed_text(chunk)
            vectors.append(vector)

            # ### Step 3: Save the "Metadata" so the AI knows which URL this chunk came from.
            # Merge semantic metadata with page metadata
            combined_metadata = {
                "url": page.url,
                "type": page.type,
                "content": chunk,
                "school_year": page.school_year,
                "recency_score": page.recency_score,
                "is_current_year": bool(page.is_current_year),
                **metadata  # Add semantic metadata from smart chunking
            }
            metadatas.append(combined_metadata)

    # ### Step 4: Convert the list of vectors into a high-performance Numpy array.
    vectors = np.array(vectors)

    # ### Step 5: Add everything to FAISS and save the files to disk.
    store.add(vectors, metadatas)
    store.save()

    print(f"Index built successfully with {len(metadatas)} unique chunks.")
    db.close()

if __name__ == "__main__":
    build_index()