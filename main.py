"""FastAPI REST API for handling background tasks with Huey."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.lifespan import lifespan_handler

app = FastAPI(
    title="UIKit Agent API",
    description="API for generating code from Figma",
    version="0.0.1",
    lifespan=lifespan_handler,
)

# --- CORS SETTINGS
app.add_middleware(
    CORSMiddleware,
    # For Figma (Origin: null) wildcard is required,
    # BUT we disable credentials so the browser allows it.
    allow_origins=["*"],
    # DISABLE this for wildcard (safer)
    # Enable only if you are sure you are sending cookies
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTERS
# Register all REST API routers
app.include_router(api_router)

# If running the file directly in terminal using this command:
# REDIS_HOST=localhost uv run python main.py
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        ssl_keyfile="certificates/localhost+2-key.pem",
        ssl_certfile="certificates/localhost+2.pem",
    )
