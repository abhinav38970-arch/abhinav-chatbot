# backend/app/services/search_service.py
import re
from .llm_service import generate_answer
from flashrank import Ranker, RerankRequest
from backend.app.retrieval.hybrid_retriever import HybridRetriever
from rank_bm25 import BM25Okapi
from backend.app.safety.guardrails import guard_input, guard_output
from backend.app.safety.pii_filter import scrub_outbound
from backend.app.logs.logger import logger

# Initialize the Re-ranker once
ranker = Ranker()
retriever = HybridRetriever.instance()

GREETING_PATTERNS = [
    r'\bhi\b', r'\bhello\b', r'\bhey\b', r'\bhow are you\b',
    r'\bgood morning\b', r'\bgood afternoon\b', r'\bgreetings\b'
]


def _is_greeting(user_query: str) -> bool:
    return any(re.search(p, user_query) for p in GREETING_PATTERNS)


def find_similar_queries(query: str) -> str:
    """Suggest related topics from the corpus when nothing relevant is found."""
    try:
        docs = retriever._bm25_docs or []
        if not docs:
            return "No similar topics found."
        bm25 = BM25Okapi([d["content"].split() for d in docs[:5000]])
        similar = bm25.get_top_n(query.split(), docs[:5000], n=3)
        lines = []
        for doc in similar:
            first = doc["content"].split('.')[0][:100]
            school = doc.get("school_id", "")
            lines.append(f"- [{school}] {first.strip()}...")
        return "\n".join(lines) if lines else "No similar topics found."
    except Exception:
        return "No similar topics found."


def run_search(query: str, history: list = None, school_hint: str = None):
    if history is None:
        history = []

    user_query = query.lower().strip()

    # 🛡️ SAFETY LAYER 1: input guardrails (injection, jailbreaks, harmful asks)
    decision = guard_input(query)
    if not decision.allowed:
        logger.info(f"🛡️ Blocked input ({decision.category})")
        return {"answer": decision.user_message, "sources": []}

    # 👋 Greeting & intent router (district-wide persona)
    if _is_greeting(user_query) and len(user_query.split()) <= 4:
        return {
            "answer": (
                "🐾 Welcome to Husky AI! I'm your Fremont Unified School District assistant, "
                "covering every FUSD school and district office.\n\n"
                "I can help with:\n"
                "- 🕒 Bell schedules and class times\n"
                "- 📅 Events, calendars, and activities\n"
                "- 📚 Academic programs and resources\n"
                "- 🏫 Policies and procedures\n"
                "- 👥 Staff and department contacts\n\n"
                "Just mention any school by name — Washington, Kennedy, Irvington, "
                "Mission San Jose, Horner, Weibel, and more."
            ),
            "sources": []
        }

    # 1️⃣ HYBRID RETRIEVAL: dense (FAISS) + keyword (persistent BM25),
    #    fused with RRF, routed to the detected school (or UI profile hint)
    results, detected_school = retriever.retrieve(query, k=12, school_hint=school_hint)

    if not results:
        similar = find_similar_queries(query)
        return {
            "answer": (
                "I couldn't find information about that in the FUSD database.\n\n"
                f"Topics you might find helpful:\n{similar}\n\n"
                "For the most accurate details, please check the official "
                "Fremont Unified School District website or contact the school office."
            ),
            "sources": ["https://fremontunified.org"]
        }

    # 2️⃣ CROSS-ENCODER RE-RANK the fused candidates for final precision
    passages = [{"id": i, "text": r["content"], "meta": r} for i, r in enumerate(results)]
    try:
        reranked = ranker.rerank(RerankRequest(query=query, passages=passages))
        top_results = [r["meta"] for r in reranked[:6]]
    except Exception:
        logger.exception("Reranker failed - using fused ranking")
        top_results = results[:6]

    # 3️⃣ BUILD LABELED CONTEXT so the LLM always knows which school each fact belongs to
    context_blocks = []
    seen_urls = set()
    for i, res in enumerate(top_results, 1):
        school_name = res.get("school_name") or res.get("school_id") or "FUSD"
        title = (res.get("title") or "").strip() or "Untitled Page"
        url = res.get("url", "")
        role = res.get("semantic_role", "unknown")
        context_blocks.append(
            f"### SOURCE {i} — {school_name}\n"
            f"Page: {title} | Type: {res.get('page_type', 'html')} | Topic: {role}\n"
            f"URL: {url}\n"
            f"{res['content']}"
        )
        if url:
            seen_urls.add(url)

    context = "\n\n".join(context_blocks)

    routing_note = ""
    if detected_school:
        routing_note = f"The user's question appears to be about school ID '{detected_school}'. Prioritize sources from that school."

    no_school_note = ("No specific school detected - this may be a district-wide "
                      "question. If the user named a school in a previous message, "
                      "prefer that school's sources.")
    enhanced_context = f"""
SCHOOL ROUTING: {routing_note or no_school_note}

RETRIEVED SOURCES (each labeled with its school):
{context}
"""

    # 🛡️ SAFETY LAYER 2: PII redaction — personal info the user typed must
    # NEVER leave to the external LLM. Retrieval already ran on the original
    # query; only the outbound text is scrubbed.
    safe_query, q_report = scrub_outbound(query)
    if q_report.contains_pii:
        logger.info(f"🔒 Redacted PII before LLM call: {q_report.findings}")
    safe_history = []
    for msg in (history or []):
        safe_msg = dict(msg)
        safe_msg["content"], _ = scrub_outbound(str(msg.get("content", "")))
        safe_history.append(safe_msg)
    safe_context, _ = scrub_outbound(enhanced_context)

    # 4️⃣ GENERATE ANSWER
    answer = generate_answer(safe_query, safe_context, safe_history)

    # 🛡️ SAFETY LAYER 3: output guard (leak check)
    answer = guard_output(answer)

    return {
        "answer": answer,
        "sources": list(seen_urls)[:6],
    }
