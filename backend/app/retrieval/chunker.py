# backend/app/retrieval/chunker.py

def chunk_text(text, chunk_size=600, overlap=100):
    """
    ### Purpose: Splits long text into smaller pieces for the AI to read.
    ### Instead of cutting mid-word, it looks for double newlines (paragraphs) 
    ### or periods (sentences) to keep information together.
    """
    # ### If the text is already small, don't bother chunking it.
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    # ### We split by newlines first because school data (schedules/lists) 
    # ### relies heavily on line breaks to make sense.
    paragraphs = text.split("\n\n")
    current_chunk = ""

    for para in paragraphs:
        # ### If adding this paragraph stays under our limit, keep building the chunk.
        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += para + "\n\n"
        else:
            # ### Once full, save the chunk and start a new one.
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # ### If a single paragraph is giant, we have to force-cut it by characters.
            if len(para) > chunk_size:
                start = 0
                while start < len(para):
                    chunks.append(para[start : start + chunk_size])
                    start += chunk_size - overlap
                current_chunk = ""
            else:
                current_chunk = para + "\n\n"

    # ### Add the final remaining piece of text.
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks