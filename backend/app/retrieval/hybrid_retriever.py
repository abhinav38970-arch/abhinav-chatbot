"""
Hybrid retriever for the district-wide RAG pipeline.

Combines three signals that pure vector search misses:
  1. Dense semantic search (existing FAISS store)
  2. Persistent BM25 keyword search (exact matches: policy numbers, staff names,
     course codes — built ONCE from the DB, not per query)
  3. School routing (detects which school the question is about and prioritizes
     that school's content so answers never mix schools)

Fusion uses Reciprocal Rank Fusion (RRF) with a gentle recency boost.
"""

import os
import re
import pickle
from typing import List, Optional, Tuple

import numpy as np
from rank_bm25 import BM25Okapi

from backend.app.logs.logger import logger
from backend.app.config import SCHOOL_CONFIG
from backend.app.database.db import SessionLocal
from backend.app.database.models import Chunk, Page, School

_RETRIEVAL_DIR = os.path.dirname(os.path.abspath(__file__))
BM25_PATH = os.path.join(_RETRIEVAL_DIR, "bm25_index.pkl")
FAISS_META_PATH = os.path.join(_RETRIEVAL_DIR, "meta.pkl")
SEARCH_CACHE_PATH = os.path.join(_RETRIEVAL_DIR, "search_cache.pkl")

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "of", "to",
    "in", "on", "at", "for", "and", "or", "do", "does", "did", "what", "when",
    "where", "who", "how", "why", "can", "i", "my", "our", "you", "your",
    "it", "its", "this", "that", "with", "as", "by", "from", "about",
}

RRF_K = 60


def _tokenize(text: str) -> List[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS]


# ---------------------------------------------------------------------------
# School routing: map natural-language mentions to school_ids
# ---------------------------------------------------------------------------

class SchoolRouter:
    def __init__(self):
        # alias (lowercase phrase) -> school_id ; longer aliases win
        self.alias_to_school = {}
        for school in SCHOOL_CONFIG.schools:
            sid = school["school_id"]
            phrases = set(school.get("query_patterns", []))
            phrases.add(school["school_name"].lower())
            phrases.add(sid.replace("-", " "))
            for p in phrases:
                if p and len(p) >= 3:
                    self.alias_to_school[p.lower()] = sid
        # longest aliases first so "mission san jose elementary" beats "mission san jose"
        self._aliases_sorted = sorted(self.alias_to_school.keys(), key=len, reverse=True)

    def detect(self, query: str) -> Optional[str]:
        q = f" {query.lower().strip()} "
        for alias in self._aliases_sorted:
            if f" {alias} " in q or alias in q:
                return self.alias_to_school[alias]
        return None


# ---------------------------------------------------------------------------
# Hybrid retriever
# ---------------------------------------------------------------------------

class HybridRetriever:
    _instance = None

    @classmethod
    def instance(cls) -> "HybridRetriever":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        from backend.app.retrieval.vector_store import VectorStore
        from backend.app.retrieval.embedder import embed_text

        self._embed = embed_text
        sample = embed_text("dimension_check")
        self._store = VectorStore(len(sample))
        self._store.load()

        self.router = SchoolRouter()
        self._bm25 = None
        self._bm25_docs = []
        self._load_bm25()

    # ---------------- BM25 index (persistent) ----------------

    def _db_chunk_count(self) -> int:
        db = SessionLocal()
        try:
            return db.query(Chunk.id).count()
        finally:
            db.close()

    def _invalidate_query_cache(self):
        """Query cache is invalid whenever the FAISS metadata was rebuilt."""
        try:
            if os.path.exists(FAISS_META_PATH) and os.path.exists(SEARCH_CACHE_PATH):
                if os.path.getmtime(FAISS_META_PATH) > os.path.getmtime(SEARCH_CACHE_PATH):
                    os.remove(SEARCH_CACHE_PATH)
                    logger.info("🧹 Cleared stale search cache")
        except OSError:
            pass

    def _load_bm25(self):
        db_count = self._db_chunk_count()
        self._invalidate_query_cache()

        if os.path.exists(BM25_PATH):
            try:
                with open(BM25_PATH, "rb") as f:
                    payload = pickle.load(f)
                if payload.get("n_chunks") == db_count and payload.get("docs"):
                    self._bm25 = payload["bm25"]
                    self._bm25_docs = payload["docs"]
                    logger.info(f"📚 Loaded persistent BM25 index ({db_count} chunks)")
                    return
                logger.info(f"🔄 BM25 index stale ({payload.get('n_chunks')} vs {db_count}) - rebuilding")
            except Exception:
                logger.exception("BM25 load failed - rebuilding")

        self._build_bm25(db_count)

    def _build_bm25(self, expected_count: int):
        db = SessionLocal()
        docs = []
        try:
            rows = (
                db.query(Chunk, Page)
                .join(Page, Chunk.page_id == Page.id)
                .yield_per(500)
            )
            for chunk, page in rows:
                docs.append({
                    "chunk_id": chunk.id,
                    "content": chunk.content,
                    "url": page.url,
                    "title": page.title or "",
                    "school_id": page.school_id,
                    "recency_score": page.recency_score if page.recency_score is not None else 0.5,
                    "is_current_year": bool(page.is_current_year),
                    "semantic_role": chunk.semantic_role or "unknown",
                    "page_type": page.page_type,
                })
        finally:
            db.close()

        if not docs:
            logger.warning("⚠️ No chunks in DB - BM25 index empty")
            return

        corpus = [_tokenize(d["content"]) for d in docs]
        bm25 = BM25Okapi(corpus)

        with open(BM25_PATH, "wb") as f:
            pickle.dump({"n_chunks": len(docs), "bm25": bm25, "docs": docs}, f)

        self._bm25 = bm25
        self._bm25_docs = docs
        logger.info(f"📚 Built persistent BM25 index over {len(docs)} chunks "
                    f"(saved to {BM25_PATH})")

    def rebuild(self):
        """Force a full BM25 rebuild (call after a new crawl + index build)."""
        self._build_bm25(self._db_chunk_count())

    # ---------------- Retrieval ----------------

    def detect_school(self, query: str) -> Optional[str]:
        return self.router.detect(query)

    def retrieve(self, query: str, k: int = 8,
                 school_hint: Optional[str] = None) -> Tuple[List[dict], Optional[str]]:
        """
        Returns (results, detected_school).
        Each result dict: content, url, title, school_id, recency_score,
        is_current_year, semantic_role, page_type, fused_score.

        school_hint: optional school_id from the UI profile — biases retrieval
        when the user didn't name a school in the question itself.
        """
        detected_school = self.router.detect(query) or school_hint

        candidates = {}   # key -> {"doc":..., "rrf": float}

        def add(doc, rank, weight=1.0):
            key = doc.get("chunk_id") or hash(doc["content"])
            entry = candidates.setdefault(key, {"doc": doc, "rrf": 0.0})
            entry["rrf"] += weight / (RRF_K + rank)

        # 1. Dense semantic results
        try:
            qvec = self._embed(query)
            dense = self._store.search(qvec, k * 4)
            for rank, meta in enumerate(dense):
                add(meta, rank)
        except Exception:
            logger.exception("Dense search failed")

        # 2. BM25 keyword results
        if self._bm25 is not None and self._bm25_docs:
            try:
                scores = self._bm25.get_scores(_tokenize(query))
                top_idx = np.argsort(scores)[::-1][: k * 4]
                for rank in top_idx:
                    if scores[rank] <= 0:
                        break
                    add(self._bm25_docs[int(rank)], rank)
            except Exception:
                logger.exception("BM25 search failed")

        # 3. School-aware filtering + recency boost
        ranked = sorted(candidates.values(), key=lambda e: e["rrf"], reverse=True)

        if detected_school:
            on_target = [e for e in ranked
                         if e["doc"].get("school_id") in (detected_school, "district")]
            off_target = [e for e in ranked
                          if e["doc"].get("school_id") not in (detected_school, "district")]
            # Only exclude other schools when we have enough on-target material;
            # otherwise keep everything but let ranking sort it out
            if len(on_target) >= min(k, 4):
                ranked = on_target + []
            else:
                ranked = on_target + off_target

        results = []
        for e in ranked[:k]:
            doc = dict(e["doc"])
            recency = float(doc.get("recency_score") or 0.5)
            boost = 1.0 + 0.3 * recency + (0.2 if doc.get("is_current_year") else 0.0)
            doc["fused_score"] = round(e["rrf"] * boost, 6)
            doc["detected_school"] = detected_school
            results.append(doc)

        return results, detected_school


if __name__ == "__main__":
    r = HybridRetriever.instance()
    while True:
        q = input("\nQuery (empty to quit): ").strip()
        if not q:
            break
        res, school = r.retrieve(q, k=5)
        print(f"🎯 Detected school: {school}")
        for d in res:
            print(f"  [{d['school_id']}] {d['title'][:50]} | role={d['semantic_role']} "
                  f"| score={d['fused_score']:.4f}")
            print(f"      {d['content'][:120].replace(chr(10), ' ')}")
