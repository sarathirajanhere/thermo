"""
Main intelligence pipeline for ThermoGuard AI.
Orchestrates the complete AI analysis: classification → baseline → anomaly → priority → evidence.
"""

from typing import Dict, Any, List
import logging
import time

from ..features.feature_pipeline import extract_all_features
from ..pipelines.classification_pipeline import classify_thermal_event
from ..pipelines.anomaly_pipeline import analyze_thermal_event_anomaly
from ..pipelines.priority_pipeline import calculate_priority
from ..inference.baseline import get_facility_baseline

logger = logging.getLogger(__name__)


def analyze_thermal_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Complete AI intelligence analysis for a thermal event.

    Pipeline:
    1. Feature extraction
    2. Classification
    3. Facility baseline analysis
    4. Anomaly detection
    5. Priority scoring
    6. Evidence compilation

    Args:
        event: Normalized event dictionary from FIRMS/geospatial enrichment

    Returns:
        Complete intelligence result dictionary
    """
    start_time = time.time()
    event_id = event.get('event_id', 'unknown')

    try:
        logger.info(f"Starting AI intelligence analysis for event {event_id}")

        # Step 1: Feature extraction (for logging/debugging)
        features = extract_all_features(event)
        logger.debug(f"Extracted {len(features)} features for event {event_id}")

        # Step 2: Classification
        classification_result = classify_thermal_event(event)
        logger.debug(f"Classification: {classification_result.get('label')} "
                    f"(confidence: {classification_result.get('confidence', 0):.2f})")

        # Step 3: Facility baseline analysis
        baseline_result = get_facility_baseline(event)
        logger.debug(f"Baseline status: {baseline_result.get('status')}")

        # Step 4: Anomaly detection
        anomaly_result = analyze_thermal_event_anomaly(event)
        logger.debug(f"Anomaly: {anomaly_result.get('level')} "
                    f"(score: {anomaly_result.get('score', 0):.2f})")

        # Step 5: Priority scoring
        priority_result = calculate_priority(
            classification_result,
            baseline_result,
            anomaly_result,
            event
        )
        logger.debug(f"Priority: {priority_result.get('severity')} "
                    f"(score: {priority_result.get('score', 0):.2f})")

        # Step 6: Compile final intelligence result
        intelligence_result = {
            "event_id": event_id,
            "timestamp": event.get('timestamp'),
            "classification": {
                "label": classification_result.get('label'),
                "confidence": classification_result.get('confidence'),
                "evidence": classification_result.get('evidence', [])
            },
            "baseline": {
                "status": baseline_result.get('status'),
                "expected_value": baseline_result.get('expected_value'),
                "current_value": baseline_result.get('current_value',
                                    event.get('thermal_features', {}).get('thermal_intensity') or
                                    event.get('frp', 0.0)),
                "deviation": baseline_result.get('deviation'),
                "deviation_ratio": baseline_result.get('deviation_ratio'),
                "variability": baseline_result.get('variability'),
                "sample_count": baseline_result.get('sample_count')
            },
            "anomaly": {
                "score": anomaly_result.get('score'),
                "level": anomaly_result.get('level'),
                "evidence": anomaly_result.get('evidence', []),
                "deviation": anomaly_result.get('deviation'),
                "deviation_ratio": anomaly_result.get('deviation_ratio'),
                "baseline_value": anomaly_result.get('baseline_value'),
                "current_value": anomaly_result.get('current_value')
            },
            "priority": {
                "severity": priority_result.get('severity'),
                "score": priority_result.get('score'),
                "evidence": priority_result.get('evidence', [])
            },
            "processing_time_ms": (time.time() - start_time) * 1000
        }

        logger.info(f"AI intelligence analysis completed for event {event_id} "
                   f"in {intelligence_result['processing_time_ms']:.2f}ms")

        return intelligence_result

    except Exception as e:
        logger.error(f"Error in AI intelligence pipeline for event {event_id}: {str(e)}", exc_info=True)
        # Return safe fallback result
        return {
            "event_id": event_id,
            "timestamp": event.get('timestamp'),
            "classification": {
                "label": "Other",
                "confidence": 0.1,
                "evidence": ["AI pipeline error - defaulting to Other"]
            },
            "baseline": {
                "status": "ERROR",
                "expected_value": None,
                "current_value": event.get('frp', 0.0),
                "deviation": None,
                "deviation_ratio": None,
                "variability": None,
                "sample_count": 0
            },
            "anomaly": {
                "score": 0.0,
                "level": "UNKNOWN",
                "evidence": ["AI pipeline error - anomaly detection failed"],
                "deviation": None,
                "deviation_ratio": None,
                "baseline_value": None,
                "current_value": event.get('frp', 0.0)
            },
            "priority": {
                "severity": "MODERATE",  # Safe fallback
                "score": 0.5,
                "evidence": ["AI pipeline error - defaulting to MODERATE priority"]
            },
            "processing_time_ms": (time.time() - start_time) * 1000,
            "error": str(e)
        }


def analyze_batch_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyze a batch of thermal events.

    Args:
        events: List of normalized event dictionaries

    Returns:
        List of intelligence result dictionaries
    """
    logger.info(f"Starting batch analysis of {len(events)} events")
    results = []

    for event in events:
        result = analyze_thermal_event(event)
        results.append(result)

    logger.info(f"Batch analysis completed. Processed {len(results)} events")
    return results


# Convenience function for external use
def get_event_intelligence(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get intelligence analysis for a single thermal event.

    Args:
        event: Normalized event dictionary

    Returns:
        Intelligence result dictionary
    """
    return analyze_thermal_event(event)