# backend/app/retrieval/search.py

from backend.app.retrieval.embedder import embed_text
from backend.app.retrieval.vector_store import VectorStore
from backend.app.retrieval.cache import SearchCache
import numpy as np



_sample_vector = embed_text("dimension_check")
_DIMENSION = len(_sample_vector)

_store = VectorStore(_DIMENSION)
_store.load()

_cache = SearchCache()


def search(query: str, k: int = 5):
    """
    Performs semantic search with caching.
    """

    
    cached = _cache.get(query)
    if cached:
        print("⚡ cache hit")
        return cached

    
    query_vector = embed_text(query)

    
    query_vector = query_vector / np.linalg.norm(query_vector)

    
    results = _store.search(query_vector, k)

    
    _cache.set(query, results)

    return results


if __name__ == "__main__":
    query = input("Enter search query: ")
    results = search(query)

    for r in results:
        print("\nURL:", r["url"])
        print("Type:", r["type"])
        print("Snippet:", r["content"][:300])
