# backend/app/retrieval/vector_store.py

import faiss
import numpy as np
import os
import pickle

INDEX_PATH = "backend/app/retrieval/faiss.index"
META_PATH = "backend/app/retrieval/meta.pkl"

class VectorStore:
    def __init__(self, dimension: int):
        """### Purpose: Manages the FAISS index, which is like a 'Math Map' of your data."""
        self.dimension = dimension
        # ### IndexFlatIP uses 'Inner Product' (similarity) to find the best match.
        self.index = faiss.IndexFlatIP(dimension)
        # ### Stores the actual text that matches the math vectors.
        self.metadata = []

    def add(self, vectors: np.ndarray, metadatas: list):
        """### Normalizes the math and adds the new data to the index."""
        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        self.metadata.extend(metadatas)

    def search(self, query_vector: np.ndarray, k: int = 8):
        """### Purpose: Finds the 'K' most similar chunks to the user's question."""
        query_vector = np.array([query_vector]).astype("float32")
        faiss.normalize_L2(query_vector)

        # ### Perform the actual math search in FAISS.
        distances, indices = self.index.search(query_vector, k)

        results = []
        for i in indices[0]:
            # ### If FAISS finds a match, we pull the text out of our metadata list.
            if i != -1 and i < len(self.metadata):
                results.append(self.metadata[i])

        return results

    def save(self):
        """### Writes the math index and the text metadata to files."""
        faiss.write_index(self.index, INDEX_PATH)
        with open(META_PATH, "wb") as f:
            pickle.dump(self.metadata, f)

    def load(self):
        """### Loads the existing index from the disk so we don't have to re-scrape."""
        if os.path.exists(INDEX_PATH):
            self.index = faiss.read_index(INDEX_PATH)
        if os.path.exists(META_PATH):
            with open(META_PATH, "rb") as f:
                self.metadata = pickle.load(f)