# backend/app/retrieval/cache.py

import pickle
import os
import hashlib

CACHE_PATH = "backend/app/retrieval/search_cache.pkl"


class SearchCache:

    def __init__(self):
        if os.path.exists(CACHE_PATH):
            with open(CACHE_PATH, "rb") as f:
                self.cache = pickle.load(f)
        else:
            self.cache = {}

    def _hash(self, query: str):
        return hashlib.md5(query.encode()).hexdigest()

    def get(self, query: str):
        return self.cache.get(self._hash(query))

    def set(self, query: str, results):
        self.cache[self._hash(query)] = results
        with open(CACHE_PATH, "wb") as f:
            pickle.dump(self.cache, f)