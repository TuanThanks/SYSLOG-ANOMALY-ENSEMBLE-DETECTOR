---
name: syslog-anomaly-chain
description: End-to-end execution chain for the Syslog Anomaly Ensemble Detector.
---

# Syslog Anomaly Chain

This chain describes the full project workflow.

## Phase 1 — Dataset

Input files:

- data/baseline_normal.txt
- data/test_logs.txt
- data/ground_truth.json

Purpose:

- baseline_normal.txt is used to learn normal behavior.
- test_logs.txt is used for anomaly detection.
- ground_truth.json is used later for evaluation.

## Phase 2 — Embedding

Command:

    python3 scripts/embed_logs.py

Expected outputs:

- outputs/baseline_embeddings.json
- outputs/test_embeddings.json

## Phase 3 — Parallel Detector Execution

Command:

    python3 scripts/parallel_runner.py

This runs these detectors independently in parallel:

- Centroid Detector
- KNN Detector

Expected outputs:

- outputs/centroid_scores.json
- outputs/knn_scores.json
- outputs/parallel_trace.json

## Phase 4 — Ensemble Voting

Command:

    python3 scripts/ensemble_detector.py

Expected output:

- outputs/ensemble_results.json

## Phase 5 — LLM Explanation

Command:

    python3 scripts/explain_anomalies.py

Expected output:

- outputs/anomaly_report.json

## Phase 6 — Markdown Report

Command:

    python3 scripts/report_writer.py

Expected output:

- outputs/ket_qua.md

## Full Pipeline Command

Command:

    python3 scripts/run_pipeline.py

This command runs all major pipeline phases automatically.
