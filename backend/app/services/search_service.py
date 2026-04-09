# backend/app/services/search_service.py
from ..retrieval.search import search, all_documents
from .llm_service import generate_answer
from rank_bm25 import BM25Okapi
from flashrank import Ranker, RerankRequest

# Initialize the Re-ranker once
ranker = Ranker()

def run_search(query: str, history: list = None, scope: str = "district"):
    if history is None:
        history = []

    user_query = query.lower()
    schedule_context = ""

    # 🕒 1. HARDCODED MASTER SCHEDULE
    if any(word in user_query for word in ["schedule", "times", "period", "dismissal", "lunch", "break"]):
        schedule_context = """
        WASHINGTON HIGH SCHOOL MASTER BELL SCHEDULE (2025-2026):
        REGULAR SCHEDULE (Mon, Thu, Fri):
        - 0 Period: 7:30 - 8:20 | Period 1: 8:30 - 9:22 | Period 2: 9:28 - 10:20
        - Break: 10:20 - 10:26 | Husky/Flex: 10:32 - 11:04 | Period 3: 11:10 - 12:02
        - Period 4: 12:08 - 1:00 | Lunch: 1:00 - 1:30 | Period 5: 1:36 - 2:28 | Period 6: 2:34 - 3:26
        """

    # 2️⃣ STEP 2: HYBRID SEARCH (Removed filter_metadata to fix TypeError)
    vector_results = search(query, k=10)
    
    # Using all_documents for BM25 to ensure it runs locally without scope errors
    filtered_docs = all_documents if all_documents else []
    
    if not filtered_docs:
        keyword_results_raw = []
    else:
        tokenized_corpus = [doc["content"].split() for doc in filtered_docs]
        bm25 = BM25Okapi(tokenized_corpus)
        keyword_results_raw = bm25.get_top_n(query.split(), filtered_docs, n=5)

    # 3️⃣ STEP 3: BLEND & RE-RANK
    combined_dict = {res["content"]: res for res in (vector_results + keyword_results_raw)}
    combined_list = list(combined_dict.values())
    
    passages = [{"id": i, "text": res["content"], "meta": res} for i, res in enumerate(combined_list)]
    
    rerank_request = RerankRequest(query=query, passages=passages)
    reranked = ranker.rerank(rerank_request)

    top_results = [r["meta"] for r in reranked[:3]]

    # 4️⃣ STEP 4: PREPARE CONTEXT & SOURCES
    if not top_results and not schedule_context:
        context = "No specific school data found."
        sources = []
    else:
        web_context = "\n\n".join([r["content"] for r in top_results])
        context = f"{schedule_context}\n\n{web_context}".strip()
        sources = list(set([str(r.get("url")) for r in top_results if r.get("url")]))

    # 5️⃣ STEP 5: GENERATE ANSWER
    answer = generate_answer(query, context, history)

    return {
        "answer": answer,
        "sources": sources
    }