# backend/app/retrieval/vector_store.py

import faiss
import numpy as np
import os
import pickle

INDEX_PATH = "backend/app/retrieval/faiss.index"
META_PATH = "backend/app/retrieval/meta.pkl"


class VectorStore:
    def __init__(self, dimension: int):
        self.dimension = dimension

       
        self.index = faiss.IndexFlatIP(dimension)

        self.metadata = []

    def add(self, vectors: np.ndarray, metadatas: list):
        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        self.metadata.extend(metadatas)

    def search(self, query_vector: np.ndarray, k: int = 8):
        query_vector = np.array([query_vector]).astype("float32")
        faiss.normalize_L2(query_vector)

        distances, indices = self.index.search(query_vector, k)

        results = []
        for i in indices[0]:
            if i < len(self.metadata):
                results.append(self.metadata[i])

        return results

    def save(self):
        faiss.write_index(self.index, INDEX_PATH)
        with open(META_PATH, "wb") as f:
            pickle.dump(self.metadata, f)

    def load(self):
        if os.path.exists(INDEX_PATH):
            self.index = faiss.read_index(INDEX_PATH)

        if os.path.exists(META_PATH):
            with open(META_PATH, "rb") as f:
                self.metadata = pickle.load(f)
