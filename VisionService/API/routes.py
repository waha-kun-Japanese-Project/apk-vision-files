"""
API Routes for Vision Service - with refusal logic for "no problem" images.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid
import os
import shutil
from datetime import datetime

from VisionService.Core.model import predict_image
from VisionService.Infrastructure.validators import validate_file
from VisionService.Infrastructure.utils import check_image_quality, enhance_image
from VisionService.Infrastructure.config import Settings, get_settings
from VisionService.Infrastructure.logger import get_logger

# Import enhanced modules
from VisionService.Core.knowledge_base import get_knowledge_recommendation
from VisionService.Core.severity_enhanced import calculate_severity_enhanced
from VisionService.Core.model import model
from VisionService.Infrastructure.queue_broker import RabbitMQBroker
from VisionService.Shared.constants import SERVICE_NAME, SERVICE_VERSION

router = APIRouter()
logger = get_logger("VisionService.API")

# Thread pool for async predictions
executor = ThreadPoolExecutor(max_workers=4)


# ============================================
# HEALTH CHECK ENDPOINT
# ============================================
@router.get("/health", tags=["health"])
async def health_check():
    """Check if service and model are healthy."""
    try:
        # Check RabbitMQ connection
        rabbitmq_status = "unknown"
        try:
            # max_retries=1: health checks must fail fast, not wait through
            # the worker's full retry-with-backoff (see queue_broker.py) -
            # a slow /health response can itself trip k8s readiness probes.
            broker = RabbitMQBroker(max_retries=1)
            broker.close()
            rabbitmq_status = "connected"
        except Exception as e:
            rabbitmq_status = f"error: {str(e)}"
        
        return {
            "status": "healthy" if model is not None else "unhealthy",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "model_loaded": model is not None,
            "rabbitmq": rabbitmq_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "model_loaded": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ============================================
# SERVICE INFO ENDPOINT
# ============================================
@router.get("/", tags=["info"])
async def root():
    """Service information."""
    settings = get_settings()
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "description": "Computer Vision for irrigation problem diagnosis",
        "endpoints": {
            "/api/v1/predict": "POST - Synchronous prediction (1-3s)",
            "/api/v1/predict-async": "POST - Asynchronous prediction (RabbitMQ)",
            "/health": "GET - Service health check",
            "/docs": "GET - API documentation"
        },
        "rabbitmq": {
            "host": settings.RABBITMQ_HOST,
            "port": settings.RABBITMQ_PORT,
            "queues": {
                "requests": "vision.prediction.requests",
                "results": "vision.prediction.results"
            }
        },
        "timestamp": datetime.now().isoformat()
    }


# ============================================
# SYNCHRONOUS PREDICTION ENDPOINT
# ============================================
@router.post("/api/v1/predict", tags=["prediction"])
async def predict(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Analyze an image and return irrigation problem diagnosis (SYNCHRONOUS).
    
    - **file**: Image file (JPG, PNG, WEBP, BMP) - max 10MB
    - **Returns**: Complete diagnosis with problem type, severity, and repair steps
    - **Processing time**: 1-3 seconds
    """
    file_path = None
    request_id = str(uuid.uuid4())[:8]
    
    try:
        # 1. Validate file
        validated = validate_file(file, settings)
        logger.info(f"[{request_id}] Received file: {validated['filename']}")
        
        # 2. Check file size
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="الملف فارغ")
        
        if len(contents) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"حجم الملف كبير جداً. الحد الأقصى: {settings.MAX_FILE_SIZE // (1024*1024)} ميجابايت"
            )
        await file.seek(0)
        
        # 3. Save temporarily
        safe_filename = f"{request_id}_{file.filename}"
        file_path = os.path.join(settings.UPLOAD_FOLDER, safe_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"[{request_id}] Saved file: {file_path}")
        
        # 4. Quality check
        if settings.QUALITY_CHECK_ENABLED:
            is_good, quality_msg = check_image_quality(file_path)
            if not is_good:
                return {
                    "status": "poor_quality",
                    "message": quality_msg,
                    "suggestion": "حاول التقاط الصورة من زاوية أفضل أو في إضاءة أفضل",
                    "timestamp": datetime.now().isoformat()
                }
        
        # 5. Enhance image
        image_to_predict = file_path
        if settings.ENHANCE_IMAGE_ENABLED:
            enhanced_path = enhance_image(file_path)
            if enhanced_path != file_path:
                image_to_predict = enhanced_path
                logger.info(f"[{request_id}] Image enhanced")
        
        # 6. Run prediction (async)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor, 
            predict_image, 
            image_to_predict
        )
        
        english_class = result['problem_code']
        confidence = result['confidence']
        problem = result['problem_arabic']
        severity = result['severity']
        recommendation = result['recommendation']
        explanation = result['explanation']
        repair_steps = result['repair_steps']
        
        logger.info(f"[{request_id}] Prediction: {english_class} ({confidence:.2f}%)")
        
        # ============================================
        # REFUSE "NO PROBLEM" IMAGES
        # ============================================
        
        # 1. If confidence is very low (< 50%), refuse with clear message
        if confidence < 50.0:
            return {
                "status": "refused",
                "message": "لم يتم الكشف عن مشكلة واضحة في الصورة.",
                "confidence": f"{confidence:.2f}%",
                "suggestion": "يرجى رفع صورة توضح مكان المشكلة بشكل أفضل.",
                "timestamp": datetime.now().isoformat()
            }
        
        # 2. If confidence is low to medium (50-65%), return "uncertain"
        if confidence < 65.0:
            return {
                "status": "uncertain",
                "message": "الصورة غير واضحة أو لا تظهر مشكلة محددة بوضوح.",
                "confidence": f"{confidence:.2f}%",
                "suggestion": "يرجى رفع صورة أوضح أو التأكد من وجود مشكلة.",
                "timestamp": datetime.now().isoformat()
            }
        
        # ============================================
        # 3. Confidence is high (>= 65%), return diagnosis with ALL fields
        # ============================================
        
        # Return combined result with ALL required fields
        return {
            "status": "success",
            "problem": problem,  # ✅ Prediction problem (Arabic)
            "problem_code": english_class,  # ✅ Prediction problem (English code)
            "confidence": f"{confidence:.2f}%",  # ✅ Confidence
            "severity": severity,  # ✅ Severity
            "recommendation": recommendation,  # ✅ Recommendation
            "explanation": explanation,  # ✅ Explanation
            "repair_steps": repair_steps,  # ✅ Repair steps
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"حدث خطأ: {str(e)}")
    
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"[{request_id}] Cleaned up temporary file")
            except Exception as e:
                logger.warning(f"[{request_id}] Failed to delete file: {e}")


# ============================================
# ASYNCHRONOUS PREDICTION ENDPOINT
# ============================================
@router.post("/api/v1/predict-async", tags=["prediction"])
async def predict_async(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Submit an image for asynchronous processing.
    
    - **file**: Image file (JPG, PNG, WEBP, BMP) - max 10MB
    - **Returns**: request_id immediately
    - **Result**: Delivered via RabbitMQ queue 'vision.prediction.results'
    """
    file_path = None
    request_id = str(uuid.uuid4())[:8]
    
    try:
        # 1. Validate file
        validated = validate_file(file, settings)
        logger.info(f"[{request_id}] Received file (async): {validated['filename']}")
        
        # 2. Check file size
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        if len(contents) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {settings.MAX_FILE_SIZE // (1024*1024)} MB"
            )
        await file.seek(0)
        
        # 3. Save temporarily
        safe_filename = f"{request_id}_{file.filename}"
        file_path = os.path.join(settings.UPLOAD_FOLDER, safe_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"[{request_id}] Saved file: {file_path}")
        
        # 4. Publish to queue
        # max_retries=1: this is an inline HTTP request - a client
        # shouldn't wait through the full retry-with-backoff, better to
        # fail fast and let them retry the upload
        broker = RabbitMQBroker(max_retries=1)
        broker.publish_request(request_id, file_path)
        broker.close()
        
        return {
            "status": "accepted",
            "request_id": request_id,
            "message": "Request accepted for processing. Result will be delivered asynchronously via RabbitMQ.",
            "queue": "vision.prediction.results",
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error: {e}")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))