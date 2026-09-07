"""
Facility baseline engine for ThermoGuard AI.
Computes expected thermal behavior for facilities and detects deviations.
"""

from typing import Dict, Any, Optional, List
import logging
import math
from collections import deque

logger = logging.getLogger(__name__)


class FacilityBaseline:
    """
    Maintains and computes baseline thermal behavior for a facility.

    For MVP, uses simple statistical baseline (mean, median) from historical data.
    Designed to be replaceable with more sophisticated time-series models.
    """

    def __init__(self, facility_id: str):
        self.facility_id = facility_id
        self.history = deque(maxlen=100)  # Keep last 100 observations
        self.baseline_value = None
        self.baseline_std = None
        self.sample_count = 0
        logger.info(f"FacilityBaseline initialized for facility {facility_id}")

    def add_observation(self, thermal_value: float, timestamp: str = None) -> None:
        """
        Add a new thermal observation to the facility's history.

        Args:
            thermal_value: Thermal intensity measurement (FRP, brightness temp, etc.)
            timestamp: Optional timestamp of observation
        """
        self.history.append({
            'value': thermal_value,
            'timestamp': timestamp
        })
        self.sample_count += 1
        self._update_baseline()

    def _update_baseline(self) -> None:
        """Update baseline statistics from historical data."""
        if len(self.history) < 2:
            return

        values = [obs['value'] for obs in self.history]

        # Calculate mean and standard deviation
        self.baseline_value = sum(values) / len(values)

        if len(values) >= 2:
            variance = sum((x - self.baseline_value) ** 2 for x in values) / len(values)
            self.baseline_std = math.sqrt(variance) if variance > 0 else 0.0
        else:
            self.baseline_std = 0.0

    def get_baseline(self) -> Dict[str, Any]:
        """
        Get current baseline statistics for the facility.

        Returns:
            Dictionary with baseline information
        """
        if self.sample_count == 0:
            return {
                "status": "NO_DATA",
                "expected_value": None,
                "expected_frequency": None,
                "variability": None,
                "sample_count": 0
            }

        if self.sample_count < 5:
            return {
                "status": "INSUFFICIENT_DATA",
                "expected_value": self.baseline_value,
                "expected_frequency": None,
                "variability": self.baseline_std,
                "sample_count": self.sample_count
            }

        return {
            "status": "AVAILABLE",
            "expected_value": self.baseline_value,
            "expected_frequency": len(self.history),  # Simplified frequency
            "variability": self.baseline_std,
            "sample_count": self.sample_count
        }

    def compute_deviation(self, current_value: float) -> Dict[str, Any]:
        """
        Compute deviation of current value from baseline.

        Args:
            current_value: Current thermal measurement

        Returns:
            Dictionary with deviation information
        """
        baseline = self.get_baseline()

        if baseline["status"] in ["NO_DATA", "INSUFFICIENT_DATA"]:
            return {
                "deviation": None,
                "deviation_ratio": None,
                "z_score": None,
                "baseline_status": baseline["status"]
            }

        expected = baseline["expected_value"]
        variability = baseline["variability"]

        # Absolute deviation
        deviation = current_value - expected

        # Relative deviation (ratio)
        deviation_ratio = deviation / expected if expected != 0 else float('inf') if current_value > 0 else 0.0

        # Z-score (if we have sufficient variability)
        z_score = None
        if variability and variability > 0:
            z_score = deviation / variability
        elif variability == 0:
            z_score = 0.0 if deviation == 0 else float('inf') if deviation > 0 else float('-inf')

        return {
            "deviation": deviation,
            "deviation_ratio": deviation_ratio,
            "z_score": z_score,
            "baseline_status": baseline["status"],
            "expected_value": expected,
            "variability": variability
        }


def calculate_baseline(facility_id: str, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate facility baseline from historical data (functional interface).

    Args:
        facility_id: Identifier for the facility
        historical_data: List of historical observations with 'value' and optionally 'timestamp'

    Returns:
        Baseline information dictionary
    """
    baseline_engine = FacilityBaseline(facility_id)

    for obs in historical_data:
        value = obs.get('value', obs.get('frp', obs.get('thermal_intensity', 0.0)))
        timestamp = obs.get('timestamp')
        baseline_engine.add_observation(value, timestamp)

    return baseline_engine.get_baseline()


def detect_anomaly_from_baseline(event: Dict[str, Any], baseline_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect anomaly by comparing event with facility baseline.

    Args:
        event: Current event dictionary
        baseline_info: Baseline information from calculate_baseline or FacilityBaseline.get_baseline()

    Returns:
        Anomaly detection result
    """
    # Extract current thermal value from event
    thermal_features = event.get('thermal_features', {})
    current_value = (
        thermal_features.get('thermal_intensity') or
        event.get('frp', 0.0) or
        thermal_features.get('brightness_temperature', 0.0)
    )

    # Handle case where we might need to compute baseline on the fly
    if baseline_info.get('status') == 'NO_DATA':
        # Try to compute from historical_context in event
        historical_context = event.get('historical_context', {})
        if historical_context:
            baseline_value = historical_context.get('baseline_value', 0.0)
            historical_count = historical_context.get('historical_observation_count', 0)

            # Simplified baseline - in reality would use proper historical data
            if historical_count > 0:
                expected_value = baseline_value
                # Estimate variability - placeholder for demo
                variability = baseline_value * 0.2 if baseline_value > 0 else 5.0

                deviation = current_value - expected_value
                deviation_ratio = deviation / expected_value if expected_value != 0 else float('inf') if current_value > 0 else 0.0

                # Simple anomaly score based on deviation
                anomaly_score = min(1.0, abs(deviation_ratio) / 2.0)  # Cap at 1.0 for 2x deviation

                return {
                    "score": anomaly_score,
                    "level": "LOW" if anomaly_score < 0.3 else "MEDIUM" if anomaly_score < 0.7 else "HIGH",
                    "deviation": deviation,
                    "deviation_ratio": deviation_ratio,
                    "baseline_value": expected_value,
                    "current_value": current_value,
                    "evidence": [
                        f"Current value {current_value:.1f} vs baseline {expected_value:.1f}",
                        f"Deviation ratio: {deviation_ratio:.2f}"
                    ]
                }

    # Use provided baseline info
    if baseline_info.get('status') in ['NO_DATA', 'INSUFFICIENT_DATA']:
        return {
            "score": 0.0,
            "level": "UNKNOWN",
            "deviation": None,
            "deviation_ratio": None,
            "evidence": ["Insufficient baseline data for anomaly detection"]
        }

    expected_value = baseline_info.get('expected_value', 0.0)
    variability = baseline_info.get('variability', 1.0)

    deviation = current_value - expected_value
    deviation_ratio = deviation / expected_value if expected_value != 0 else float('inf') if current_value > 0 else 0.0

    # Calculate anomaly score based on deviation and persistence
    persistence_score = event.get('temporal_features', {}).get('persistence_score', 0.0)
    observation_count = event.get('temporal_features', {}).get('observation_count', 0)

    # Base anomaly score from deviation
    deviation_score = min(1.0, abs(deviation_ratio) / 2.0)  # Normalize to 0-1 range

    # Boost score based on persistence
    persistence_boost = persistence_score * 0.3

    # Boost score based on observation count (more observations = more confident)
    count_boost = min(0.2, observation_count / 20.0)  # Max 0.2 boost for 20+ observations

    anomaly_score = min(1.0, deviation_score + persistence_boost + count_boost)

    # Determine level
    if anomaly_score < 0.25:
        level = "LOW"
    elif anomaly_score < 0.6:
        level = "MEDIUM"
    else:
        level = "HIGH"

    evidence = []
    if abs(deviation_ratio) > 0.5:
        evidence.append(f"Significant deviation from facility baseline ({deviation_ratio:.1f}x)")
    if persistence_score > 0.6:
        evidence.append("Persistent thermal activity")
    if observation_count >= 3:
        evidence.append(f"Multiple observations ({observation_count})")
    if not evidence:
        evidence.append("Baseline comparison completed")

    return {
        "score": anomaly_score,
        "level": level,
        "deviation": deviation,
        "deviation_ratio": deviation_ratio,
        "baseline_value": expected_value,
        "current_value": current_value,
        "evidence": evidence
    }


# Convenience functions for external use
def get_facility_baseline(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract facility baseline information from event context.

    Args:
        event: Normalized event dictionary

    Returns:
        Baseline information dictionary
    """
    historical_context = event.get('historical_context', {})
    if not historical_context:
        return {"status": "NO_DATA"}

    # In a real implementation, this would connect to a database or time-series store
    # For MVP, we use the simplified historical context provided
    baseline_value = historical_context.get('baseline_value', 0.0)
    historical_count = historical_context.get('historical_observation_count', 0)

    # Extract current thermal value from event (same as in anomaly detection)
    thermal_features = event.get('thermal_features', {})
    current_value = (
        thermal_features.get('thermal_intensity') or
        event.get('frp', 0.0) or
        thermal_features.get('brightness_temperature', 0.0)
    )

    if historical_count == 0:
        return {"status": "NO_DATA"}
    elif historical_count < 5:
        return {
            "status": "INSUFFICIENT_DATA",
            "expected_value": baseline_value,
            "sample_count": historical_count
        }
    else:
        # Estimate variability - in reality would come from historical data
        variability = baseline_value * 0.2 if baseline_value > 0 else 5.0
        deviation = current_value - baseline_value
        deviation_ratio = deviation / baseline_value if baseline_value != 0 else float('inf') if current_value > 0 else 0.0
        return {
            "status": "AVAILABLE",
            "expected_value": baseline_value,
            "variability": variability,
            "sample_count": historical_count,
            "deviation": deviation,
            "deviation_ratio": deviation_ratio
        }