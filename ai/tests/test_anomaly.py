"""
Tests for the anomaly detection engine.
"""

import unittest
import sys
import os

# Add the project root to the path so we can import ai modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ai.inference.anomaly import AnomalyDetector, detect_anomaly
from ai.inference.baseline import get_facility_baseline


class TestAnomalyDetection(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.detector = AnomalyDetector()

    def test_detector_initialization(self):
        """Test that detector initializes correctly."""
        self.assertIsInstance(self.detector, AnomalyDetector)

    def test_insufficient_baseline_handling(self):
        """Test handling of insufficient baseline data."""
        event = {
            "event_id": "TEST-001",
            "frp": 50.0,
            "confidence": 0.9,
            "historical_context": {},  # No historical data
            "thermal_features": {"thermal_intensity": 50.0},
            "temporal_features": {"persistence_score": 0.5, "observation_count": 2},
            "spatial_context": {"context_type": "Industrial Facility", "inside_facility": True}
        }

        baseline_info = get_facility_baseline(event)
        self.assertEqual(baseline_info["status"], "NO_DATA")

        result = self.detector.detect_anomaly(event, baseline_info)

        # Should handle gracefully and possibly flag extreme values
        self.assertIn("level", result)
        self.assertIn("score", result)
        self.assertIn("evidence", result)

    def test_statistical_anomaly_detection(self):
        """Test statistical anomaly detection with sufficient baseline."""
        event = {
            "event_id": "TEST-002",
            "frp": 30.0,
            "confidence": 0.85,
            "thermal_features": {"thermal_intensity": 30.0},
            "temporal_features": {"persistence_score": 0.6, "observation_count": 3},
            "spatial_context": {"context_type": "Industrial Facility", "inside_facility": True},
            "historical_context": {
                "baseline_value": 12.0,
                "historical_observation_count": 20
            }
        }

        baseline_info = get_facility_baseline(event)
        self.assertEqual(baseline_info["status"], "AVAILABLE")

        result = self.detector.detect_anomaly(event, baseline_info)

        # Should detect anomaly due to high deviation from baseline
        self.assertGreater(result["score"], 0.3)  # Should be elevated
        self.assertIn(result["level"], ["LOW", "MEDIUM", "HIGH"])
        self.assertIsInstance(result["evidence"], list)

    def test_extreme_frp_anomaly(self):
        """Test that extreme FRP values are flagged as anomalies."""
        event = {
            "event_id": "TEST-003",
            "frp": 120.0,  # Very high FRP
            "confidence": 0.9,
            "thermal_features": {"thermal_intensity": 120.0},
            "temporal_features": {"persistence_score": 0.5, "observation_count": 2},
            "spatial_context": {"context_type": "Industrial Facility", "inside_facility": True},
            "historical_context": {
                "baseline_value": 15.0,
                "historical_observation_count": 10
            }
        }

        result = detect_anomaly(event)  # Uses convenience function

        # Should be flagged as high anomaly due to extreme FRP
        self.assertGreater(result["score"], 0.7)
        self.assertEqual(result["level"], "HIGH")
        self.assertTrue(any("Extreme" in evidence for evidence in result["evidence"]))

    def test_persistence_boost(self):
        """Test that persistence boosts anomaly score."""
        base_event = {
            "event_id": "TEST-004",
            "frp": 25.0,
            "confidence": 0.8,
            "thermal_features": {"thermal_intensity": 25.0},
            "temporal_features": {"persistence_score": 0.5, "observation_count": 3},
            "spatial_context": {"context_type": "Industrial Facility", "inside_facility": True},
            "historical_context": {
                "baseline_value": 15.0,
                "historical_observation_count": 15
            }
        }

        # Low persistence event
        low_persistence_event = base_event.copy()
        low_persistence_event["temporal_features"]["persistence_score"] = 0.2

        # High persistence event
        high_persistence_event = base_event.copy()
        high_persistence_event["temporal_features"]["persistence_score"] = 0.8

        low_result = detect_anomaly(low_persistence_event)
        high_result = detect_anomaly(high_persistence_event)

        # High persistence should have higher or equal anomaly score
        self.assertGreaterEqual(high_result["score"], low_result["score"])

    def test_industrial_context_boost(self):
        """Test that industrial context boosts anomaly significance."""
        base_event = {
            "event_id": "TEST-005",
            "frp": 20.0,
            "confidence": 0.75,
            "thermal_features": {"thermal_intensity": 20.0},
            "temporal_features": {"persistence_score": 0.5, "observation_count": 3},
            "historical_context": {
                "baseline_value": 12.0,
                "historical_observation_count": 12
            }
        }

        # Non-industrial context
        non_industrial_event = base_event.copy()
        non_industrial_event["spatial_context"] = {
            "context_type": "Forest",
            "inside_facility": False
        }

        # Industrial context
        industrial_event = base_event.copy()
        industrial_event["spatial_context"] = {
            "context_type": "Industrial Facility",
            "inside_facility": True,
            "nearby_features": ["Storage Tanks", "Pipeline"]
        }

        non_industrial_result = detect_anomaly(non_industrial_event)
        industrial_result = detect_anomaly(industrial_event)

        # Industrial context should boost the score
        self.assertGreaterEqual(industrial_result["score"], non_industrial_result["score"])

    def test_confidence_boost(self):
        """Test that high confidence boosts anomaly score."""
        base_event = {
            "event_id": "TEST-006",
            "frp": 22.0,
            "thermal_features": {"thermal_intensity": 22.0},
            "temporal_features": {"persistence_score": 0.5, "observation_count": 3},
            "spatial_context": {"context_type": "Industrial Facility", "inside_facility": True},
            "historical_context": {
                "baseline_value": 15.0,
                "historical_observation_count": 15
            }
        }

        # Low confidence
        low_conf_event = base_event.copy()
        low_conf_event["confidence"] = 0.4

        # High confidence
        high_conf_event = base_event.copy()
        high_conf_event["confidence"] = 0.9

        low_result = detect_anomaly(low_conf_event)
        high_result = detect_anomaly(high_conf_event)

        # High confidence should boost the score
        self.assertGreaterEqual(high_result["score"], low_result["score"])

    def test_detect_anomaly_convenience_function(self):
        """Test the convenience detect_anomaly function."""
        event = {
            "event_id": "TEST-007",
            "frp": 18.0,
            "confidence": 0.8,
            "thermal_features": {"thermal_intensity": 18.0},
            "temporal_features": {"persistence_score": 0.6, "observation_count": 4},
            "spatial_context": {
                "context_type": "Industrial Facility",
                "facility_id": "FAC-001",
                "inside_facility": True,
                "nearby_features": ["Storage Tanks"]
            },
            "historical_context": {
                "baseline_value": 12.0,
                "historical_observation_count": 18
            }
        }

        result = detect_anomaly(event)

        self.assertIsInstance(result, dict)
        self.assertIn("score", result)
        self.assertIn("level", result)
        self.assertIn("evidence", result)
        self.assertIsInstance(result["score"], float)
        self.assertIsInstance(result["level"], str)
        self.assertIsInstance(result["evidence"], list)
        self.assertGreaterEqual(result["score"], 0.0)
        self.assertLessEqual(result["score"], 1.0)


if __name__ == '__main__':
    unittest.main()