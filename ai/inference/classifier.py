"""
Thermal event classifier for ThermoGuard AI.
Implements deterministic rule-based classification for MVP,
designed to be replaceable with trained XGBoost model.
"""

from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class ThermalClassifier:
    """
    Classifies thermal events into categories:
    - Industrial Fire
    - Gas Flare
    - Forest Fire
    - Crop Burning
    - Other

    For MVP, uses deterministic rules based on features.
    Designed to have same interface as ML model classifier.
    """

    def __init__(self):
        self.classes = [
            "Industrial Fire",
            "Gas Flare",
            "Forest Fire",
            "Crop Burning",
            "Other"
        ]
        logger.info("ThermalClassifier initialized (deterministic MVP version)")

    def predict(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a thermal event.

        Args:
            event: Normalized event dictionary with features

        Returns:
            Classification result with label, confidence, and evidence
        """
        try:
            # Extract features for classification
            features = self._extract_classification_features(event)

            # Apply classification rules
            class_label, confidence, evidence = self._apply_classification_rules(features, event)

            result = {
                "label": class_label,
                "confidence": confidence,
                "evidence": evidence
            }

            logger.debug(f"Classification result: {result}")
            return result

        except Exception as e:
            logger.error(f"Error in classification: {str(e)}")
            # Return safe fallback
            return {
                "label": "Other",
                "confidence": 0.1,
                "evidence": ["Classification error - defaulting to Other"]
            }

    def _extract_classification_features(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features specifically for classification decision."""
        from ..features.feature_pipeline import extract_all_features
        return extract_all_features(event)

    def _apply_classification_rules(self, features: Dict[str, Any], event: Dict[str, Any]) -> Tuple[str, float, list]:
        """
        Apply deterministic classification rules.

        Returns:
            Tuple of (class_label, confidence, evidence_list)
        """
        evidence = []

        # Extract key features
        context_type = features.get('context_type', 'Other')
        inside_facility = bool(features.get('inside_facility', False))
        frp = features.get('frp', 0.0)
        confidence_val = features.get('confidence', 0.0)
        persistence = features.get('persistence_score', 0.0)
        observation_count = features.get('observation_count', 0)

        # Nearby features
        nearby_features = features.get('nearby_features', [])
        nearby_high_risk = features.get('nearby_high_risk_count', 0)

        # Historical context
        deviation_ratio = features.get('deviation_ratio', 0.0)
        is_increasing = bool(features.get('is_increasing', False))

        # Rule 1: Industrial Facility with high FRP and deviation -> Industrial Fire
        if (context_type == 'Industrial Facility' or inside_facility) and frp > 25.0 and deviation_ratio > 1.0:
            evidence.append("Industrial facility with high thermal intensity")
            evidence.append("Significant deviation from facility baseline")
            if is_increasing:
                evidence.append("Increasing thermal trend")
            if observation_count >= 3:
                evidence.append("Persistent observations")
            return "Industrial Fire", min(0.95, 0.7 + (frp - 25) * 0.01 + deviation_ratio * 0.1), evidence

        # Rule 2: Industrial Facility with moderate FRP and known flare patterns -> Gas Flare
        if (context_type == 'Industrial Facility' or inside_facility) and frp > 5.0:
            # Check for flare indicators
            flare_indicators = ['Storage Tanks', 'Pipeline', 'Processing Unit', 'Flare Stack']
            has_flare_infrastructure = any(indicator in nearby_features for indicator in flare_indicators)

            if has_flare_infrastructure and deviation_ratio < 0.5 and persistence > 0.6:
                evidence.append("Industrial facility with flare infrastructure")
                evidence.append("Normal baseline deviation for facility")
                evidence.append("Persistent thermal activity")
                return "Gas Flare", min(0.9, 0.6 + persistence * 0.3), evidence
            elif has_flare_infrastructure:
                evidence.append("Industrial facility with flare infrastructure")
                evidence.append("Moderate thermal activity")
                return "Gas Flare", min(0.8, 0.5 + confidence_val * 0.3), evidence

        # Rule 3: Forest context -> Forest Fire
        if context_type == 'Forest' or features.get('context_forest', 0) > 0.5:
            evidence.append("Forest land use context")
            if frp > 15.0:
                evidence.append("High thermal intensity consistent with forest fire")
            if observation_count >= 2:
                evidence.append("Multiple observations suggesting persistence")
            return "Forest Fire", min(0.85, 0.5 + frp * 0.02), evidence

        # Rule 4: Agricultural context -> Crop Burning
        if context_type == 'Agricultural Land' or features.get('context_agricultural', 0) > 0.5:
            evidence.append("Agricultural land use context")
            if frp > 10.0:
                evidence.append("Thermal intensity consistent with crop residue burning")
            if persistence > 0.5:
                evidence.append("Persistent burning pattern")
            return "Crop Burning", min(0.8, 0.4 + frp * 0.03), evidence

        # Rule 5: High FRP without clear context -> Other (could be unknown industrial)
        if frp > 30.0:
            evidence.append("Very high thermal intensity")
            evidence.append("Unclear contextual classification")
            return "Other", min(0.75, 0.4 + frp * 0.01), evidence

        # Default: Other with low confidence
        evidence.append("No clear classification pattern detected")
        return "Other", max(0.1, confidence_val * 0.5), evidence


def classify_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function for classifying an event.

    Args:
        event: Normalized event dictionary

    Returns:
        Classification result
    """
    classifier = ThermalClassifier()
    return classifier.predict(event)