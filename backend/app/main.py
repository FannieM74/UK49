import sys, os
# Add both the backend directory (to import `app`) and the repository root (to import `backend`)
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.extend([backend_dir, repo_root])
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import draws, scrape, predictions

app = FastAPI(title="UK49 Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

app.include_router(draws.router)
app.include_router(scrape.router)
app.include_router(predictions.router)

@app.get("/api/health")
def health():
    return {"status": "ok", "draws_count": 0}
