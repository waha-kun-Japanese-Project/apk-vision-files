"""
Severity calculation logic.
"""

from Shared.enums import SeverityLevel

def calculate_severity(problem: str, confidence: float) -> str:
    """
    Calculate severity level based on problem type and confidence.
    
    Args:
        problem: Problem code (Pipe_Damage, Overflow, Blockage)
        confidence: Confidence percentage (0-100)
    
    Returns:
        Severity level in Arabic
    """
    if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 100:
        return SeverityLevel.UNKNOWN.value
    
    if problem == "Pipe_Damage":
        if confidence >= 95:
            return SeverityLevel.VERY_CRITICAL.value
        elif confidence >= 85:
            return SeverityLevel.CRITICAL.value
        elif confidence >= 70:
            return SeverityLevel.HIGH.value
        elif confidence >= 50:
            return SeverityLevel.MEDIUM.value
        else:
            return SeverityLevel.LOW.value
    
    elif problem == "Overflow":
        if confidence >= 95:
            return SeverityLevel.VERY_HIGH.value
        elif confidence >= 85:
            return SeverityLevel.HIGH.value
        elif confidence >= 70:
            return SeverityLevel.MEDIUM.value
        elif confidence >= 50:
            return SeverityLevel.LOW.value
        else:
            return SeverityLevel.MINOR.value
    
    elif problem == "Blockage":
        if confidence >= 95:
            return SeverityLevel.MEDIUM.value
        elif confidence >= 85:
            return SeverityLevel.LOW.value
        elif confidence >= 70:
            return SeverityLevel.MINOR.value
        elif confidence >= 50:
            return SeverityLevel.VERY_MINOR.value
        else:
            return SeverityLevel.NEGLIGIBLE.value
    
    return SeverityLevel.UNKNOWN.value