"""
Middleware setup for the Vision Service.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from Infrastructure.config import get_settings

logger = logging.getLogger(__name__)

def setup_middleware(app: FastAPI):
    """Setup all middleware for the application."""
    settings = get_settings()
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    logger.info("Middleware configured successfully")