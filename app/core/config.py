from pydantic_settings import BaseSettings #type:ignore
from functools import lru_cache
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database settings
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "regulations_db")

    # API settings
    REGULATIONS_API_URL: str = os.getenv(
        "REGULATIONS_API_URL",
        "https://api.regulations.gov"
    )
    REGULATIONS_API_KEY: str = os.getenv("REGULATIONS_API_KEY", "DEMO_KEY")

    # Ollama settings
    OLLAMA_API_URL: str = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "qwen:1b")

    # App settings
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    class Config:
        env_file = ".env"
        extra = "allow"  # Allow extra fields

@lru_cache()
def get_settings() -> Settings:
    return Settings() 