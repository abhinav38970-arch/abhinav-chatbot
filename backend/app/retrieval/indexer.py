# backend/app/retrieval/indexer.py

from backend.app.database.db import SessionLocal
from backend.app.database.models import Page
from backend.app.retrieval.embedder import embed_text
from backend.app.retrieval.vector_store import VectorStore
from backend.app.retrieval.chunker import chunk_text
import numpy as np

def build_index():
    db = SessionLocal()
    pages = db.query(Page).all()

    if not pages:
        print("No pages found in database. Run the scraper first!")
        return

    print(f"Found {len(pages)} pages. Creating embeddings...")

    sample_vector = embed_text("test")
    dimension = len(sample_vector)
    store = VectorStore(dimension)

    vectors = []
    metadatas = []

    for page in pages:
        chunks = chunk_text(page.content)

        for chunk in chunks:
            if not chunk.strip():
                continue

            vector = embed_text(chunk)
            vectors.append(vector)

            # ### UPDATED: Added category so the 'Bouncer' can filter results
            metadatas.append({
                "url": page.url,
                "type": page.type,
                "content": chunk,
                "category": page.category  # <--- CRITICAL ADDITION
            })

    vectors = np.array(vectors)
    store.add(vectors, metadatas)
    store.save()

    print(f"Index built successfully with {len(metadatas)} unique chunks.")
    db.close()

if __name__ == "__main__":
    build_index()