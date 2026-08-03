# backend/app/services/search_service.py
from ..retrieval.search import search, all_documents
from .llm_service import generate_answer
from rank_bm25 import BM25Okapi
from flashrank import Ranker, RerankRequest
from backend.app.retrieval.chunker import smart_chunk_text
from backend.app.database.models import Page

# Initialize the Re-ranker once
ranker = Ranker()

def run_search(query: str, history: list = None):
    if history is None:
        history = []

    user_query = query.lower()
    
    # 👋 TASK 1: GREETING & INTENT ROUTER
    # Detect casual greetings and bypass vector database
    greeting_keywords = ["hi", "hello", "hey", "how are you", "good morning", "good afternoon", "greetings"]
    if any(greeting in user_query for greeting in greeting_keywords):
        return {
            "answer": """
            🐾 Welcome to Husky AI! I'm your Washington High School Assistant, ready to help with schedules, events, resources, and school information. 
            
            How can I assist you today? You can ask about:
            - 🕒 Bell schedules and class times
            - 📅 Upcoming events and activities
            - 📚 Academic resources and programs
            - 🏫 School policies and procedures
            - 👥 Staff and department contacts
            """,
            "sources": []
        }
    
    schedule_context = ""

    # 🕒 1. HARDCODED MASTER SCHEDULE (2025-2026)
    if any(word in user_query for word in ["schedule", "times", "period", "dismissal", "lunch", "break"]):
        schedule_context = """
        WASHINGTON HIGH SCHOOL MASTER BELL SCHEDULE (2025-2026):

        REGULAR SCHEDULE (Mon, Thu, Fri):
        - 0 Period: 7:30 - 8:20
        - Period 1: 8:30 - 9:22
        - Period 2: 9:28 - 10:20
        - Break: 10:20 - 10:26
        - Husky/Flex: 10:32 - 11:04
        - Period 3: 11:10 - 12:02
        - Period 4: 12:08 - 1:00
        - Lunch: 1:00 - 1:30
        - Period 5: 1:36 - 2:28
        - Period 6: 2:34 - 3:26

        BLOCK SCHEDULE (Tue, Wed):
        - 0 Period: 7:30 - 8:20
        - Period 1/2: 8:30 - 10:03
        - Break: 10:03 - 10:15
        - Husky/Flex: 11:04 - 12:37
        - Period 3/4: 12:37 - 1:07
        - Lunch: 1:07 - 1:37
        - Period 5/6: 1:37 - 2:50

        MINIMUM DAY (Regular Schedule):
        - 0 Period: 7:30 - 8:20
        - Period 1: 8:30 - 9:09
        - Period 2: 9:15 - 9:54
        - Period 3: 10:00 - 10:39
        - Break: 10:39 - 10:48
        - Period 4: 10:54 - 11:33
        - Period 5: 11:39 - 12:18
        - Period 6: 12:24 - 1:03
        - Lunch: 1:03 - 1:33

        ULTRA MINIMUM DAY:
        - Periods are shorter (approx 30 mins). Dismissal is typically around 12:10 PM.

        FINALS SCHEDULE:
        - 0 Period: 7:30 - 8:20
        - First Final (1/3/5): 8:30 - 10:34
        - Break: 10:34 - 10:50
        - Second Final (2/4/6): 10:50 - 12:54
        - Lunch: 12:54 - 1:24

        NOTE: Special schedules (Assembly, Testing, or Parent Teacher Conferences) vary by date. 
        Always check the school's digital calendar for today's specific alerts.
        """

    # 2️⃣ STEP 2: HYBRID SEARCH (Vector + Keyword) with Smart Chunking
    vector_results = search(query, k=10)
    
    # Apply smart chunking to results for better context
    enhanced_results = []
    for result in vector_results:
        content_type = "text"
        if "type" in result and result["type"] == "html":
            content_type = "html"
        elif "type" in result and result["type"] == "pdf":
            content_type = "text"  # PDFs are already processed
        
        # Use smart chunking for better context preservation
        smart_chunks = smart_chunk_text(result["content"], content_type=content_type)
        
        for chunk_data in smart_chunks:
            enhanced_result = result.copy()
            enhanced_result["content"] = chunk_data["content"]
            # Merge metadata
            if "metadata" in enhanced_result:
                enhanced_result["metadata"].update(chunk_data.get("metadata", {}))
            else:
                enhanced_result["metadata"] = chunk_data.get("metadata", {})
            enhanced_results.append(enhanced_result)
    
    # Update vector_results with enhanced results
    vector_results = enhanced_results

    tokenized_corpus = [doc["content"].split() for doc in all_documents]
    bm25 = BM25Okapi(tokenized_corpus)
    keyword_results_raw = bm25.get_top_n(query.split(), all_documents, n=5)

    # 3️⃣ STEP 3: BLEND & RE-RANK with Semantic Awareness
    combined_dict = {}
    for res in (vector_results + keyword_results_raw):
        # Create unique key based on content + url to avoid duplicates
        key = (res["content"][:100], res.get("url", ""))
        combined_dict[key] = res
    
    combined_list = list(combined_dict.values())
    
    passages = [{"id": i, "text": res["content"], "meta": res} for i, res in enumerate(combined_list)]
    
    rerank_request = RerankRequest(query=query, passages=passages)
    reranked = ranker.rerank(rerank_request)

    top_results = [r["meta"] for r in reranked[:3]]

    # 4️⃣ STEP 4: PREPARE CONTEXT & SOURCES with Semantic Filtering
    if not top_results and not schedule_context:
        context = "No specific school data found."
        sources = []
    else:
        # Filter and prioritize results based on semantic metadata
        filtered_results = []
        for result in top_results:
            metadata = result.get("metadata", {})
            semantic_role = metadata.get("semantic_role", "unknown")
            
            # Prioritize schedule info for schedule-related queries
            if ("schedule" in user_query or "time" in user_query) and semantic_role == "schedule_info":
                filtered_results.insert(0, result)  # Add to front
            # Prioritize policy info for policy-related queries
            elif ("policy" in user_query or "rule" in user_query) and semantic_role == "policy_info":
                filtered_results.insert(0, result)  # Add to front
            # Prioritize event info for event-related queries
            elif ("event" in user_query or "activity" in user_query) and semantic_role == "event_info":
                filtered_results.insert(0, result)  # Add to front
            else:
                filtered_results.append(result)
        
        web_context = "\n\n".join([r["content"] for r in filtered_results])
        context = f"{schedule_context}\n\n{web_context}".strip()
        sources = list(set([str(r.get("url")) for r in filtered_results if r.get("url")]))

    # 5️⃣ STEP 5: GENERATE ANSWER with Enhanced Context and Confidence
    # Use the context enhancer to create optimal LLM context
    try:
        from llm.context_enhancer import LLMContextEnhancer
        enhancer = LLMContextEnhancer()
        temporal_context = enhancer.get_temporal_context()
        
        # Create enhanced context with temporal awareness
        enhanced_context = f"""
TEMPORAL CONTEXT:
- Current School Year: {temporal_context['current_school_year']}
- Current Date: {temporal_context['current_date']}
- Academic Period: {temporal_context['academic_period']}

RELEVANT INFORMATION:
{context}
        """
        
        answer = generate_answer(query, enhanced_context, history)
        
    except Exception:
        # Fallback to original context if enhancer fails
        answer = generate_answer(query, context, history)
    
    return {
        "answer": answer,
        "sources": sources
    }