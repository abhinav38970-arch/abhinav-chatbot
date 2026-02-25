# backend/app/retrieval/chunker.py

def chunk_text(text, chunk_size=500, overlap=100):
    """
    Split text into overlapping chunks for better search precision.
    """

    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks