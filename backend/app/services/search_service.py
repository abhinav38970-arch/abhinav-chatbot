from backend.app.retrieval.search import search
from backend.app.services.llm_service import generate_answer


def run_search(query: str):
    # 1️⃣ retrieve relevant documents
    results = search(query, k=10)

    # 2️⃣ combine context
    context = "\n\n".join([r["content"] for r in results])

    # 3️⃣ generate AI answer
    answer = generate_answer(query, context)

    return {
        "answer": answer,
        "sources": [
            {"url": r["url"]}
            for r in results
        ]
    }
