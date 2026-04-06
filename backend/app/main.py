from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routers.search_router import router as search_router
import os

app = FastAPI(title="School AI Backend")

# ✅ Connects the frontend to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# Attach the router that contains the /ask endpoint
app.include_router(search_router)

@app.get("/")
def root():
    return {
        "status": "Husky AI Online", 
        "engine": "FAISS Vector Store",
        "database": "SQLite (Surgical Scrape)"
    }

if __name__ == "__main__":
    import uvicorn
    # Render provides a specific port via environment variables
    port = int(os.environ.get("PORT", 8000))
    # We pass 'app' directly here to fix the port binding issue
    # We keep the host as 0.0.0.0 for Render accessibility
    uvicorn.run(app, host="0.0.0.0", port=port)