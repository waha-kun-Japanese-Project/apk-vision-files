"""
Configuration management using environment variables.
"""

import os
from pathlib import Path
from typing import List
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ============================================
    # Service Settings
    # ============================================
    SERVICE_NAME: str = "vision-service"
    SERVICE_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = True
    
    # ============================================
    # Model Settings
    # ============================================

    # ============================================
# Model Settings
# ============================================
    MODEL_PATH: str = "models/efficientnet_waha_kun.keras"
    BINARY_MODEL_PATH: str = "models/binary_classifier.keras"  # ← جديد
    CONFIDENCE_THRESHOLD: float = 75.0
    BINARY_THRESHOLD: float = 0.75  # ← جديد

    # File Settings
    # ============================================
    UPLOAD_FOLDER: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".webp", ".bmp"]
    
    # ============================================
    # Image Processing Settings
    # ============================================
    QUALITY_CHECK_ENABLED: bool = True
    ENHANCE_IMAGE_ENABLED: bool = True
    
    # ============================================
    # CORS Settings
    # ============================================
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # ============================================
    # RabbitMQ Settings
    # ============================================
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
