"""
Anomaly detection engine for ThermoGuard AI.
Detects abnormal thermal behavior using statistical and rule-based methods.
"""

from typing import Dict, Any, List, Tuple
import logging
import math

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detects anomalies in thermal events by comparing with expected patterns.

    For MVP, uses statistical deviation from baseline combined with
    contextual risk factors. Designed to be replaceable with ML-based
    anomaly detection (IsolationForest, OneClassSVM, etc.) later.
    """

    def __init__(self):
        logger.info("AnomalyDetector initialized (statistical MVP version)")

    def detect_anomaly(self, event: Dict[str, Any], baseline_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Detect anomaly in a thermal event.

        Args:
            event: Normalized event dictionary
            baseline_info: Optional baseline information (if not provided, will be extracted from event)

        Returns:
            Anomaly detection result with score, level, and evidence
        """
        try:
            # Get baseline info if not provided
            if baseline_info is None:
                from .baseline import get_facility_baseline
                baseline_info = get_facility_baseline(event)

            # Extract current thermal value
            thermal_features = event.get('thermal_features', {})
            current_value = (
                thermal_features.get('thermal_intensity') or
                event.get('frp', 0.0) or
                thermal_features.get('brightness_temperature', 0.0)
            )

            # Handle missing baseline data
            if baseline_info.get('status') in ['NO_DATA', 'INSUFFICIENT_DATA']:
                return self._handle_insufficient_baseline(event, baseline_info)

            # Statistical anomaly detection
            anomaly_result = self._statistical_anomaly_detection(event, baseline_info, current_value)

            # Contextual anomaly boosters
            contextual_result = self._contextual_anomaly_boost(event, anomaly_result)

            # Finalize result
            final_result = self._finalize_anomaly_result(contextual_result, event)

            logger.debug(f"Anomaly detection result: {final_result}")
            return final_result

        except Exception as e:
            logger.error(f"Error in anomaly detection: {str(e)}")
            return {
                "score": 0.0,
                "level": "UNKNOWN",
                "evidence": ["Anomaly detection error - defaulting to normal"]
            }

    def _handle_insufficient_baseline(self, event: Dict[str, Any], baseline_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle cases where baseline data is insufficient."""
        evidence = ["Insufficient historical data for baseline comparison"]

        # If we have extreme values, still flag as potential anomaly
        frp = event.get('frp', 0.0)
        if frp > 50.0:  # Very high FRP suggests anomaly regardless of baseline
            evidence.append("Extreme thermal intensity detected")
            return {
                "score": min(0.8, frp / 100.0),
                "level": "HIGH" if frp > 75.0 else "MEDIUM",
                "evidence": evidence
            }

        return {
            "score": 0.0,
            "level": "UNKNOWN",
            "evidence": evidence
        }

    def _statistical_anomaly_detection(self, event: Dict[str, Any], baseline_info: Dict[str, Any], current_value: float) -> Dict[str, Any]:
        """Perform statistical anomaly detection based on baseline."""
        expected_value = baseline_info.get('expected_value', 0.0)
        variability = baseline_info.get('variability', 1.0)

        # Calculate deviation metrics
        absolute_deviation = abs(current_value - expected_value)
        deviation_ratio = absolute_deviation / expected_value if expected_value != 0 else float('inf') if current_value > 0 else 0.0

        # Z-score like metric
        z_score = absolute_deviation / variability if variability > 0 else 0.0

        # Base anomaly score from statistical deviation
        # Using a sigmoid-like function to bound the score
        deviation_score = min(1.0, deviation_ratio / 3.0)  # 3x deviation = max score
        variability_score = min(1.0, z_score / 3.0)       # 3 sigma = max score

        # Combine deviation and variability scores
        statistical_score = max(deviation_score, variability_score)

        evidence = []
        if deviation_ratio > 1.0:
            evidence.append(f"Deviation from baseline: {deviation_ratio:.1f}x")
        if z_score > 2.0:
            evidence.append(f"Statistical anomaly (z-score: {z_score:.1f})")

        return {
            "score": statistical_score,
            "absolute_deviation": absolute_deviation,
            "deviation_ratio": deviation_ratio,
            "z_score": z_score,
            "expected_value": expected_value,
            "current_value": current_value,
            "evidence": evidence
        }

    def _contextual_anomaly_boost(self, event: Dict[str, Any], base_result: Dict[str, Any]) -> Dict[str, Any]:
        """Boost anomaly score based on contextual risk factors."""
        score = base_result.get('score', 0.0)
        evidence = base_result.get('evidence', []).copy()

        # Industrial context increases concern for anomalies
        spatial_context = event.get('spatial_context', {})
        if spatial_context.get('context_type') == 'Industrial Facility' or spatial_context.get('inside_facility', False):
            score = min(1.0, score + 0.2)  # Boost for industrial context
            evidence.append("Industrial facility context increases anomaly significance")

        # Persistence boost
        temporal_features = event.get('temporal_features', {})
        persistence_score = temporal_features.get('persistence_score', 0.0)
        observation_count = temporal_features.get('observation_count', 0)

        if persistence_score > 0.7:
            score = min(1.0, score + persistence_score * 0.3)
            evidence.append(f"High persistence score: {persistence_score:.2f}")
        elif observation_count >= 5:
            score = min(1.0, score + 0.2)
            evidence.append(f"Multiple observations: {observation_count}")

        # Confidence boost - high confidence readings are more reliable
        confidence = event.get('confidence', 0.0)
        if confidence > 0.8:
            score = min(1.0, score + 0.1)
            evidence.append("High confidence detection")

        # FRP thresholds for immediate concern
        frp = event.get('frp', 0.0)
        if frp > 100.0:
            score = 1.0
            evidence.append("Extreme FRP (>100 MW) indicates significant event")
        elif frp > 50.0:
            score = min(1.0, score + 0.3)
            evidence.append("High FRP (>50 MW)")

        # Update the result
        base_result['score'] = score
        base_result['evidence'] = evidence
        return base_result

    def _finalize_anomaly_result(self, result: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert numerical score to anomaly level and finalize result."""
        score = result.get('score', 0.0)

        # Convert score to level
        if score < 0.25:
            level = "LOW"
        elif score < 0.6:
            level = "MEDIUM"
        else:
            level = "HIGH"

        # Ensure we have evidence
        evidence = result.get('evidence', [])
        if not evidence:
            evidence = ["Anomaly analysis completed"]

        return {
            "score": score,
            "level": level,
            "evidence": evidence[:5]  # Limit evidence to top 5 items
        }


def detect_anomaly(event: Dict[str, Any], baseline_info: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convenience function for anomaly detection.

    Args:
        event: Normalized event dictionary
        baseline_info: Optional baseline information

    Returns:
        Anomaly detection result
    """
    detector = AnomalyDetector()
    return detector.detect_anomaly(event, baseline_info)