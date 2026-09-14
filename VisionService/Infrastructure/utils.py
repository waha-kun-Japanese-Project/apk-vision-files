"""
Image processing utilities.
"""

from PIL import Image, UnidentifiedImageError, ImageEnhance
import numpy as np
from tensorflow.keras.applications.efficientnet import preprocess_input
import logging
import os
from typing import Tuple

from Shared.constants import TARGET_SIZE, MIN_IMAGE_SIZE

logger = logging.getLogger(__name__)

# ============================================
# Prepare Image
# ============================================
def prepare_image(image_path: str) -> np.ndarray:
    """
    Prepare image for model input.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Preprocessed image array
        
    Raises:
        ValueError: If image processing fails
    """
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        if os.path.getsize(image_path) == 0:
            raise ValueError("File is empty")
        
        try:
            img = Image.open(image_path)
        except UnidentifiedImageError:
            raise ValueError("File is not a valid image")
        
        if img.width < MIN_IMAGE_SIZE[0] or img.height < MIN_IMAGE_SIZE[1]:
            raise ValueError(
                f"Image too small. Minimum size: {MIN_IMAGE_SIZE[0]}x{MIN_IMAGE_SIZE[1]} pixels"
            )
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        img = img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
        img_array = np.array(img, dtype=np.float32)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        
        return img_array
    
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        raise ValueError(f"Failed to process image: {str(e)}")

# ============================================
# Check Image Quality
# ============================================
def check_image_quality(image_path: str) -> Tuple[bool, str]:
    """
    Check image quality.
    
    Args:
        image_path: Path to the image
        
    Returns:
        Tuple of (is_good, message)
    """
    try:
        img = Image.open(image_path)
        img_array = np.array(img)
        
        # Check dimensions
        if img.width < 100 or img.height < 100:
            return False, "الصورة صغيرة جداً. يرجى رفع صورة أوضح"
        
        # Check brightness
        brightness = np.mean(img_array)
        if brightness < 30:
            return False, "الصورة مظلمة جداً. يرجى رفع صورة بإضاءة أفضل"
        if brightness > 220:
            return False, "الصورة ساطعة جداً. حاول تقليل الإضاءة"
        
        # Check contrast
        if len(img_array.shape) == 3:
            gray = np.mean(img_array, axis=2)
        else:
            gray = img_array
        
        contrast = np.std(gray)
        if contrast < 20:
            return False, "التباين منخفض جداً. حاول تحسين الإضاءة"
        
        return True, "جودة الصورة جيدة"
    
    except Exception as e:
        logger.error(f"Quality check error: {e}")
        return True, "تعذر فحص جودة الصورة"

# ============================================
# Enhance Image
# ============================================
def enhance_image(image_path: str) -> str:
    """
    Enhance image quality automatically.
    
    Args:
        image_path: Path to the image
        
    Returns:
        Path to enhanced image
    """
    try:
        img = Image.open(image_path)
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.3)
        
        # Enhance brightness
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
        
        # Save enhanced image
        name, ext = os.path.splitext(image_path)
        enhanced_path = f"{name}_enhanced{ext}"
        img.save(enhanced_path, quality=95)
        
        logger.info(f"Image enhanced: {enhanced_path}")
        return enhanced_path
    
    except Exception as e:
        logger.error(f"Enhancement error: {e}")
        return image_path