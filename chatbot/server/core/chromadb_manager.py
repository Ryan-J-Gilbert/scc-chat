"""ChromaDB connection and collection management."""

import logging
from pathlib import Path
from typing import Dict, Optional

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection

from .config import settings

logger = logging.getLogger(__name__)


class ChromaDBManager:
    """Manages ChromaDB client and collections as a singleton."""
    
    _instance: Optional['ChromaDBManager'] = None
    _client: Optional[ClientAPI] = None
    _collections: Dict[str, Collection] = {}
    
    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize ChromaDB manager."""
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the ChromaDB persistent client."""
        db_path = Path(settings.chroma_db_path)
        db_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initializing ChromaDB client at {db_path}")
        self._client = chromadb.PersistentClient(path=str(db_path))
        logger.info("ChromaDB client initialized successfully")
    
    def get_collection(self, collection_name: str) -> Collection:
        """
        Get or create a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            ChromaDB collection instance
        """
        if collection_name not in self._collections:
            logger.info(f"Loading collection: {collection_name}")
            self._collections[collection_name] = self._client.get_or_create_collection(
                name=collection_name
            )
        
        return self._collections[collection_name]
    
    def list_collections(self) -> list[str]:
        """List all available collections."""
        collections = self._client.list_collections()
        return [col.name for col in collections]
    
    @property
    def client(self) -> ClientAPI:
        """Get the ChromaDB client."""
        return self._client


# Global instance
chroma_manager = ChromaDBManager()