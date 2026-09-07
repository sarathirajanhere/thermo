# ThermoGuard AI Module

This module contains the AI analytics layer for ThermoGuard AI, responsible for:
- Thermal event classification
- Facility-specific baseline analysis
- Anomaly detection
- Event severity/priority scoring
- Explainable evidence generation
- AI inference interfaces

## Structure

```
ai/
├── README.md
├── models/
│   ├── classifier_model.py
│   ├── anomaly_model.py
│   └── model_metadata.json
├── features/
│   ├── thermal_features.py
│   ├── spatial_features.py
│   ├── temporal_features.py
│   └── feature_pipeline.py
├── pipelines/
│   ├── classification_pipeline.py
│   └── anomaly_pipeline.py
├── training/
│   ├── train_classifier.py
│   ├── train_anomaly.py
│   └── configs/
├── inference/
│   ├── classifier.py
│   ├── baseline.py
│   ├── anomaly.py
│   └── priority.py
├── evaluation/
│   ├── evaluate_classifier.py
│   ├── evaluate_anomaly.py
│   └── metrics.json
└── tests/
    ├── test_classifier.py
    ├── test_baseline.py
    └── test_anomaly.py
```

## Responsibilities (Member 3 - AI/Analytics Lead)

1. Thermal-event classification
2. Facility-specific baseline analysis
3. Anomaly detection
4. Event severity / priority scoring
5. Explainable evidence generation
6. AI inference interfaces
7. AI-related tests
8. Integration of the AI engine with the existing backend/geospatial pipeline
9. Committing all completed work cleanly to the shared GitHub repository

## Data Contract

The AI module expects events in the following format (simplified for MVP):

```json
{
  "event_id": "TG-IND-0247",
  "timestamp": "2026-09-07T10:30:00Z",
  "latitude": 12.3456,
  "longitude": 78.9012,
  "sensor": "VIIRS",
  "confidence": 0.91,
  "frp": 42.5,
  "thermal_features": {
    "brightness_temperature": null,
    "thermal_intensity": 42.5
  },
  "temporal_features": {
    "observation_count": 5,
    "duration_minutes": 45,
    "persistence_score": 0.8
  },
  "spatial_context": {
    "context_type": "Industrial Facility",
    "facility_id": "FAC-001",
    "facility_name": "Demo Chemical Plant",
    "distance_to_facility": 0,
    "inside_facility": true,
    "nearby_features": [
      "Storage Tanks",
      "Pipeline",
      "Processing Unit"
    ]
  },
  "historical_context": {
    "baseline_value": 18.0,
    "current_value": 42.5,
    "historical_observation_count": 30
  }
}
```

The AI module returns an intelligence result in the format:

```json
{
  "event_id": "TG-IND-0247",
  "classification": {
    "label": "Potential Industrial Fire",
    "confidence": 0.93
  },
  "baseline": {
    "status": "AVAILABLE",
    "expected_value": 18.0,
    "current_value": 42.5,
    "deviation": 24.5
  },
  "anomaly": {
    "score": 0.88,
    "level": "HIGH"
  },
  "priority": {
    "severity": "CRITICAL",
    "score": 0.91
  },
  "evidence": [
    "Inside industrial facility",
    "Thermal intensity above facility baseline",
    "Abnormal temporal behavior"
  ]
}
```

## Implementation Notes

- For the 10-hour MVP, we implement deterministic, explainable baselines and rule-based classification.
- The architecture supports swapping in trained XGBoost/Scikit-learn models later.
- All inference functions are deterministic and JSON-safe.
- Evidence is generated from actual available features, never fabricated.