from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Real Estate Inbox Copilot"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = "sqlite:///./real_estate.db"
    
    SECRET_KEY: str = "supersecretkey"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    DATASET_PATH: str = "../data/sample_emails.json"
    
    GOOGLE_API_KEY: Optional[str] = None
    MODEL_NAME: str = "gemini-2.0-flash-exp"
    EMBEDDING_MODEL_NAME: str = "text-embedding-004"
    
    # Admin configuration
    ADMIN_EMAIL: str = "alex.chan@remaxmetrohomes.com"  # Demo admin user

    class Config:
        env_file = ".env"

settings = Settings()
