"""
File validation utilities.
"""

from fastapi import UploadFile, HTTPException
from typing import Dict, Any
import os

from Infrastructure.config import Settings

def validate_file(file: UploadFile, settings: Settings) -> Dict[str, Any]:
    """
    Validate uploaded file.
    
    Args:
        file: Uploaded file
        settings: Application settings
        
    Returns:
        Dictionary with file information
        
    Raises:
        HTTPException: If validation fails
    """
    # Check extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"نوع الملف '{ext}' غير مدعوم. الأنواع المدعومة: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Check filename
    if not file.filename or len(file.filename) > 255:
        raise HTTPException(
            status_code=400,
            detail="اسم الملف غير صالح"
        )
    
    return {
        "filename": file.filename,
        "extension": ext,
        "size": file.size if hasattr(file, 'size') else 0
    }