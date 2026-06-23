---
name: knn-detector
description: Detect anomalies using average cosine distance to nearest normal baseline logs.
---

# KNN Detector Skill

## Purpose

Detect syslog lines that are far from their nearest normal neighbors.

## Input Files

- outputs/baseline_embeddings.json
- outputs/test_embeddings.json

## Command

    python3 scripts/knn_detector.py

## Output Files

- outputs/knn_scores.json
- outputs/knn_model_info.json

## Method

1. Load baseline and test embeddings.
2. Fit NearestNeighbors on baseline normal embeddings.
3. For each test log, find the 5 nearest normal logs.
4. Calculate average cosine distance.
5. Normalize scores.
6. Flag anomalies using threshold.

## Configuration

    K_NEIGHBORS = 5
    metric = cosine
    threshold = mean + std
