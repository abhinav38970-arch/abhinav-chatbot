from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from backend.app.services.search_service import run_search

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    history: Optional[List[dict]] = []

@router.post("/ask")
def ask(request: ChatRequest):
    user_query = request.query.lower().strip()
    
    # 1. Greeting Check
    greetings = ["hello", "hi", "hey", "go huskies"]
    if user_query in greetings:
        return {
            "answer": "Hey! 🐾 I'm Husky AI. How can I help you today?",
            "sources": []
        }

    # 2. Identify Category
    school_keywords = ["washington", "whs", "husky", "huskies", "school", "campus"]
    if any(word in user_query for word in school_keywords):
        scope = "washington_high"
    else:
        scope = "district"

    # 3. Call search_service
    response = run_search(request.query, request.history, scope=scope)
    return response