"""
Core layer - business logic.
"""

from .model import predict_image, model
from .severity import calculate_severity
from .severity_enhanced import calculate_severity_enhanced
from .knowledge_base import get_knowledge_recommendation
from .problem_info import PROBLEM_INFO
from .binary_model import is_irrigation_problem

__all__ = [
    'predict_image',
    'model',
    'calculate_severity',
    'calculate_severity_enhanced',
    'get_knowledge_recommendation',
    'SimpleKnowledgeBase',
    'PROBLEM_INFO',
    'get_knowledge_documents'
]
