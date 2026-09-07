"""
Thermal feature extraction for ThermoGuard AI.
Extracts features from FIRMS thermal observations.
"""

import math
from typing import Dict, Any, Optional


def extract_thermal_features(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract thermal features from a FIRMS event.

    Args:
        event: Normalized FIRMS event dictionary

    Returns:
        Dictionary of thermal features
    """
    features = {}

    # Basic FRP (Fire Radiative Power) - key indicator of intensity
    frp = event.get('frp', 0.0)
    features['frp'] = frp
    features['frp_log'] = math.log(frp + 1.0) if frp > 0 else 0.0

    # Confidence of detection (0-1)
    confidence = event.get('confidence', 0.0)
    features['confidence'] = confidence

    # Brightness temperature if available
    brightness_temp = event.get('thermal_features', {}).get('brightness_temperature')
    if brightness_temp is not None:
        features['brightness_temperature'] = float(brightness_temp)
        features['brightness_temp_normalized'] = (brightness_temp - 300) / 50  # Normalize around typical values
    else:
        features['brightness_temperature'] = None
        features['brightness_temp_normalized'] = 0.0

    # Thermal intensity from features or fallback to FRP
    thermal_intensity = event.get('thermal_features', {}).get('thermal_intensity', frp)
    features['thermal_intensity'] = thermal_intensity
    features['thermal_intensity_log'] = math.log(thermal_intensity + 1.0) if thermal_intensity > 0 else 0.0

    return features


def extract_thermal_ratios(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract ratio-based thermal features for normalization.

    Args:
        event: Normalized FIRMS event dictionary

    Returns:
        Dictionary of thermal ratio features
    """
    features = {}

    frp = event.get('frp', 0.0)
    confidence = event.get('confidence', 0.0)

    # Confidence-weighted FRP
    features['confidence_weighted_frp'] = frp * confidence

    # Thermal intensity per unit confidence (avoid division by zero)
    if confidence > 0:
        features['intensity_per_confidence'] = frp / confidence
    else:
        features['intensity_per_confidence'] = 0.0

    return features