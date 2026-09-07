"""
Temporal feature extraction for ThermoGuard AI.
Extracts features from temporal patterns in thermal observations.
"""

from typing import Dict, Any, Optional
import math


def extract_temporal_features(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract temporal features from event observations.

    Args:
        event: Normalized event dictionary with temporal_features

    Returns:
        Dictionary of temporal features
    """
    features = {}
    temporal = event.get('temporal_features', {})

    # Observation count - persistence indicator
    obs_count = temporal.get('observation_count', 0)
    features['observation_count'] = obs_count
    features['observation_count_log'] = math.log(obs_count + 1.0) if obs_count > 0 else 0.0
    features['is_persistent'] = 1.0 if obs_count >= 3 else 0.0  # 3+ observations suggests persistent event

    # Duration in minutes
    duration = temporal.get('duration_minutes', 0.0)
    features['duration_minutes'] = duration
    features['duration_log'] = math.log(duration + 1.0) if duration > 0 else 0.0
    features['is_long_duration'] = 1.0 if duration >= 30.0 else 0.0  # 30+ minutes suggests sustained activity

    # Persistence score (0-1) - already normalized in input
    persistence = temporal.get('persistence_score', 0.0)
    features['persistence_score'] = persistence
    features['high_persistence'] = 1.0 if persistence >= 0.7 else 0.0

    # Calculate observation frequency if we had timestamps (simplified)
    # In a real implementation, we'd compute events per hour from timestamps
    if duration > 0 and obs_count > 0:
        features['obs_per_minute'] = obs_count / duration
        features['obs_per_hour'] = obs_count / (duration / 60.0) if duration > 0 else 0.0
    else:
        features['obs_per_minute'] = 0.0
        features['obs_per_hour'] = 0.0

    return features


def extract_temporal_trends(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract temporal trend features by comparing with historical data.

    Args:
        event: Normalized event dictionary with historical_context

    Returns:
        Dictionary of temporal trend features
    """
    features = {}
    historical = event.get('historical_context', {})

    # Current vs historical comparison
    current_value = event.get('thermal_features', {}).get('thermal_intensity') or event.get('frp', 0.0)
    baseline_value = historical.get('baseline_value', 0.0)
    historical_count = historical.get('historical_observation_count', 0)

    # Avoid division by zero
    if baseline_value > 0:
        features['deviation_ratio'] = (current_value - baseline_value) / baseline_value
        features['current_to_baseline_ratio'] = current_value / baseline_value
    else:
        features['deviation_ratio'] = 0.0 if current_value == 0 else float('inf') if current_value > 0 else 0.0
        features['current_to_baseline_ratio'] = float('inf') if current_value > 0 else 1.0

    # Absolute deviation
    features['absolute_deviation'] = abs(current_value - baseline_value)

    # Historical data sufficiency
    features['historical_data_sufficient'] = 1.0 if historical_count >= 10 else 0.0
    features['historical_count_normalized'] = min(historical_count / 30.0, 1.0)  # Normalize to 30 observations

    # Trend direction
    features['is_increasing'] = 1.0 if current_value > baseline_value else 0.0
    features['is_decreasing'] = 1.0 if current_value < baseline_value else 0.0
    features['is_stable'] = 1.0 if abs(current_value - baseline_value) < (baseline_value * 0.1) else 0.0  # Within 10%

    # Z-score style normalization (simplified)
    # In reality, we'd need historical std dev, but we'll use a placeholder for demo
    if historical_count >= 5:
        # Placeholder std dev estimation - in reality would come from historical data
        estimated_std = baseline_value * 0.3  # Assume 30% variation as placeholder
        if estimated_std > 0:
            features['z_score'] = (current_value - baseline_value) / estimated_std
        else:
            features['z_score'] = 0.0
    else:
        features['z_score'] = 0.0

    return features