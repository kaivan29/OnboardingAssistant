from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Grok API Configuration
    xai_api_key: str
    xai_base_url: str = "https://api.x.ai/v1"
    xai_model: str = "grok-4-1-fast-reasoning"
    xai_resume_model: str = "grok-4-fast"  # Fast model for resume analysis
    
    # Database Configuration
    database_url: str = "sqlite+aiosqlite:///./onboarding.db"
    
    # Application Settings
    app_name: str = "Grok Onboarding Platform"
    debug: bool = False
    
    # CORS Settings
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
