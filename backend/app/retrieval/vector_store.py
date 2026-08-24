import faiss
import numpy as np
import os
import pickle
import hashlib # 🆕 Added for deduplication
from datetime import datetime # 🆕 Added for recency tracking

_RETRIEVAL_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(_RETRIEVAL_DIR, "faiss.index")
META_PATH = os.path.join(_RETRIEVAL_DIR, "meta.pkl")

class VectorStore:
    def __init__(self, dimension: int):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.metadata = []
        # 🆕 We track unique content hashes to prevent the same info being added twice
        self.seen_hashes = set() 

    def add(self, vectors: np.ndarray, metadatas: list):
        """Adds data while checking for duplicates and adding timestamps."""
        new_vectors = []
        
        for i, meta in enumerate(metadatas):
            # 1️⃣ Deduplication: Create a unique 'fingerprint' of the text
            content_hash = hashlib.md5(meta["content"].encode()).hexdigest()
            
            if content_hash not in self.seen_hashes:
                # 2️⃣ Metadata Enrichment: Add a timestamp if it doesn't have one
                if "timestamp" not in meta:
                    meta["timestamp"] = datetime.now().strftime("%Y%m%d")
                
                # Mark this as the latest version by default
                meta["is_latest"] = True 
                
                self.seen_hashes.add(content_hash)
                self.metadata.append(meta)
                new_vectors.append(vectors[i])

        # 3️⃣ Only add to FAISS if there are actually new, unique items
        if new_vectors:
            new_vectors_np = np.array(new_vectors).astype("float32")
            faiss.normalize_L2(new_vectors_np)
            self.index.add(new_vectors_np)

    def search(self, query_vector: np.ndarray, k: int = 8):
        query_vector = np.array([query_vector]).astype("float32")
        faiss.normalize_L2(query_vector)

        distances, indices = self.index.search(query_vector, k)

        results = []
        for score, i in zip(distances[0], indices[0]):
            if i != -1 and i < len(self.metadata):
                meta = dict(self.metadata[i])
                # Attach similarity so downstream fusion can weigh by relevance
                meta["_dense_score"] = float(score)
                results.append(meta)

        return results

    def save(self):
        faiss.write_index(self.index, INDEX_PATH)
        # 🆕 We now save the hashes too so deduplication works after a restart
        data_to_save = {
            "metadata": self.metadata,
            "seen_hashes": self.seen_hashes
        }
        with open(META_PATH, "wb") as f:
            pickle.dump(data_to_save, f)

    def load(self):
        if os.path.exists(INDEX_PATH):
            self.index = faiss.read_index(INDEX_PATH)
        if os.path.exists(META_PATH):
            with open(META_PATH, "rb") as f:
                saved_data = pickle.load(f)
                # 🆕 Handle both old format and new format (with hashes)
                if isinstance(saved_data, dict):
                    self.metadata = saved_data.get("metadata", [])
                    self.seen_hashes = saved_data.get("seen_hashes", set())
                else:
                    self.metadata = saved_data
                    self.seen_hashes = set()