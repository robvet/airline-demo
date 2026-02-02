"""
FastAPI Server for Pacific Airlines Agent.

Run with: uvicorn run:app --reload --port 8000
Or: python run.py
"""
from dotenv import load_dotenv
load_dotenv()  # Load .env before any other imports

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router

# Create FastAPI app
app = FastAPI(
    title="Pacific Airlines Agent API",
    description="Deterministic AI agent for airline customer service",
    version="1.0.0",
)

# CORS for Streamlit UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
