"""
Binary classifier to check if image is an irrigation problem or not.
"""

import tensorflow as tf
import numpy as np
import os
import logging
from typing import Tuple

from Infrastructure.utils import prepare_image
from Infrastructure.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BinaryClassifier:
    """
    Binary classifier to determine if an image shows an irrigation problem.
    Returns: (is_problem, confidence)
    """
    
    def __init__(self):
        self.model = None
        self.threshold = settings.BINARY_THRESHOLD
        self._load_model()
    
    def _load_model(self):
        """Load the binary classifier model."""
        model_path = settings.BINARY_MODEL_PATH
        try:
            if os.path.exists(model_path):
                self.model = tf.keras.models.load_model(model_path)
                logger.info(f"✅ Binary classifier loaded from: {model_path}")
            else:
                logger.warning("⚠️ Binary classifier not found. Using fallback method.")
                self.model = None
        except Exception as e:
            logger.error(f"❌ Failed to load binary classifier: {e}")
            self.model = None
    
    def predict(self, image_path: str) -> Tuple[bool, float]:
        """
        Predict if image shows an irrigation problem.
        
        Args:
            image_path: Path to image
            
        Returns:
            Tuple of (is_problem, confidence)
        """
        if self.model is None:
            return self._fallback_predict(image_path)
        
        try:
            img = prepare_image(image_path)
            prediction = self.model.predict(img, verbose=0)
            prob = float(prediction[0][0])
            return prob > self.threshold, prob
        except Exception as e:
            logger.error(f"Binary prediction error: {e}")
            return self._fallback_predict(image_path)
    
    def _fallback_predict(self, image_path: str) -> Tuple[bool, float]:
        """
        Fallback method when model is not available.
        Uses the main model's confidence as indicator.
        """
        try:
            from Core.model import predict_image
            result = predict_image(image_path)
            confidence = result.get('confidence', 0)
            
            # If confidence is high, it's likely a problem
            # If confidence is low, it's likely not a problem
            is_problem = confidence > 60.0
            
            return is_problem, confidence / 100.0
        except Exception as e:
            logger.error(f"Fallback prediction error: {e}")
            return True, 0.5


# Singleton instance
binary_classifier = BinaryClassifier()


def is_irrigation_problem(image_path: str, threshold: float = None) -> Tuple[bool, float]:
    """
    Check if image shows an irrigation problem.
    
    Args:
        image_path: Path to image
        threshold: Minimum confidence to consider as problem
        
    Returns:
        Tuple of (is_problem, confidence)
    """
    if threshold is None:
        threshold = settings.BINARY_THRESHOLD
    
    is_problem, confidence = binary_classifier.predict(image_path)
    
    if confidence < threshold:
        is_problem = False
    
    return is_problem, confidence