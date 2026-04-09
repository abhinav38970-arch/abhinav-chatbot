import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.routers.search_router import router as search_router

app = FastAPI(title="School AI Backend")

# ✅ CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# 1. Attach API Routes with a prefix to avoid conflict with Static Files
app.include_router(search_router, prefix="/api")

@app.get("/status")
def status():
    return {
        "status": "Husky AI Online", 
        "engine": "Hybrid (FAISS + BM25)", 
        "database": "SQLite (Surgical Scrape)"
    }

# 2. Serve Frontend Files
current_dir = os.path.dirname(os.path.abspath(__file__))
# Adjusted to find your frontend folder relative to main.py
frontend_path = os.path.normpath(os.path.join(current_dir, "..", "..", "frontend"))

if os.path.exists(frontend_path):
    # html=True serves index.html at the root "/"
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    print(f"Warning: Frontend path not found at {frontend_path}")