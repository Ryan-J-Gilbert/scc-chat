"""ChromaDB-based tool services for RAG."""

import logging
from typing import Any, Dict, List, Tuple

from server.core.chromadb_manager import chroma_manager
from server.core.config import settings
from .base import BaseToolService

logger = logging.getLogger(__name__)


def _filter_hits_by_max_distance(
    documents: List[str],
    metadatas: List[Dict[str, Any]],
    distances: List[float],
    max_distance: float,
) -> List[Tuple[str, Dict[str, Any], float]]:
    """Drop retrieval hits with distance greater than max_distance (if enabled)."""
    triples = list(zip(documents, metadatas, distances))
    if max_distance <= 0:
        return triples
    kept = [(d, m, dist) for d, m, dist in triples if dist <= max_distance]
    dropped = len(triples) - len(kept)
    if dropped:
        logger.info(
            "RAG distance filter removed %s hit(s) (max_distance=%s)",
            dropped,
            max_distance,
        )
    return kept


def _clip_doc_text(doc: str, max_chars: int) -> str:
    """Truncate documentation body for tool output (max_chars <= 0 = no limit)."""
    if max_chars <= 0 or len(doc) <= max_chars:
        return doc
    return f"{doc[:max_chars]}..."


class ChromaDBQATool(BaseToolService):
    """Tool for searching Q&A pairs in ChromaDB."""
    
    def __init__(self, collection_name: str = None):
        """
        Initialize the Q&A search tool.
        
        Args:
            collection_name: Name of the ChromaDB collection (defaults to settings)
        """
        self.collection_name = collection_name or settings.qa_collection_name
        self.collection = chroma_manager.get_collection(self.collection_name)
        logger.info(f"Initialized ChromaDBQATool with collection: {self.collection_name}")
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "search_qa_pairs"
    
    def execute(self, query: str, n_results: int = 5) -> str:
        """
        Search Q&A pairs based on query.
        
        Args:
            query: Search query string
            n_results: Number of results to return
            
        Returns:
            Formatted string with search results
        """
        logger.info(f"Searching Q&A pairs for query: '{query}' (n_results={n_results})")
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            if not results['documents'] or not results['documents'][0]:
                return "No relevant Q&A pairs found for your query."
            
            hits = _filter_hits_by_max_distance(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
                settings.rag_max_distance,
            )
            if not hits:
                return (
                    "No Q&A pairs passed the configured relevance distance threshold "
                    f"(rag_max_distance={settings.rag_max_distance})."
                )
            
            # Format results
            formatted_results = []
            for i, (doc, metadata, distance) in enumerate(hits, 1):
                question = metadata.get('question', 'N/A')
                answer = metadata.get('answer', 'N/A')
                
                formatted_results.append(
                    f"Result {i} (relevance: {1 - distance:.3f}):\n"
                    f"Q: {question}\n"
                    f"A: {answer}\n"
                )
            
            result_str = "\n".join(formatted_results)
            logger.info(f"Found {len(formatted_results)} Q&A pairs")
            return result_str
            
        except Exception as e:
            logger.error(f"Error searching Q&A pairs: {e}", exc_info=True)
            return f"Error searching Q&A pairs: {str(e)}"
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return OpenAI-compatible tool definition."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": (
                    "Search through a database of Q&A pairs to find relevant questions "
                    "and answers. Use this when the user asks questions that might be "
                    "answered by existing Q&A content."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find relevant Q&A pairs"
                        },
                        "n_results": {
                            "type": "integer",
                            "description": "Number of results to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        }


class ChromaDBDocsTool(BaseToolService):
    """Tool for searching documentation in ChromaDB."""
    
    def __init__(self, collection_name: str = None):
        """
        Initialize the documentation search tool.
        
        Args:
            collection_name: Name of the ChromaDB collection (defaults to settings)
        """
        self.collection_name = collection_name or settings.docs_collection_name
        self.collection = chroma_manager.get_collection(self.collection_name)
        logger.info(f"Initialized ChromaDBDocsTool with collection: {self.collection_name}")
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "search_documentation"
    
    def execute(self, query: str, n_results: int = 5) -> str:
        """
        Search documentation based on query.
        
        Args:
            query: Search query string
            n_results: Number of results to return
            
        Returns:
            Formatted string with search results
        """
        logger.info(f"Searching documentation for query: '{query}' (n_results={n_results})")
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            if not results['documents'] or not results['documents'][0]:
                return "No relevant documentation found for your query."
            
            hits = _filter_hits_by_max_distance(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
                settings.rag_max_distance,
            )
            if not hits:
                return (
                    "No documentation passed the configured relevance distance threshold "
                    f"(rag_max_distance={settings.rag_max_distance})."
                )
            
            # Format results
            formatted_results = []
            for i, (doc, metadata, distance) in enumerate(hits, 1):
                title = metadata.get('title', 'Untitled')
                source = metadata.get('source', 'Unknown')
                body = _clip_doc_text(doc, settings.rag_docs_content_max_chars)
                
                formatted_results.append(
                    f"Result {i} (relevance: {1 - distance:.3f}):\n"
                    f"Title: {title}\n"
                    f"Source: {source}\n"
                    f"Content: {body}\n"
                )
            
            result_str = "\n".join(formatted_results)
            logger.info(f"Found {len(formatted_results)} documentation entries")
            return result_str
            
        except Exception as e:
            logger.error(f"Error searching documentation: {e}", exc_info=True)
            return f"Error searching documentation: {str(e)}"
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return OpenAI-compatible tool definition."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": (
                    "Search through technical documentation to find relevant information. "
                    "Use this when the user needs detailed documentation or reference materials."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find relevant documentation"
                        },
                        "n_results": {
                            "type": "integer",
                            "description": "Number of results to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        }