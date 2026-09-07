"""
Feature pipeline for ThermoGuard AI.
Combines thermal, spatial, and temporal features into a unified feature vector.
"""

from typing import Dict, Any, List
import logging

from .thermal_features import extract_thermal_features, extract_thermal_ratios
from .spatial_features import extract_spatial_features, extract_spatial_context_summary
from .temporal_features import extract_temporal_features, extract_temporal_trends

logger = logging.getLogger(__name__)


def extract_all_features(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract all features from an event for AI processing.

    Args:
        event: Normalized event dictionary

    Returns:
        Dictionary containing all extracted features
    """
    try:
        features = {}

        # Extract features from each domain
        thermal_features = extract_thermal_features(event)
        thermal_ratio_features = extract_thermal_ratios(event)
        spatial_features = extract_spatial_features(event)
        spatial_summary = extract_spatial_context_summary(event)
        temporal_features = extract_temporal_features(event)
        temporal_trends = extract_temporal_trends(event)

        # Combine all features
        features.update(thermal_features)
        features.update(thermal_ratio_features)
        features.update(spatial_features)
        features.update(spatial_summary)
        features.update(temporal_features)
        features.update(temporal_trends)

        # Add metadata
        features['_event_id'] = event.get('event_id', 'unknown')
        features['_timestamp'] = event.get('timestamp', '')

        logger.debug(f"Extracted {len(features)} features for event {features['_event_id']}")

        return features

    except Exception as e:
        logger.error(f"Error extracting features for event {event.get('event_id', 'unknown')}: {str(e)}")
        # Return minimal safe features to prevent crashes
        return {
            '_event_id': event.get('event_id', 'unknown'),
            '_timestamp': event.get('timestamp', ''),
            'frp': 0.0,
            'confidence': 0.0,
            'context_industrial': 0.0,
            'observation_count': 0,
            'persistence_score': 0.0,
            'deviation_ratio': 0.0
        }


def get_feature_names() -> List[str]:
    """
    Get list of feature names used by the model (excluding metadata).

    Returns:
        List of feature names
    """
    # This would ideally be derived from a trained model, but for MVP we define explicitly
    return [
        # Thermal features
        'frp', 'frp_log', 'confidence', 'brightness_temperature', 'brightness_temp_normalized',
        'thermal_intensity', 'thermal_intensity_log', 'confidence_weighted_frp', 'intensity_per_confidence',

        # Spatial features
        'context_industrial', 'context_agricultural', 'context_forest', 'context_other',
        'inside_facility', 'distance_to_facility', 'distance_to_facility_normalized',
        'nearby_feature_count', 'nearby_high_risk_count', 'nearby_high_risk_ratio',
        'has_facility_id',

        # Temporal features
        'observation_count', 'observation_count_log', 'is_persistent', 'duration_minutes',
        'duration_log', 'is_long_duration', 'persistence_score', 'high_persistence',
        'obs_per_minute', 'obs_per_hour',

        # Temporal trends
        'deviation_ratio', 'current_to_baseline_ratio', 'absolute_deviation',
        'historical_data_sufficient', 'historical_count_normalized',
        'is_increasing', 'is_decreasing', 'is_stable', 'z_score'
    ]


def filter_features_for_model(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter features to only those used by the model, removing metadata and handling missing values.

    Args:
        features: Dictionary of all extracted features

    Returns:
        Dictionary of features suitable for model input
    """
    feature_names = get_feature_names()
    filtered_features = {}

    for feature_name in feature_names:
        value = features.get(feature_name, 0.0)  # Default to 0.0 for missing features

        # Handle special values that could break ML models
        if isinstance(value, (int, float)):
            if math.isinf(value) or math.isnan(value):
                filtered_features[feature_name] = 0.0
            else:
                filtered_features[feature_name] = float(value)
        else:
            # Convert non-numeric to numeric if possible, otherwise default
            try:
                filtered_features[feature_name] = float(value)
            except (ValueError, TypeError):
                filtered_features[feature_name] = 0.0

    return filtered_features