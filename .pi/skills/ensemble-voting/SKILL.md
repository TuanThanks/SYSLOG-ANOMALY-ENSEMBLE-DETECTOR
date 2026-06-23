---
name: ensemble-voting
description: Combine Centroid and KNN detector results using weighted ensemble voting.
---

# Ensemble Voting Skill

## Purpose

Combine independent detector outputs into a final anomaly decision.

## Input Files

- outputs/centroid_scores.json
- outputs/knn_scores.json

## Command

    python3 scripts/ensemble_detector.py

## Output File

- outputs/ensemble_results.json

## Method

The ensemble score is calculated as:

    ensemble_score = 0.5 * centroid_score + 0.5 * knn_score

## Decision Rules

A log is marked as final anomaly if:

1. Both Centroid and KNN flag it as anomaly.

OR

2. The weighted ensemble score is greater than or equal to the threshold.

Default threshold:

    ENSEMBLE_THRESHOLD = 0.7

## Benefit

This reduces false positives from a single detector and improves confidence before LLM explanation.
