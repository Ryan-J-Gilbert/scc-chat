"""Application configuration using Pydantic settings."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    github_api_key: str
    openai_api_key: Optional[str] = None
    
    # ChromaDB Configuration
    chroma_db_path: str = "./chroma_db"
    qa_collection_name: str = "qa_collection"
    docs_collection_name: str = "documentation_collection"
    
    # LLM Configuration
    default_model: str = "gpt-4o-mini"
    max_tokens: int = 1500
    temperature: float = 0.7
    
    # System Prompt
    system_prompt: str = """You are a helpful AI assistant with access to a knowledge base through specialized tools.

When a user asks a question:
1. Determine if you need to search the knowledge base using your available tools
2. Use the search_qa_pairs tool to find relevant Q&A pairs
3. Use the search_documentation tool to find relevant technical documentation
4. Synthesize information from multiple sources when appropriate
5. Provide clear, accurate answers based on the retrieved information
6. If you cannot find relevant information, say so honestly

Guidelines:
- Always cite when you're using information from the knowledge base
- Be concise but thorough
- If multiple Q&A pairs or documents are relevant, synthesize them into a coherent answer
- Ask clarifying questions if the user's query is ambiguous
- Maintain a friendly, professional tone"""
    
    # Server Configuration
    server_host: str = "localhost"
    server_port: int = 8000
    
    # Logging
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
