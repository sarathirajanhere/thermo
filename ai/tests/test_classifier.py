"""
Tests for the thermal event classifier.
"""

import unittest
import sys
import os

# Add the project root to the path so we can import ai modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ai.inference.classifier import ThermalClassifier, classify_event


class TestThermalClassifier(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.classifier = ThermalClassifier()

    def test_classifier_initialization(self):
        """Test that classifier initializes correctly."""
        self.assertIsInstance(self.classifier, ThermalClassifier)
        self.assertEqual(len(self.classifier.classes), 5)
        self.assertIn("Industrial Fire", self.classifier.classes)
        self.assertIn("Gas Flare", self.classifier.classes)
        self.assertIn("Forest Fire", self.classifier.classes)
        self.assertIn("Crop Burning", self.classifier.classes)
        self.assertIn("Other", self.classifier.classes)

    def test_industrial_fire_classification(self):
        """Test classification of industrial fire event."""
        event = {
            "event_id": "TEST-001",
            "timestamp": "2026-09-07T10:30:00Z",
            "latitude": 12.3456,
            "longitude": 78.9012,
            "frp": 35.0,
            "confidence": 0.9,
            "thermal_features": {
                "thermal_intensity": 35.0
            },
            "temporal_features": {
                "observation_count": 4,
                "duration_minutes": 30.0,
                "persistence_score": 0.7
            },
            "spatial_context": {
                "context_type": "Industrial Facility",
                "facility_id": "FAC-001",
                "facility_name": "Test Plant",
                "inside_facility": True,
                "nearby_features": ["Storage Tanks", "Processing Unit"]
            },
            "historical_context": {
                "baseline_value": 15.0,
                "historical_observation_count": 20
            }
        }

        result = self.classifier.predict(event)

        # Should classify as Industrial Fire with reasonable confidence
        self.assertEqual(result["label"], "Industrial Fire")
        self.assertGreater(result["confidence"], 0.5)
        self.assertIsInstance(result["evidence"], list)
        self.assertGreater(len(result["evidence"]), 0)

    def test_gas_flare_classification(self):
        """Test classification of gas flare event."""
        event = {
            "event_id": "TEST-002",
            "timestamp": "2026-09-07T10:30:00Z",
            "latitude": 12.3456,
            "longitude": 78.9012,
            "frp": 12.0,
            "confidence": 0.85,
            "thermal_features": {
                "thermal_intensity": 12.0
            },
            "temporal_features": {
                "observation_count": 5,
                "duration_minutes": 40.0,
                "persistence_score": 0.8
            },
            "spatial_context": {
                "context_type": "Industrial Facility",
                "facility_id": "FAC-001",
                "facility_name": "Test Plant",
                "inside_facility": True,
                "nearby_features": ["Storage Tanks", "Pipeline", "Flare Stack"]
            },
            "historical_context": {
                "baseline_value": 11.0,
                "historical_observation_count": 25
            }
        }

        result = self.classifier.predict(event)

        # Should classify as Gas Flare
        self.assertEqual(result["label"], "Gas Flare")
        self.assertGreater(result["confidence"], 0.4)
        self.assertIsInstance(result["evidence"], list)

    def test_forest_fire_classification(self):
        """Test classification of forest fire event."""
        event = {
            "event_id": "TEST-003",
            "timestamp": "2026-09-07T10:30:00Z",
            "latitude": 12.5000,
            "longitude": 79.0000,
            "frp": 25.0,
            "confidence": 0.8,
            "thermal_features": {
                "thermal_intensity": 25.0
            },
            "temporal_features": {
                "observation_count": 3,
                "duration_minutes": 35.0,
                "persistence_score": 0.6
            },
            "spatial_context": {
                "context_type": "Forest",
                "facility_id": None,
                "facility_name": None,
                "inside_facility": False,
                "nearby_features": ["Tree Cover", "Vegetation"]
            },
            "historical_context": {
                "baseline_value": 2.0,
                "historical_observation_count": 5
            }
        }

        result = self.classifier.predict(event)

        # Should classify as Forest Fire
        self.assertEqual(result["label"], "Forest Fire")
        self.assertGreater(result["confidence"], 0.4)
        self.assertIsInstance(result["evidence"], list)

    def test_crop_burning_classification(self):
        """Test classification of crop burning event."""
        event = {
            "event_id": "TEST-004",
            "timestamp": "2026-09-07T10:30:00Z",
            "latitude": 12.6000,
            "longitude": 79.1000,
            "frp": 18.0,
            "confidence": 0.75,
            "thermal_features": {
                "thermal_intensity": 18.0
            },
            "temporal_features": {
                "observation_count": 4,
                "duration_minutes": 45.0,
                "persistence_score": 0.7
            },
            "spatial_context": {
                "context_type": "Agricultural Land",
                "facility_id": None,
                "facility_name": None,
                "inside_facility": False,
                "nearby_features": ["Crop Field", "Irrigation"]
            },
            "historical_context": {
                "baseline_value": 3.0,
                "historical_observation_count": 8
            }
        }

        result = self.classifier.predict(event)

        # Should classify as Crop Burning
        self.assertEqual(result["label"], "Crop Burning")
        self.assertGreater(result["confidence"], 0.3)
        self.assertIsInstance(result["evidence"], list)

    def test_other_classification(self):
        """Test classification of unclear/other event."""
        event = {
            "event_id": "TEST-005",
            "timestamp": "2026-09-07T10:30:00Z",
            "latitude": 12.7000,
            "longitude": 79.2000,
            "frp": 8.0,
            "confidence": 0.6,
            "thermal_features": {
                "thermal_intensity": 8.0
            },
            "temporal_features": {
                "observation_count": 1,
                "duration_minutes": 5.0,
                "persistence_score": 0.2
            },
            "spatial_context": {
                "context_type": "Other",
                "facility_id": None,
                "facility_name": None,
                "inside_facility": False,
                "nearby_features": []
            },
            "historical_context": {
                "baseline_value": 1.0,
                "historical_observation_count": 2
            }
        }

        result = self.classifier.predict(event)

        # Should classify as Other
        self.assertEqual(result["label"], "Other")
        self.assertIsInstance(result["confidence"], float)
        self.assertIsInstance(result["evidence"], list)

    def test_classify_event_convenience_function(self):
        """Test the convenience classify_event function."""
        event = {
            "event_id": "TEST-006",
            "timestamp": "2026-09-07T10:30:00Z",
            "latitude": 12.3456,
            "longitude": 78.9012,
            "frp": 28.0,
            "confidence": 0.88,
            "thermal_features": {
                "thermal_intensity": 28.0
            },
            "temporal_features": {
                "observation_count": 3,
                "duration_minutes": 25.0,
                "persistence_score": 0.6
            },
            "spatial_context": {
                "context_type": "Industrial Facility",
                "facility_id": "FAC-001",
                "facility_name": "Test Plant",
                "inside_facility": True,
                "nearby_features": ["Storage Tanks"]
            },
            "historical_context": {
                "baseline_value": 12.0,
                "historical_observation_count": 15
            }
        }

        result = classify_event(event)

        self.assertIsInstance(result, dict)
        self.assertIn("label", result)
        self.assertIn("confidence", result)
        self.assertIn("evidence", result)
        self.assertIsInstance(result["label"], str)
        self.assertIsInstance(result["confidence"], float)
        self.assertIsInstance(result["evidence"], list)


if __name__ == '__main__':
    unittest.main()