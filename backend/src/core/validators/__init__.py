"""
Validators module - Input validation components.

Submodules:
- zip.py: ZIP file and directory validation
- cross_validator.py: Cross-validation for complementary detection system
"""

from src.core.validators.cross_validator import (
    CrossValidator,
    CrossValidationResult,
    EnhancedDetectionResults,
    cross_validate_detections,
    get_framework_from_library,
    get_framework_from_tool_config,
    get_priority_frameworks_for_language,
    LIBRARY_TO_FRAMEWORK_MAP,
    TOOL_TO_FRAMEWORK_MAP,
    LANGUAGE_FRAMEWORK_PRIORITY,
)

__all__ = [
    "CrossValidator",
    "CrossValidationResult",
    "EnhancedDetectionResults",
    "cross_validate_detections",
    "get_framework_from_library",
    "get_framework_from_tool_config",
    "get_priority_frameworks_for_language",
    "LIBRARY_TO_FRAMEWORK_MAP",
    "TOOL_TO_FRAMEWORK_MAP",
    "LANGUAGE_FRAMEWORK_PRIORITY",
]
