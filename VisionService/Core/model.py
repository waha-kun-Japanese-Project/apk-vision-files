"""
AI Model loading and prediction logic.
"""

import tensorflow as tf
import numpy as np
import os
import logging
from typing import Dict, Any

from Infrastructure.config import get_settings
from Infrastructure.utils import prepare_image
from Core.severity import calculate_severity
from Core.problem_info import PROBLEM_INFO
from Shared.exceptions import ModelLoadError, PredictionError

logger = logging.getLogger(__name__)
settings = get_settings()

# ============================================
# Class Names
# ============================================
CLASS_NAMES = ["Blockage", "Overflow", "Pipe_Damage"]

# ============================================
# Load Model
# ============================================
def load_model(model_path: str):
    """Load the TensorFlow model from the specified path."""
    try:
        logger.info(f"Loading model from: {model_path}")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        model = tf.keras.models.load_model(model_path)
        logger.info("Model loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise ModelLoadError(f"Failed to load model: {str(e)}")

# Load model at startup
try:
    model = load_model(settings.MODEL_PATH)
except Exception as e:
    logger.error(f"Model initialization failed: {e}")
    model = None

# ============================================
# Prediction Function
# ============================================
def predict_image(image_path: str) -> Dict[str, Any]:
    """
    Predict the irrigation problem from an image.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary with prediction results
        
    Raises:
        PredictionError: If prediction fails
    """
    try:
        if model is None:
            raise ModelLoadError("Model not loaded")
        
        # Validate input
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        if os.path.getsize(image_path) == 0:
            raise ValueError("File is empty")
        
        # Prepare image
        img = prepare_image(image_path)
        
        # Run inference
        prediction = model.predict(img, verbose=0)
        
        # Extract results
        predicted_index = int(np.argmax(prediction))
        confidence = float(np.max(prediction) * 100)
        problem_code = CLASS_NAMES[predicted_index]
        
        # Get problem info
        info = PROBLEM_INFO.get(problem_code, {})
        
        # Calculate severity
        severity = calculate_severity(problem_code, confidence)
        
        # ============================================
        # Return ALL required fields
        # ============================================
        return {
            "problem_code": problem_code,
            "problem_arabic": info.get("arabic", problem_code),
            "confidence": confidence,
            "severity": severity,
            "recommendation": info.get("recommendation", ""),
            "explanation": info.get("explanation", "").strip(),
            "repair_steps": info.get("steps", [])
        }
    
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise PredictionError(f"Prediction failed: {str(e)}")
