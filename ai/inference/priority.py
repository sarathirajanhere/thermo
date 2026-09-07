"""
Priority scoring engine for ThermoGuard AI.
Converts classification, baseline, and anomaly results into priority levels.
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class PriorityEngine:
    """
    Assigns priority levels to thermal events based on multiple factors:
    - Classification type
    - Industrial context
    - Anomaly score
    - Baseline deviation
    - Persistence
    - Confidence

    Priority levels: LOW, MODERATE, HIGH, CRITICAL
    """

    def __init__(self):
        logger.info("PriorityEngine initialized")

    def prioritize(
        self,
        classification: Dict[str, Any],
        baseline: Dict[str, Any],
        anomaly: Dict[str, Any],
        event: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Calculate priority score and severity level for an event.

        Args:
            classification: Result from classification step
            baseline: Result from baseline analysis
            anomaly: Result from anomaly detection
            event: Original event dictionary (optional, for additional context)

        Returns:
            Priority result with severity level, score, and evidence
        """
        try:
            # Extract key components
            class_label = classification.get('label', 'Other')
            class_confidence = classification.get('confidence', 0.0)
            class_evidence = classification.get('evidence', [])

            anomaly_score = anomaly.get('score', 0.0)
            anomaly_level = anomaly.get('level', 'UNKNOWN')
            anomaly_evidence = anomaly.get('evidence', [])

            baseline_status = baseline.get('status', 'NO_DATA')
            baseline_deviation = baseline.get('deviation_ratio', 0.0) if isinstance(baseline.get('deviation_ratio'), (int, float)) else 0.0

            # Extract event context
            spatial_context = event.get('spatial_context', {}) if event else {}
            temporal_features = event.get('temporal_features', {}) if event else {}
            inside_facility = spatial_context.get('inside_facility', False)
            context_type = spatial_context.get('context_type', 'Other')
            confidence = event.get('confidence', 0.0) if event else 0.0
            persistence_score = temporal_features.get('persistence_score', 0.0) if temporal_features else 0.0
            observation_count = temporal_features.get('observation_count', 0) if temporal_features else 0

            # Calculate base priority score
            priority_score = self._calculate_base_priority(
                class_label, class_confidence, anomaly_score, baseline_status,
                baseline_deviation, inside_facility, context_type, confidence,
                persistence_score, observation_count
            )

            # Determine severity level
            severity = self._score_to_severity(priority_score)

            # Generate evidence
            evidence = self._generate_priority_evidence(
                class_label, class_confidence, anomaly_score, anomaly_level,
                baseline_status, baseline_deviation, inside_facility, context_type,
                persistence_score, observation_count, class_evidence, anomaly_evidence
            )

            result = {
                "severity": severity,
                "score": priority_score,
                "evidence": evidence
            }

            logger.debug(f"Priority result: {result}")
            return result

        except Exception as e:
            logger.error(f"Error in priority calculation: {str(e)}")
            # Return safe fallback
            return {
                "severity": "MODERATE",  # Safe middle ground
                "score": 0.5,
                "evidence": ["Priority calculation error - defaulting to MODERATE"]
            }

    def _calculate_base_priority(
        self,
        class_label: str,
        class_confidence: float,
        anomaly_score: float,
        baseline_status: str,
        baseline_deviation: float,
        inside_facility: bool,
        context_type: str,
        confidence: float,
        persistence_score: float,
        observation_count: int
    ) -> float:
        """Calculate the base priority score (0-1)."""
        score = 0.0

        # 1. Classification contribution (0-0.3)
        class_weights = {
            "Industrial Fire": 0.3,
            "Potential Industrial Fire": 0.3,  # Assuming this might be used
            "Gas Flare": 0.1,  # Lower priority for routine flares
            "Forest Fire": 0.2,
            "Crop Burning": 0.15,
            "Other": 0.1
        }
        class_score = class_weights.get(class_label, 0.1) * class_confidence
        score += class_score

        # 2. Anomaly contribution (0-0.3)
        anomaly_weight = 0.3
        score += anomaly_score * anomaly_weight

        # 3. Baseline deviation contribution (0-0.2)
        # Only applies if we have sufficient baseline data
        if baseline_status == "AVAILABLE":
            deviation_score = min(1.0, abs(baseline_deviation) / 2.0)  # Cap at 2x deviation
            score += deviation_score * 0.2
        elif baseline_status == "INSUFFICIENT_DATA":
            # Still give some weight if we have some data
            score += 0.05

        # 4. Industrial context boost (0-0.1)
        if inside_facility or context_type == "Industrial Facility":
            score += 0.1

        # 5. Persistence contribution (0-0.05)
        persistence_component = persistence_score * 0.05
        score += persistence_component

        # 6. Observation count contribution (0-0.05)
        obs_component = min(0.05, observation_count / 40.0)  # Max at 40+ observations
        score += obs_component

        # 7. Confidence contribution (0-0.05)
        confidence_component = confidence * 0.05
        score += confidence_component

        # 8. NON-INDUSTRIAL CONTEXT REDUCTION
        # Key ThermoGuard principle: non-industrial events should not get CRITICAL priority
        # regardless of anomaly score, as they are not industrial safety concerns
        if context_type in ["Forest", "Agricultural Land"] or not inside_facility:
            # Apply reduction factor for non-industrial contexts
            # This ensures forest fires, crop burning, etc. don't get incorrectly prioritized as CRITICAL
            # for industrial safety response
            if context_type == "Forest":
                score *= 0.6  # Reduce forest fire priority by 40%
            elif context_type == "Agricultural Land":
                score *= 0.7  # Reduce crop burning priority by 30%
            else:
                score *= 0.8  # General non-industrial reduction

        # Ensure score is in [0, 1] range
        return max(0.0, min(1.0, score))

    def _score_to_severity(self, score: float) -> str:
        """Convert numerical score to severity level."""
        if score < 0.25:
            return "LOW"
        elif score < 0.5:
            return "MODERATE"
        elif score < 0.75:
            return "HIGH"
        else:
            return "CRITICAL"

    def _generate_priority_evidence(
        self,
        class_label: str,
        class_confidence: float,
        anomaly_score: float,
        anomaly_level: str,
        baseline_status: str,
        baseline_deviation: float,
        inside_facility: bool,
        context_type: str,
        persistence_score: float,
        observation_count: int,
        class_evidence: List[str],
        anomaly_evidence: List[str]
    ) -> List[str]:
        """Generate human-readable evidence for the priority decision."""
        evidence = []

        # Classification evidence
        if class_confidence > 0.5:
            evidence.append(f"Classified as {class_label} (confidence: {class_confidence:.2f})")
        else:
            evidence.append(f"Classified as {class_label} with low confidence")

        # Anomaly evidence
        if anomaly_score > 0.6:
            evidence.append(f"High anomaly score: {anomaly_score:.2f}")
        elif anomaly_score > 0.3:
            evidence.append(f"Moderate anomaly score: {anomaly_score:.2f}")

        # Baseline evidence
        if baseline_status == "AVAILABLE":
            if abs(baseline_deviation) > 1.0:
                evidence.append(f"Significant deviation from facility baseline ({baseline_deviation:.1f}x)")
            elif abs(baseline_deviation) > 0.5:
                evidence.append(f"Moderate deviation from facility baseline ({baseline_deviation:.1f}x)")
        elif baseline_status == "INSUFFICIENT_DATA":
            evidence.append("Limited historical data for baseline comparison")

        # Context evidence
        if inside_facility:
            evidence.append("Event located inside industrial facility")
        elif context_type == "Industrial Facility":
            evidence.append("Event in industrial context")

        # Persistence evidence
        if persistence_score > 0.7:
            evidence.append(f"High persistence score: {persistence_score:.2f}")
        elif observation_count >= 5:
            evidence.append(f"Multiple observations: {observation_count}")

        # Add top evidence from classification and anomaly (avoid duplication)
        all_evidence = list(class_evidence) + list(anomaly_evidence)
        seen = set()
        for ev in all_evidence:
            if ev not in seen and len(evidence) < 8:  # Limit total evidence
                evidence.append(ev)
                seen.add(ev)

        # Ensure we have at least some evidence
        if not evidence:
            evidence.append("Priority assessment completed based on available data")

        return evidence[:8]  # Final limit


def prioritize_event(
    classification: Dict[str, Any],
    baseline: Dict[str, Any],
    anomaly: Dict[str, Any],
    event: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Convenience function for priority calculation.

    Args:
        classification: Result from classification step
        baseline: Result from baseline analysis
        anomaly: Result from anomaly detection
        event: Original event dictionary (optional)

    Returns:
        Priority result
    """
    engine = PriorityEngine()
    return engine.prioritize(classification, baseline, anomaly, event)