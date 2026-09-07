"""
Anomaly detection pipeline for ThermoGuard AI.
Orchestrates baseline calculation and anomaly detection.
"""

from typing import Dict, Any
import logging

from ..features.feature_pipeline import extract_all_features
from ..inference.baseline import get_facility_baseline, detect_anomaly_from_baseline
from ..inference.anomaly import detect_anomaly

logger = logging.getLogger(__name__)


def analyze_thermal_event_anomaly(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Complete anomaly detection pipeline for a thermal event.

    Args:
        event: Normalized event dictionary

    Returns:
        Anomaly detection result with score, level, and evidence
    """
    try:
        logger.debug(f"Starting anomaly detection pipeline for event {event.get('event_id', 'unknown')}")

        # Extract features (for logging/debugging)
        features = extract_all_features(event)
        logger.debug(f"Extracted {len(features)} features")

        # Get facility baseline
        baseline_info = get_facility_baseline(event)
        logger.debug(f"Baseline status: {baseline_info.get('status')}")

        # Run anomaly detection (uses both statistical and contextual methods)
        result = detect_anomaly(event, baseline_info)

        logger.debug(f"Anomaly detection completed: {result.get('level')} (score: {result.get('score'):.2f})")
        return result

    except Exception as e:
        logger.error(f"Error in anomaly detection pipeline: {str(e)}")
        return {
            "score": 0.0,
            "level": "UNKNOWN",
            "evidence": ["Anomaly detection pipeline error"]
        }