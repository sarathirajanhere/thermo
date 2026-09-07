"""
Spatial feature extraction for ThermoGuard AI.
Extracts features from geospatial context provided by OSM/enrichment layer.
"""

import math
from typing import Dict, Any, List, Optional


def extract_spatial_features(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract spatial features from event context.

    Args:
        event: Normalized event dictionary with spatial_context

    Returns:
        Dictionary of spatial features
    """
    features = {}
    spatial_context = event.get('spatial_context', {})

    # Context type encoding (one-hot style)
    context_type = spatial_context.get('context_type', 'Other')
    features['context_industrial'] = 1.0 if context_type == 'Industrial Facility' else 0.0
    features['context_agricultural'] = 1.0 if context_type == 'Agricultural Land' else 0.0
    features['context_forest'] = 1.0 if context_type == 'Forest' else 0.0
    features['context_other'] = 1.0 if context_type not in ['Industrial Facility', 'Agricultural Land', 'Forest'] else 0.0

    # Facility relationship
    features['inside_facility'] = 1.0 if spatial_context.get('inside_facility', False) else 0.0
    features['distance_to_facility'] = float(spatial_context.get('distance_to_facility', 0.0))
    features['distance_to_facility_normalized'] = min(features['distance_to_facility'] / 1000.0, 1.0)  # Normalize to km, cap at 1

    # Nearby infrastructure count and types
    nearby_features = spatial_context.get('nearby_features', [])
    features['nearby_feature_count'] = len(nearby_features)

    # Specific infrastructure types that might indicate higher risk
    high_risk_indicators = ['Storage Tanks', 'Pipeline', 'Processing Unit', 'Refinery', 'Chemical Plant']
    features['nearby_high_risk_count'] = sum(1 for feature in nearby_features if feature in high_risk_indicators)
    features['nearby_high_risk_ratio'] = features['nearby_high_risk_count'] / max(len(nearby_features), 1)

    # Facility identification
    facility_id = spatial_context.get('facility_id', '')
    features['has_facility_id'] = 1.0 if facility_id else 0.0
    # In a real implementation, we might hash facility_id for privacy, but for demo we keep it simple

    return features


def extract_spatial_context_summary(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract summary/context information for explainability.

    Args:
        event: Normalized event dictionary

    Returns:
        Dictionary of contextual information for evidence generation
    """
    spatial_context = event.get('spatial_context', {})

    summary = {
        'context_type': spatial_context.get('context_type', 'Unknown'),
        'facility_name': spatial_context.get('facility_name', 'Unknown'),
        'facility_id': spatial_context.get('facility_id', 'Unknown'),
        'inside_facility': spatial_context.get('inside_facility', False),
        'distance_to_facility': spatial_context.get('distance_to_facility', 0.0),
        'nearby_features': spatial_context.get('nearby_features', []),
        'is_industrial': spatial_context.get('context_type') == 'Industrial Facility'
    }

    return summary