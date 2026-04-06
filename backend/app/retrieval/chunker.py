# backend/app/retrieval/chunker.py
from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text(text, chunk_size=600, overlap=100):
    """
    ### Purpose: Uses the 'langchain-text-splitters' library to smartly split text.
    ### It prioritizes keeping paragraphs and sentences together so the AI 
    ### doesn't lose context mid-sentence.
    """
    # If there's no text or it's tiny, return as is
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    # Initialize the "Smart Engine"
    # It tries to split by the first separator, and if the result is still too big, 
    # it moves to the next one in the list.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    # Returns a list of strings, perfectly compatible with your indexer.py
    return splitter.split_text(text)