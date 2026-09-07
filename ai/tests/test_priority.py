"""
Tests for the priority scoring engine.
"""

import unittest
import sys
import os

# Add the project root to the path so we can import ai modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ai.inference.priority import PriorityEngine, prioritize_event


class TestPriorityEngine(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.engine = PriorityEngine()

    def test_priority_engine_initialization(self):
        """Test that priority engine initializes correctly."""
        self.assertIsInstance(self.engine, PriorityEngine)

    def test_low_priority_event(self):
        """Test priority calculation for low priority event (routine gas flare)."""
        classification = {
            "label": "Gas Flare",
            "confidence": 0.8,
            "evidence": ["Industrial facility with flare infrastructure"]
        }
        baseline = {
            "status": "AVAILABLE",
            "expected_value": 17.0,
            "deviation_ratio": 0.1  # 10% above baseline
        }
        anomaly = {
            "score": 0.2,
            "level": "LOW",
            "evidence": ["Minimal deviation from baseline"]
        }
        event = {
            "spatial_context": {
                "inside_facility": True,
                "context_type": "Industrial Facility"
            },
            "temporal_features": {
                "persistence_score": 0.6,
                "observation_count": 4
            },
            "confidence": 0.8
        }

        result = self.engine.prioritize(classification, baseline, anomaly, event)

        # Should be LOW or MODERATE priority
        self.assertIn(result["severity"], ["LOW", "MODERATE"])
        self.assertGreaterEqual(result["score"], 0.0)
        self.assertLessEqual(result["score"], 1.0)
        self.assertIsInstance(result["evidence"], list)

    def test_high_priority_event(self):
        """Test priority calculation for high priority event."""
        classification = {
            "label": "Industrial Fire",
            "confidence": 0.9,
            "evidence": ["Industrial facility with high thermal intensity"]
        }
        baseline = {
            "status": "AVAILABLE",
            "expected_value": 15.0,
            "deviation_ratio": 2.0  # 2x baseline - significant deviation
        }
        anomaly = {
            "score": 0.8,
            "level": "HIGH",
            "evidence": ["Significant deviation from baseline", "Persistent thermal activity"]
        }
        event = {
            "spatial_context": {
                "inside_facility": True,
                "context_type": "Industrial Facility"
            },
            "temporal_features": {
                "persistence_score": 0.8,
                "observation_count": 6
            },
            "confidence": 0.9
        }

        result = self.engine.prioritize(classification, baseline, anomaly, event)

        # Should be HIGH or CRITICAL priority
        self.assertIn(result["severity"], ["HIGH", "CRITICAL"])
        self.assertGreater(result["score"], 0.5)
        self.assertIsInstance(result["evidence"], list)

    def test_critical_priority_event(self):
        """Test priority calculation for critical priority event."""
        classification = {
            "label": "Industrial Fire",
            "confidence": 0.95,
            "evidence": ["Industrial facility with high thermal intensity", "Significant deviation from facility baseline"]
        }
        baseline = {
            "status": "AVAILABLE",
            "expected_value": 12.0,
            "deviation_ratio": 3.0  # 3x baseline - major deviation
        }
        anomaly = {
            "score": 0.9,
            "level": "HIGH",
            "evidence": ["Major deviation from baseline", "High persistence", "Industrial facility context"]
        }
        event = {
            "spatial_context": {
                "inside_facility": True,
                "context_type": "Industrial Facility",
                "nearby_features": ["Storage Tanks", "Processing Unit", "Pipeline"]
            },
            "temporal_features": {
                "persistence_score": 0.9,
                "observation_count": 8
            },
            "confidence": 0.95
        }

        result = self.engine.prioritize(classification, baseline, anomaly, event)

        # Should be CRITICAL priority
        self.assertEqual(result["severity"], "CRITICAL")
        self.assertGreater(result["score"], 0.7)
        self.assertIsInstance(result["evidence"], list)
        # Should have multiple pieces of evidence
        self.assertGreater(len(result["evidence"]), 2)

    def test_non_industrial_low_priority(self):
        """Test that non-industrial events get lower priority even with high anomaly."""
        classification = {
            "label": "Forest Fire",
            "confidence": 0.85,
            "evidence": ["Forest land use context", "High thermal intensity"]
        }
        baseline = {
            "status": "AVAILABLE",
            "expected_value": 2.0,
            "deviation_ratio": 10.0  # High deviation but in forest context
        }
        anomaly = {
            "score": 0.85,
            "level": "HIGH",
            "evidence": ["Significant deviation from baseline"]
        }
        event = {
            "spatial_context": {
                "inside_facility": False,
                "context_type": "Forest"
            },
            "temporal_features": {
                "persistence_score": 0.7,
                "observation_count": 5
            },
            "confidence": 0.8
        }

        result = self.engine.prioritize(classification, baseline, anomaly, event)

        # Should be MODERATE or HIGH (not CRITICAL due to non-industrial context)
        self.assertIn(result["severity"], ["LOW", "MODERATE", "HIGH"])
        self.assertNotEqual(result["severity"], "CRITICAL")  # Should not be critical for forest fire
        self.assertIsInstance(result["evidence"], list)

    def test_score_to_severity_conversion(self):
        """Test conversion of numerical scores to severity levels."""
        self.assertEqual(self.engine._score_to_severity(0.1), "LOW")
        self.assertEqual(self.engine._score_to_severity(0.3), "MODERATE")
        self.assertEqual(self.engine._score_to_severity(0.6), "HIGH")
        self.assertEqual(self.engine._score_to_severity(0.8), "CRITICAL")
        self.assertEqual(self.engine._score_to_severity(0.0), "LOW")
        self.assertEqual(self.engine._score_to_severity(1.0), "CRITICAL")

    def test_prioritize_event_convenience_function(self):
        """Test the convenience prioritize_event function."""
        classification = {
            "label": "Gas Flare",
            "confidence": 0.75,
            "evidence": ["Industrial facility with flare infrastructure"]
        }
        baseline = {
            "status": "AVAILABLE",
            "expected_value": 16.0,
            "deviation_ratio": 0.2
        }
        anomaly = {
            "score": 0.3,
            "level": "LOW",
            "evidence": ["Minimal anomaly detected"]
        }
        event = {
            "spatial_context": {
                "inside_facility": True,
                "context_type": "Industrial Facility"
            },
            "temporal_features": {
                "persistence_score": 0.5,
                "observation_count": 3
            },
            "confidence": 0.75
        }

        result = prioritize_event(classification, baseline, anomaly, event)

        self.assertIsInstance(result, dict)
        self.assertIn("severity", result)
        self.assertIn("score", result)
        self.assertIn("evidence", result)
        self.assertIsInstance(result["severity"], str)
        self.assertIsInstance(result["score"], float)
        self.assertIsInstance(result["evidence"], list)
        self.assertIn(result["severity"], ["LOW", "MODERATE", "HIGH", "CRITICAL"])


if __name__ == '__main__':
    unittest.main()