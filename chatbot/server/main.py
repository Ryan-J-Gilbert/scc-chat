"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.core.config import settings
from server.core.chromadb_manager import chroma_manager
from server.api.routes import chat, health

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting up chatbot server...")
    logger.info(f"ChromaDB path: {settings.chroma_db_path}")
    logger.info(f"Available collections: {chroma_manager.list_collections()}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down chatbot server...")


# Create FastAPI app
app = FastAPI(
    title="Chatbot API",
    description="RAG-powered chatbot with tool calling support",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(chat.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Chatbot API",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "server.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True,
        log_level=settings.log_level.lower()
    )