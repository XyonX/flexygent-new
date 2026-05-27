"""
Cloudflare LLM Proxy Server
An OpenAI-compatible API proxy that forwards requests to Cloudflare Workers AI.

Usage:
    # Set up your .env file first (copy from .env.example)
    pip install -r requirements.txt
    python main.py

Then in another terminal:
    # Generate a proxy API key (using the admin key from .env)
    curl -X POST http://localhost:8000/admin/keys?name=my-key \
      -H "Authorization: Bearer YOUR_ADMIN_API_KEY"

    # Use the proxy like OpenAI
    curl http://localhost:8000/v1/chat/completions \
      -H "Authorization: Bearer GENERATED_PROXY_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "model": "@cf/meta/llama-3.1-8b-instruct",
        "messages": [{"role": "user", "content": "Hello!"}]
      }'
"""

import sys
from pathlib import Path

# Ensure we can import from the project directory
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from router import router

app = FastAPI(
    title="Cloudflare LLM Proxy",
    description="OpenAI-compatible API proxy for Cloudflare Workers AI",
    version="1.0.0",
)

# Allow CORS for all origins (useful for local development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(router)


@app.on_event("startup")
async def startup():
    """Initialize the database on startup."""
    init_db()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Cloudflare LLM Proxy",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "admin": {
                "list_keys": "GET /admin/keys",
                "create_key": "POST /admin/keys?name=...",
                "revoke_key": "DELETE /admin/keys/{id}",
            },
            "openai": {
                "list_models": "GET /v1/models",
                "chat_completions": "POST /v1/chat/completions",
                "embeddings": "POST /v1/embeddings",
            },
        },
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
