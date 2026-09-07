"""
Priority scoring pipeline for ThermoGuard AI.
Orchestrates priority calculation from classification, baseline, and anomaly results.
"""

from typing import Dict, Any
import logging

from ..features.feature_pipeline import extract_all_features
from ..inference.priority import prioritize_event

logger = logging.getLogger(__name__)


def calculate_priority(
    classification: Dict[str, Any],
    baseline: Dict[str, Any],
    anomaly: Dict[str, Any],
    event: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Complete priority scoring pipeline.

    Args:
        classification: Result from classification step
        baseline: Result from baseline analysis
        anomaly: Result from anomaly detection
        event: Original event dictionary (optional)

    Returns:
        Priority result with severity level, score, and evidence
    """
    try:
        logger.debug("Starting priority scoring pipeline")

        # Run priority calculation
        result = prioritize_event(classification, baseline, anomaly, event)

        logger.debug(f"Priority calculation completed: {result.get('severity')} (score: {result.get('score'):.2f})")
        return result

    except Exception as e:
        logger.error(f"Error in priority pipeline: {str(e)}")
        return {
            "severity": "MODERATE",
            "score": 0.5,
            "evidence": ["Priority pipeline error"]
        }