"""Configuration management using Pydantic Settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # LLM Configuration
    llm_api_key: str
    llm_model_id: str = "deepseek-ai/DeepSeek-V3.2"
    llm_base_url: str = "https://api-inference.modelscope.cn/v1"
    llm_timeout: int = 60
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000

    # Embedding Configuration
    embedding_api_key: Optional[str] = None
    embedding_model: str = "BAAI/bge-large-zh-v1.5"
    embedding_base_url: str = "https://api-inference.modelscope.cn/v1"

    # SerpAPI Configuration
    serpapi_api_key: str

    # Database Configuration
    database_url: str = "sqlite+aiosqlite:///./data/student_agent.db"

    # Vector Store Configuration
    vector_store_path: str = "./data/vector_db"
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Application Configuration
    app_name: str = "Student Learning Agent"
    app_version: str = "1.0.0"
    debug: bool = False

    # CORS Configuration
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Authentication
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"


# Global settings instance
settings = Settings()
