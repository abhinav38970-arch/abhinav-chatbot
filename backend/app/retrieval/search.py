# backend/app/retrieval/search.py

from backend.app.retrieval.embedder import embed_text
from backend.app.retrieval.vector_store import VectorStore
from backend.app.retrieval.cache import SearchCache
import numpy as np

# Initialize once (not per request)
_sample_vector = embed_text("dimension_check")
_DIMENSION = len(_sample_vector)

_store = VectorStore(_DIMENSION)
_store.load()

_cache = SearchCache()

# --- 🆕 ADDED FOR ADVANCED RAG (Fixed for your file structure) ---
faiss_index = _store.index

# We check if it's named 'metadata' (from your meta.pkl) or 'documents'
if hasattr(_store, 'metadata'):
    all_documents = _store.metadata
else:
    # Fallback to .documents if metadata doesn't exist
    all_documents = getattr(_store, 'documents', [])
# ---------------------------------------------------------------

def search(query: str, k: int = 5):
    """
    Performs semantic search with caching.
    """

    # 1️⃣ Check cache first
    cached = _cache.get(query)
    if cached:
        print("⚡ cache hit")
        return cached

    # 2️⃣ Embed query
    query_vector = embed_text(query)

    # 3️⃣ Normalize vector (important for cosine-style similarity)
    norm = np.linalg.norm(query_vector)
    if norm > 0:
        query_vector = query_vector / norm

    # 4️⃣ Perform FAISS search
    results = _store.search(query_vector, k)

    # 5️⃣ Store in cache
    _cache.set(query, results)

    return results


if __name__ == "__main__":
    query = input("Enter search query: ")
    results = search(query)

    for r in results:
        print("\nURL:", r["url"])
        print("Type:", r["type"])
        print("Snippet:", r["content"][:300])