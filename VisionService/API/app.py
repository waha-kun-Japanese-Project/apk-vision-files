"""
Vision Service - WAHA KUN AI
Main entry point for the FastAPI application.
"""

import sys
import os

# Add project root to Python path

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f" Project root added to path: {project_root}")

from API.routes import router
from API.middleware import setup_middleware
from Infrastructure.config import get_settings
from Infrastructure.logger import setup_logger
from Shared.constants import SERVICE_NAME, SERVICE_VERSION
from fastapi import FastAPI

# Setup logger
logger = setup_logger("VisionService.API")
settings = get_settings()

# Create app
app = FastAPI(
    title="WAHA KUN Vision Service",
    version=SERVICE_VERSION,
    description="Computer Vision service for irrigation problem diagnosis",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup middleware
setup_middleware(app)

# Include all routes from routes.py
app.include_router(router)

# ============================================
# Main Entry Point
# ============================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
