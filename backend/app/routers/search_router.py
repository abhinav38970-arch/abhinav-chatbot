from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
# Ensure this path matches where your run_search function is saved
from backend.app.services.search_service import run_search

# ⬇️ THIS LINE IS MISSING OR BROKEN IN YOUR CURRENT FILE ⬇️
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
        return {"answer": "Hey! 🐾 I'm Husky AI. How can I help you today?"}

    # Call the service logic
    response = run_search(request.query, request.history)
    return response