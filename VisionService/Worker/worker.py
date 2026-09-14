"""
Background worker for processing vision predictions asynchronously.
"""

import json
import logging
import time
import os
from datetime import datetime

from Infrastructure.queue_broker import RabbitMQBroker
from Infrastructure.logger import setup_logger
from Core.model import predict_image
from Infrastructure.utils import enhance_image, check_image_quality
from Infrastructure.config import get_settings
from Core.binary_model import is_irrigation_problem  # ✅ أضف السطر ده

# Setup logger
logger = setup_logger("VisionService.Worker")
settings = get_settings()

def process_prediction(ch, method, properties, body):
    """
    Process a prediction request from the queue.
    
    Args:
        ch: Channel
        method: Method frame
        properties: Properties
        body: Message body
    """
    broker = None
    start_time = time.time()
    
    try:
        # Parse message
        message = json.loads(body)
        request_id = message['request_id']
        image_path = message['image_path']
        
        logger.info(f"[{request_id}] Processing started")
        
        # Check if image exists
        if not os.path.exists(image_path):
            logger.error(f"[{request_id}] Image not found: {image_path}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        # Optional: Quality check
        if settings.QUALITY_CHECK_ENABLED:
            is_good, quality_msg = check_image_quality(image_path)
            if not is_good:
                logger.warning(f"[{request_id}] Poor quality: {quality_msg}")
        
        # Optional: Enhance image
        image_to_predict = image_path
        if settings.ENHANCE_IMAGE_ENABLED:
            enhanced_path = enhance_image(image_path)
            if enhanced_path != image_path:
                image_to_predict = enhanced_path
                logger.info(f"[{request_id}] Image enhanced")
        
        # ============================================
        # ✅ BINARY CLASSIFIER CHECK (مثل الـ Sync)
        # ============================================
        
        # Check if image is actually an irrigation problem
        is_problem, binary_confidence = is_irrigation_problem(
            image_to_predict, 
            threshold=settings.BINARY_THRESHOLD
        )
        
        logger.info(f"[{request_id}] Binary check: is_problem={is_problem}, confidence={binary_confidence:.2f}")
        
        # If NOT a problem → refuse
        if not is_problem:
            result = {
                "problem_code": "Unknown",
                "problem_arabic": "لا توجد مشكلة",
                "confidence": binary_confidence * 100,
                "severity": "غير معروفة",
                "recommendation": "الصورة لا تظهر مشكلة ري واضحة.",
                "explanation": "لم يتم الكشف عن مشكلة في الري.",
                "repair_steps": []
            }
            logger.info(f"[{request_id}] Refused: Not an irrigation problem")
        else:
            # Run prediction
            prediction_start = time.time()
            result = predict_image(image_to_predict)
            prediction_time = time.time() - prediction_start
            
            logger.info(f"[{request_id}] Prediction: {result['problem_code']} ({result['confidence']:.2f}%) in {prediction_time:.2f}s")
        
        # Publish result
        broker = RabbitMQBroker()
        broker.publish_result(request_id, result, prediction_time if 'prediction_time' in locals() else 0.5)
        
        # Clean up enhanced image (if created)
        if image_to_predict != image_path and os.path.exists(image_to_predict):
            os.remove(image_to_predict)
            logger.info(f"[{request_id}] Cleaned up enhanced image")
        
        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
        total_time = time.time() - start_time
        logger.info(f"[{request_id}] Completed successfully (total: {total_time:.2f}s)")
        
    except Exception as e:
        logger.error(f"[{request_id}] Failed: {e}")
        
        # Publish error result
        try:
            broker = RabbitMQBroker()
            broker.publish_error(request_id, str(e), time.time() - start_time)
        except Exception as pub_error:
            logger.error(f"[{request_id}] Failed to publish error: {pub_error}")
        
        # Reject and requeue for retry
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    finally:
        if broker:
            broker.close()

def start_worker():
    """Start the worker to process queue messages."""
    logger.info("=" * 60)
    logger.info("Starting Vision Service Worker...")
    logger.info(f"RabbitMQ Host: {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}")
    logger.info("Waiting for messages...")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    broker = None
    try:
        broker = RabbitMQBroker()
        broker.consume_requests(process_prediction)
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
    finally:
        if broker:
            broker.close()

if __name__ == "__main__":
    start_worker()