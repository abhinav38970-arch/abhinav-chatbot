# backend/app/retrieval/search.py

from backend.app.retrieval.embedder import embed_text
from backend.app.retrieval.vector_store import VectorStore
from backend.app.retrieval.cache import SearchCache


def search(query: str, k: int = 5):
    cache = SearchCache()

    # ✅ check cache first
    cached = cache.get(query)
    if cached:
        print("⚡ cache hit")
        return cached

    # convert query → vector
    query_vector = embed_text(query)

    # determine vector size
    sample_vector = embed_text("test")
    dimension = len(sample_vector)

    # load FAISS index
    store = VectorStore(dimension)
    store.load()

    # perform semantic search
    results = store.search(query_vector, k)

    # ✅ store in cache
    cache.set(query, results)

    return results


if __name__ == "__main__":
    query = input("Enter search query: ")
    results = search(query)

    for r in results:
        print("\nURL:", r["url"])
        print("Type:", r["type"])
        print("Snippet:", r["content"][:300])