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
    Performs semantic search with caching and recency prioritization.
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

    # TASK 3: RECENCY & RELEVANCE FILTERING - Sort by recency score and current year
    if results:
        # Enhanced sorting: prioritize current year content with high recency scores
        def sort_key(result):
            # Prioritize: current year > recency score > has metadata
            current_year_score = 2.0 if result.get("is_current_year") else 1.0
            recency_score = float(result.get("recency_score", 0.5))
            has_metadata = 1.0 if result.get("metadata") else 0.5
            
            # Combine scores: current_year * recency * metadata_quality
            return (-current_year_score * recency_score * has_metadata, 
                   -recency_score,  # Secondary sort by recency
                   result.get("timestamp", 0))  # Tertiary sort by timestamp
        
        results.sort(key=sort_key)
        
        # 🔧 TASK 1: FIXED - Relaxed filtering threshold to allow more valid results
        # Previous threshold (recency >= 0.3) was too strict and filtered out valid school data
        # New logic: Keep current year content regardless of recency, and be more lenient with older content
        filtered_results = []
        for result in results:
            is_current = result.get("is_current_year", False)
            recency = float(result.get("recency_score", 0.5))
            
            # Keep current year content regardless of recency score (most important)
            # For older content, use a lower threshold (0.15 instead of 0.3) to allow more valid results
            # Also ensure we don't filter out results that have no recency score (default to 0.5)
            if is_current or recency >= 0.15 or recency == 0.5:
                filtered_results.append(result)
        
        results = filtered_results

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