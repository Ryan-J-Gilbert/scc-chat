"""Core functionality and configuration."""

from .config import settings
from .chromadb_manager import ChromaDBManager

__all__ = ["settings", "ChromaDBManager"]