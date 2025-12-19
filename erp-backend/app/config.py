from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "ERP Backend API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001"
    ]
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/erp_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30 days
    
    # Security
    BCRYPT_ROUNDS: int = 12
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".pdf", ".jpg", ".png", ".xlsx", ".csv"]
    
    # Redis (for caching)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Email (for notifications)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@erp.com"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Microservices URLs
    SALES_SERVICE_URL: str = "http://localhost:5001"
    FINANCE_SERVICE_URL: str = "http://localhost:5002"
    HR_SERVICE_URL: str = "http://localhost:5003"
    
    # HTTP Client
    HTTP_CLIENT_TIMEOUT: int = 30  # seconds
    HTTP_CLIENT_MAX_CONNECTIONS: int = 100
    HTTP_CLIENT_MAX_KEEPALIVE: int = 20
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    """
    return Settings()


# Create settings instance
settings = get_settings()
