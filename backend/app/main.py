from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routers.search_router import router as search_router

app = FastAPI(title="School AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)

@app.get("/")
def root():
    return {"status": "Backend running"}