"""
API Routes for Vision Service - with enhanced recommendation and severity.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid
import os
import shutil
from datetime import datetime
from Core.model import predict_image
from Infrastructure.validators import validate_file
from Infrastructure.utils import check_image_quality, enhance_image
from Infrastructure.config import Settings, get_settings
from Infrastructure.logger import get_logger
from Core.knowledge_base import get_knowledge_recommendation
from Core.severity_enhanced import calculate_severity_enhanced
from Core.model import model
from Infrastructure.queue_broker import RabbitMQBroker
from Shared.constants import SERVICE_NAME, SERVICE_VERSION
from Core.binary_model import is_irrigation_problem

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
            broker = RabbitMQBroker()
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
        
        logger.info(f"[{request_id}] Prediction: {english_class} ({confidence:.2f}%)")
        
        # ============================================
        # 7. BINARY CLASSIFICATION CHECK (NEW!)
        # ============================================
        
        # Check if image is actually an irrigation problem
        is_problem, binary_confidence = is_irrigation_problem(
            image_to_predict, 
            threshold=settings.BINARY_THRESHOLD
        )
        
        logger.info(f"[{request_id}] Binary check: is_problem={is_problem}, confidence={binary_confidence:.2f}")
        
        # ============================================
        # 8. REFUSE NON-IRRIGATION IMAGES (NEW!)
        # ============================================
        
        # If binary classifier says it's NOT a problem → refuse
        if not is_problem:
            return {
                "status": "refused",
                "message": "الصورة لا تظهر مشكلة ري واضحة.",
                "confidence": f"{binary_confidence * 100:.2f}%",
                "suggestion": "يرجى رفع صورة توضح مشكلة في الري (تلف أنبوب، فيض، أو انسداد).",
                "timestamp": datetime.now().isoformat()
            }
        
        # ============================================
        # 9. CHECK CONFIDENCE
        # ============================================
        
        if confidence < settings.CONFIDENCE_THRESHOLD:
            return {
                "status": "low_confidence",
                "message": f"الثقة منخفضة ({confidence:.2f}%). يرجى رفع صورة أوضح",
                "confidence": f"{confidence:.2f}%",
                "suggestion": "حاول التقاط الصورة من زاوية أفضل أو في إضاءة أفضل",
                "timestamp": datetime.now().isoformat()
            }
        
        # ============================================
        # 10. UNCERTAIN CHECK (optional)
        # ============================================
        
        # If problem is Blockage with medium confidence → uncertain
        if english_class == "Blockage" and confidence < 85.0:
            return {
                "status": "uncertain",
                "message": "تم اكتشاف انسداد محتمل، لكن الصورة غير واضحة.",
                "confidence": f"{confidence:.2f}%",
                "suggestion": "يرجى رفع صورة أوضح للقناة.",
                "timestamp": datetime.now().isoformat()
            }
        
        if english_class == "Pipe_Damage" and confidence < 85.0:
            return {
                "status": "uncertain",
                "message": "تم اكتشاف تلف محتمل في الأنبوب، لكن الصورة غير واضحة.",
                "confidence": f"{confidence:.2f}%",
                "suggestion": "يرجى رفع صورة أوضح للتلف.",
                "timestamp": datetime.now().isoformat()
            }
        
        if english_class == "Overflow" and confidence < 85.0:
            return {
                "status": "uncertain",
                "message": "تم اكتشاف فيض محتمل، لكن الصورة غير واضحة.",
                "confidence": f"{confidence:.2f}%",
                "suggestion": "يرجى رفع صورة أوضح للمنطقة.",
                "timestamp": datetime.now().isoformat()
            }
        
        # ============================================
        # 11. SUCCESS → GET RECOMMENDATION
        # ============================================
        
        # Get context
        context = {
            'weather': 'clear',
            'location': 'field',
            'crop_stage': 'normal',
            'water_availability': 'normal',
            'user_expertise': 'medium'
        }
        
        # Get recommendation
        recommendation = get_knowledge_recommendation(english_class, confidence, context)
        
        # Calculate severity
        severity_result = calculate_severity_enhanced(english_class, confidence, context)
        
        # 12. Return combined result
        return {
            "status": "success",
            "problem": recommendation.get("arabic", english_class),
            "confidence": f"{confidence:.2f}%",
            "severity": severity_result["level"],
            "recommendation": recommendation.get("recommendation", ""),
            "explanation": recommendation.get("explanation", "").strip(),
            "repair_steps": recommendation.get("steps", []),
            "timestamp": datetime.now().isoformat()
        }

        # 12. Return combined result
    
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
        validated = validate_file(file, settings)
        logger.info(f"[{request_id}] Received file (async): {validated['filename']}")
        
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        if len(contents) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {settings.MAX_FILE_SIZE // (1024*1024)} MB"
            )
        await file.seek(0)
        
        safe_filename = f"{request_id}_{file.filename}"
        file_path = os.path.join(settings.UPLOAD_FOLDER, safe_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"[{request_id}] Saved file: {file_path}")
        
        broker = RabbitMQBroker()
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
