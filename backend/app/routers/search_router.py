from fastapi import APIRouter
from backend.app.services.search_service import run_search

router = APIRouter()

@router.get("/ask")
def ask(query: str):
    return run_search(query)