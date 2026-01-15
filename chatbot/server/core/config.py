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

raise NotImplementedError