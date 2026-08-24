# backend/app/retrieval/indexer.py

from backend.app.database.db import SessionLocal
from backend.app.database.models import Page, Chunk, School
from backend.app.retrieval.embedder import embed_text
from backend.app.retrieval.vector_store import VectorStore
import numpy as np


def build_embedding_text(chunk: Chunk, page: Page, school: School) -> str:
    """
    Compose the text that gets embedded. Prepending school + title context makes
    vectors far more accurate ("bell schedule" from Washington vs Kennedy are
    distinguishable), and keeps retrieval grounded so the LLM is never confused.
    """
    parts = []
    if school and school.school_name:
        parts.append(school.school_name)
    elif page.school_id == "district":
        parts.append("Fremont Unified School District")
    else:
        parts.append(page.school_id)
    if page.title:
        parts.append(page.title)
    header = " | ".join(parts)
    return f"[{header}]\n{chunk.content}"


def build_index(batch_size: int = 64):
    """
    Bridge between the database and AI search.
    Reads chunks directly (already smart-chunked at scrape time — no double chunking),
    embeds them with school/title context, and saves into the FAISS index.
    """
    db = SessionLocal()
    try:
        query = (
            db.query(Chunk, Page, School)
            .join(Page, Chunk.page_id == Page.id)
            .outerjoin(School, Page.school_id == School.school_id)
            .order_by(Page.id, Chunk.chunk_index)
        )

        total_chunks = query.count()
        if total_chunks == 0:
            print("No chunks found in database. Run the scraper first!")
            return

        sample_vector = embed_text("test")
        dimension = len(sample_vector)
        store = VectorStore(dimension)

        vectors, metadatas = [], []
        processed = 0
        pages_seen = set()

        # Stream rows instead of loading all chunks in memory
        for chunk, page, school in query.yield_per(batch_size):
            embedding_text = build_embedding_text(chunk, page, school)
            vector = embed_text(embedding_text)
            vectors.append(vector)
            metadatas.append({
                "chunk_id": chunk.id,
                "page_id": page.id,
                "url": page.url,
                "title": page.title,
                "school_id": page.school_id,
                "school_name": school.school_name if school else page.school_id,
                "school_level": school.school_level if school else None,
                "page_type": page.page_type,
                "content": chunk.content,
                "semantic_role": chunk.semantic_role,
                "content_type": chunk.content_type,
                "school_year": page.school_year,
                "recency_score": page.recency_score,
                "is_current_year": bool(page.is_current_year),
            })
            pages_seen.add(page.id)

            processed += 1
            if processed % batch_size == 0:
                store.add(np.array(vectors).astype("float32"), metadatas)
                vectors, metadatas = [], []
                print(f"Embedded {processed}/{total_chunks} chunks "
                      f"({len(pages_seen)} pages)...")

        if vectors:
            store.add(np.array(vectors).astype("float32"), metadatas)

        store.save()
        print(f"✅ Index built successfully: {processed} unique chunks from "
              f"{len(pages_seen)} pages.")
    finally:
        db.close()


if __name__ == "__main__":
    build_index()
