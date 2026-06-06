# backend/app/retrieval/embedder.py

from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_text(text: str) -> np.ndarray:
    """
    Convert text into vector embedding.
    """
    embedding = model.encode(
        text,
        normalize_embeddings=True  
    )

    return np.array(embedding).astype("float32")
