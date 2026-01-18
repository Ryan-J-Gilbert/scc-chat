"""
ChromaDB ingestion script for SCC documentation and Q&A pairs.

This module ingests scraped TechWeb articles (markdown) and Q&A pairs from 
spreadsheets into a unified ChromaDB collection for semantic search.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings
import pandas as pd
from tqdm import tqdm


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentationIngestor:
    """Handles ingestion of SCC documentation into ChromaDB."""
    
    DEFAULT_BATCH_SIZE = 100
    
    def __init__(
        self,
        db_path: str,
        collection_name: str = "scc_documentation",
        scraped_content_dir: Optional[str] = None,
        qa_spreadsheet_path: Optional[str] = None
    ):
        """
        Initialize the documentation ingestor.
        
        Args:
            db_path: Path where ChromaDB will persist data
            collection_name: Name of the collection to create/use
            scraped_content_dir: Directory containing scraped markdown files
            qa_spreadsheet_path: Path to Excel file with Q&A pairs
        """
        self.db_path = Path(db_path)
        self.collection_name = collection_name
        self.scraped_content_dir = Path(scraped_content_dir) if scraped_content_dir else None
        self.qa_spreadsheet_path = Path(qa_spreadsheet_path) if qa_spreadsheet_path else None
        
        self.client = None
        self.collection = None
        
    def _initialize_client(self) -> None:
        """Initialize ChromaDB persistent client and collection."""
        logger.info(f"Initializing ChromaDB client at {self.db_path}")
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Using existing collection: '{self.collection_name}'")
        except Exception:
            self.collection = self.client.create_collection(name=self.collection_name)
            logger.info(f"Created new collection: '{self.collection_name}'")
    
    def _load_markdown_articles(self) -> tuple[List[str], List[Dict[str, str]], List[str]]:
        """
        Load markdown articles from scraped content directory.
        
        Returns:
            Tuple of (documents, metadatas, ids)
        """
        if not self.scraped_content_dir or not self.scraped_content_dir.exists():
            logger.warning(f"Scraped content directory not found: {self.scraped_content_dir}")
            return [], [], []
        
        documents = []
        metadatas = []
        ids = []
        
        markdown_files = list(self.scraped_content_dir.glob("*.md"))
        logger.info(f"Found {len(markdown_files)} markdown files")
        
        for filepath in tqdm(markdown_files, desc="Loading markdown articles"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract title from first line if it's a markdown header
                title = filepath.stem
                lines = content.split('\n')
                if lines and lines[0].startswith('# '):
                    title = lines[0].replace('# ', '').strip()
                
                # Extract source URL if present
                source_url = None
                if 'Source:' in content:
                    # Find the source line (usually at the end)
                    for line in reversed(lines):
                        if line.startswith('Source:'):
                            source_url = line.replace('Source:', '').strip()
                            break
                
                documents.append(content)
                metadatas.append({
                    "source": source_url or str(filepath),
                    "doc_type": "article",
                    "title": title,
                    "filename": filepath.name
                })
                ids.append(f"article_{filepath.stem}")
                
            except Exception as e:
                logger.error(f"Error loading {filepath}: {e}")
                continue
        
        logger.info(f"Successfully loaded {len(documents)} articles")
        return documents, metadatas, ids
    
    def _load_qa_spreadsheet(self) -> tuple[List[str], List[Dict[str, str]], List[str]]:
        """
        Load Q&A pairs from Excel spreadsheet.
        
        Returns:
            Tuple of (documents, metadatas, ids)
        """
        if not self.qa_spreadsheet_path or not self.qa_spreadsheet_path.exists():
            logger.warning(f"Q&A spreadsheet not found: {self.qa_spreadsheet_path}")
            return [], [], []
        
        logger.info(f"Loading Q&A pairs from {self.qa_spreadsheet_path}")
        
        try:
            df = pd.read_excel(self.qa_spreadsheet_path)
            logger.info(f"Loaded spreadsheet with {len(df)} rows")
        except Exception as e:
            logger.error(f"Error loading spreadsheet: {e}")
            return [], [], []
        
        # Validate required columns
        required_columns = ['Questions', 'Answers']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            logger.info(f"Available columns: {df.columns.tolist()}")
            return [], [], []
        
        documents = []
        metadatas = []
        ids = []
        
        for i, row in tqdm(enumerate(df.itertuples()), total=len(df), desc="Loading Q&A pairs"):
            try:
                # Skip rows with empty questions or answers
                if pd.isna(row.Questions) or pd.isna(row.Answers):
                    continue
                
                # Format Q&A document
                question = str(row.Questions).strip()
                answer = str(row.Answers).strip()
                
                # Get source if available
                source = getattr(row, 'Source', 'Unknown')
                if pd.isna(source):
                    source = 'Unknown'
                else:
                    source = str(source).strip()
                
                # Create structured Q&A document
                document = f"""Q&A Document

Question:
{question}

Answer:
{answer}

Source:
{source}
"""
                
                documents.append(document)
                metadatas.append({
                    "source": source,
                    "doc_type": "qa",
                    "question": question,
                    "answer": answer
                })
                ids.append(f"qa_{i}")
                
            except Exception as e:
                logger.error(f"Error processing row {i}: {e}")
                continue
        
        logger.info(f"Successfully loaded {len(documents)} Q&A pairs")
        return documents, metadatas, ids
    
    def _ingest_batch(
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
        if not documents:
            logger.warning("No documents to ingest")
            return
        
        total_batches = (len(documents) + batch_size - 1) // batch_size
        logger.info(
            f"Ingesting {len(documents)} documents in {total_batches} batches "
            f"(batch_size={batch_size})"
        )
        
        for i in tqdm(range(0, len(documents), batch_size), desc="Ingesting batches"):
            batch_docs = documents[i:i + batch_size]
            batch_metas = metadatas[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            
            try:
                self.collection.add(
                    documents=batch_docs,
                    metadatas=batch_metas,
                    ids=batch_ids
                )
            except Exception as e:
                logger.error(f"Error ingesting batch {i//batch_size + 1}: {e}")
                # Try to continue with remaining batches
                continue
    
    def check_existing_documents(self) -> int:
        """
        Check how many documents already exist in the collection.
        
        Returns:
            Number of existing documents
        """
        count = self.collection.count()
        logger.info(f"Collection currently contains {count} documents")
        return count
    
    def ingest(
        self,
        batch_size: int = DEFAULT_BATCH_SIZE,
        force: bool = False
    ) -> None:
        """
        Main ingestion workflow.
        
        Args:
            batch_size: Number of documents per batch
            force: If True, ingest even if collection already has documents
        """
        try:
            self._initialize_client()
            
            # Check if collection already has documents
            existing_count = self.check_existing_documents()
            if existing_count > 0 and not force:
                logger.info("Collection already contains documents. Use --force to add more.")
                return
            
            # Load articles
            article_docs, article_metas, article_ids = self._load_markdown_articles()
            
            # Load Q&A pairs
            qa_docs, qa_metas, qa_ids = self._load_qa_spreadsheet()
            
            # Combine all documents
            all_documents = article_docs + qa_docs
            all_metadatas = article_metas + qa_metas
            all_ids = article_ids + qa_ids
            
            if not all_documents:
                logger.error("No documents found to ingest!")
                return
            
            logger.info(
                f"Total documents to ingest: {len(all_documents)} "
                f"({len(article_docs)} articles, {len(qa_docs)} Q&A pairs)"
            )
            
            # Ingest all documents
            self._ingest_batch(all_documents, all_metadatas, all_ids, batch_size)
            
            # Final count
            final_count = self.collection.count()
            logger.info(f"Ingestion complete. Collection now has {final_count} documents total.")
            
        except Exception as e:
            logger.error(f"Ingestion failed: {e}", exc_info=True)
            raise


def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Ingest SCC documentation into ChromaDB"
    )
    parser.add_argument(
        "--db-path",
        default="./chroma_db",
        help="Path to ChromaDB storage directory"
    )
    parser.add_argument(
        "--collection",
        default="scc_documentation",
        help="Name of the ChromaDB collection"
    )
    parser.add_argument(
        "--articles",
        help="Path to directory containing scraped markdown articles"
    )
    parser.add_argument(
        "--qa-spreadsheet",
        help="Path to Excel file containing Q&A pairs"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for ingestion"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force ingestion even if collection already has documents"
    )
    
    args = parser.parse_args()
    
    # Validate that at least one data source is provided
    if not args.articles and not args.qa_spreadsheet:
        parser.error("At least one of --articles or --qa-spreadsheet must be provided")
    
    # Run ingestion
    ingestor = DocumentationIngestor(
        db_path=args.db_path,
        collection_name=args.collection,
        scraped_content_dir=args.articles,
        qa_spreadsheet_path=args.qa_spreadsheet
    )
    
    ingestor.ingest(
        batch_size=args.batch_size,
        force=args.force
    )


if __name__ == "__main__":
    main()