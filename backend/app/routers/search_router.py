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
    
    # Simple greeting check
    greetings = ["hello", "hi", "hey", "go huskies"]
    if user_query in greetings:
        # ✅ Return a dictionary with empty sources so frontend stays stable
        return {
            "answer": "Hey! 🐾 I'm Husky AI. How can I help you today?",
            "sources": []
        }

    # Call the service logic (This returns the dictionary from search_service)
    response = run_search(request.query, request.history)
    return response