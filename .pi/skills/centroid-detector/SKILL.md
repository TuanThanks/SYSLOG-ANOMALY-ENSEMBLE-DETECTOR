---
name: centroid-detector
description: Detect anomalies by measuring cosine distance from the normal baseline centroid.
---

# Centroid Detector Skill

## Purpose

Detect syslog lines that are far from the average normal behavior.

## Input Files

- outputs/baseline_embeddings.json
- outputs/test_embeddings.json

## Command

    python3 scripts/centroid_detector.py

## Output Files

- outputs/centroid_scores.json
- outputs/centroid_model.json

## Method

1. Load baseline embeddings.
2. Calculate the centroid vector from normal logs.
3. Measure cosine distance from each test log to the centroid.
4. Normalize scores.
5. Flag anomalies using threshold.

## Threshold

    threshold = mean + std

Where:

- mean is the average raw distance score.
- std is the standard deviation of raw distance scores.
