"""
Classification pipeline for ThermoGuard AI.
Orchestrates feature extraction and classification.
"""

from typing import Dict, Any
import logging

from ..features.feature_pipeline import extract_all_features
from ..inference.classifier import classify_event

logger = logging.getLogger(__name__)


def classify_thermal_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Complete classification pipeline for a thermal event.

    Args:
        event: Normalized event dictionary

    Returns:
        Classification result with label, confidence, and evidence
    """
    try:
        logger.debug(f"Starting classification pipeline for event {event.get('event_id', 'unknown')}")

        # Extract features (for logging/debugging)
        features = extract_all_features(event)
        logger.debug(f"Extracted {len(features)} features")

        # Run classification
        result = classify_event(event)

        logger.debug(f"Classification completed: {result.get('label')} (confidence: {result.get('confidence'):.2f})")
        return result

    except Exception as e:
        logger.error(f"Error in classification pipeline: {str(e)}")
        return {
            "label": "Other",
            "confidence": 0.1,
            "evidence": ["Classification pipeline error"]
        }