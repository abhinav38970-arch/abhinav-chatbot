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

# 1. Attach API Routes first
app.include_router(search_router)

@app.get("/status")
def status():
    return {
        "status": "Husky AI Online", 
        "engine": "Hybrid (FAISS + BM25)", 
        "database": "SQLite (Surgical Scrape)"
    }

# 2. Serve Frontend Files
# Path logic: starting from backend/app/main.py, go up 2 levels to reach root, then into frontend/
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_path = os.path.normpath(os.path.join(current_dir, "..", "..", "frontend"))

if os.path.exists(frontend_path):
    # 'html=True' looks for index.html automatically at the root URL "/"
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    print(f"Warning: Frontend path not found at {frontend_path}")

# Note: We removed the if __name__ == "__main__" block because 
# your Render command uses 'uvicorn backend.app.main:app' directly.