"""ChromaDB-based tool services for RAG."""

import json
import logging
from typing import Dict, Any

from server.core.chromadb_manager import chroma_manager
from server.core.config import settings
from .base import BaseToolService

logger = logging.getLogger(__name__)


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
            
            # Format results
            formatted_results = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ), 1):
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
            
            # Format results
            formatted_results = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ), 1):
                title = metadata.get('title', 'Untitled')
                source = metadata.get('source', 'Unknown')
                
                formatted_results.append(
                    f"Result {i} (relevance: {1 - distance:.3f}):\n"
                    f"Title: {title}\n"
                    f"Source: {source}\n"
                    f"Content: {doc[:500]}{'...' if len(doc) > 500 else ''}\n"
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