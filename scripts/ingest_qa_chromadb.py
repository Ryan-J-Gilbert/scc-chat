"""
ChromaDB document ingestion script for Q&A pairs.

This module loads Q&A pairs from a JSON file and ingests them into a
persistent ChromaDB collection with batch processing.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import chromadb
from tqdm import tqdm


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChromaDBIngestor:
    """Handles ingestion of Q&A pairs into ChromaDB."""
    
    DEFAULT_BATCH_SIZE = 32
    
    def __init__(self, db_path: str, collection_name: str = "qa_collection"):
        """
        Initialize the ChromaDB ingestor.
        
        Args:
            db_path: Path where ChromaDB will persist data
            collection_name: Name of the collection to create/use
        """
        self.db_path = Path(db_path)
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        
    def _initialize_client(self) -> None:
        """Initialize ChromaDB persistent client and collection."""
        logger.info(f"Initializing ChromaDB client at {self.db_path}")
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=str(self.db_path))
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name
        )
        logger.info(f"Collection '{self.collection_name}' ready")
    
    def _load_qa_pairs(self, json_path: str) -> List[Dict[str, Any]]:
        """
        Load Q&A pairs from JSON file.
        
        Args:
            json_path: Path to JSON file containing qa_pairs
            
        Returns:
            List of Q&A pair dictionaries
            
        Raises:
            FileNotFoundError: If JSON file doesn't exist
            json.JSONDecodeError: If JSON is malformed
            KeyError: If expected structure is missing
        """
        json_file = Path(json_path)
        if not json_file.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")
        
        logger.info(f"Loading Q&A pairs from {json_path}")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'qa_pairs' not in data:
            raise KeyError("Expected 'qa_pairs' key in JSON data")
        
        qa_pairs = data['qa_pairs']
        logger.info(f"Loaded {len(qa_pairs)} Q&A pairs")
        return qa_pairs
    
    def _prepare_data(
        self, qa_pairs: List[Dict[str, Any]]
    ) -> tuple[List[str], List[Dict[str, str]], List[str]]:
        """
        Prepare Q&A pairs for ChromaDB ingestion.
        
        Args:
            qa_pairs: List of Q&A pair dictionaries
            
        Returns:
            Tuple of (documents, metadatas, ids)
        """
        documents = []
        metadatas = []
        ids = []
        
        for row in qa_pairs:
            documents.append(row['question'])
            metadatas.append({
                "question": row["question"],
                "answer": row["answer"],
            })
            ids.append(str(row["id"]))
        
        return documents, metadatas, ids
    
    def _ingest_batches(
        self,
        documents: List[str],
        metadatas: List[Dict[str, str]],
        ids: List[str],
        batch_size: int = DEFAULT_BATCH_SIZE
    ) -> None:
        """
        Ingest documents into ChromaDB in batches.
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries
            ids: List of document IDs
            batch_size: Number of documents to process per batch
        """
        total_batches = (len(documents) + batch_size - 1) // batch_size
        logger.info(
            f"Ingesting {len(documents)} documents in {total_batches} batches "
            f"(batch_size={batch_size})"
        )
        
        for i in tqdm(range(0, len(documents), batch_size), desc="Ingesting"):
            batch_docs = documents[i:i + batch_size]
            batch_metas = metadatas[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            
            self.collection.add(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )
    
    def ingest(
        self,
        json_path: str,
        batch_size: int = DEFAULT_BATCH_SIZE,
        preview: bool = True
    ) -> None:
        """
        Main ingestion workflow.
        
        Args:
            json_path: Path to JSON file with Q&A pairs
            batch_size: Number of documents per batch
            preview: Whether to print preview of first entry
        """
        try:
            self._initialize_client()
            qa_pairs = self._load_qa_pairs(json_path)
            documents, metadatas, ids = self._prepare_data(qa_pairs)
            
            if preview and documents:
                logger.info("Preview of first entry:")
                logger.info(f"Document: {documents[0]}")
                logger.info(f"Metadata: {metadatas[0]}")
                logger.info(f"ID: {ids[0]}")
            
            self._ingest_batches(documents, metadatas, ids, batch_size)
            logger.info("Embedding and ingestion complete.")
            
        except Exception as e:
            logger.error(f"Ingestion failed: {e}", exc_info=True)
            raise


def main():
    """Main entry point for the script."""
    # Configuration
    DB_PATH = "./chroma_db"
    JSON_PATH = "/projectnb/scc-chat/research/ticketparsing/qa_pairs.json"
    COLLECTION_NAME = "qa_collection"
    BATCH_SIZE = 32
    
    # Run ingestion
    ingestor = ChromaDBIngestor(
        db_path=DB_PATH,
        collection_name=COLLECTION_NAME
    )
    ingestor.ingest(
        json_path=JSON_PATH,
        batch_size=BATCH_SIZE
    )


if __name__ == "__main__":
    main()