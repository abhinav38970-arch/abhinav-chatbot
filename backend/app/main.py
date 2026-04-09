import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.routers.search_router import router as search_router

# Added redirect_slashes=False to prevent "Connection Errors" caused by URL formatting
app = FastAPI(title="School AI Backend", redirect_slashes=False)

# ✅ CORS Middleware - Essential for the browser to talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# 1. Attach API Routes FIRST (Priority)
app.include_router(search_router, prefix="/api")

@app.get("/status")
def status():
    return {"status": "Husky AI Online"}

# 2. Serve Frontend Files LAST
current_dir = os.path.dirname(os.path.abspath(__file__))

# Checks multiple levels to find the 'frontend' folder automatically
possible_paths = [
    os.path.normpath(os.path.join(current_dir, "..", "..", "frontend")),
    os.path.normpath(os.path.join(current_dir, "..", "..", "..", "frontend")),
    os.path.join(os.getcwd(), "frontend")
]

frontend_path = None
for p in possible_paths:
    if os.path.exists(p):
        frontend_path = p
        break

if frontend_path:
    # Mounts the frontend to the root URL "/"
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    # This will show up in your Hugging Face Logs if things are missing
    print(f"Warning: Frontend path not found! Checked: {possible_paths}")