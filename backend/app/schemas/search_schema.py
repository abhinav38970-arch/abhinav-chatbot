from pydantic import BaseModel
from typing import List


class SearchResult(BaseModel):
    url: str
    snippet: str


class SearchResponse(BaseModel):
    results: List[SearchResult]