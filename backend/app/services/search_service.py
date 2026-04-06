from ..retrieval.search import search
from .llm_service import generate_answer

def run_search(query: str, history: list = None):
    """
    Enhanced search service that handles semantic retrieval 
    and passes conversation history to the LLM.
    """
    if history is None:
        history = []

    # 1️⃣ Retrieve relevant documents from vector store
    # We use k=5 to give the LLM enough text to find specific names/times
    results = search(query, k=5)

    # 2️⃣ Combine content from results into a single context block
    if not results:
        context = ""
    else:
        # Join the 'content' field of each retrieved document
        context = "\n\n".join([r["content"] for r in results])

    # 3️⃣ Generate AI answer via Groq, now passing the history
    # The LLM will use the history to understand what '0 period' refers to
    answer = generate_answer(query, context, history)

    return {
        "answer": answer,
        "sources": [
            {"url": r["url"]}
            for r in results 
        ]
    }