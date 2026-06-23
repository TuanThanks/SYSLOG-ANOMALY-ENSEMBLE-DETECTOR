---
name: report-writer
description: Generate Markdown result report from anomaly JSON outputs.
---

# Report Writer Skill

## Purpose

Convert technical JSON outputs into a readable Markdown report.

## Input Files

- outputs/anomaly_report.json
- outputs/ensemble_results.json
- outputs/parallel_trace.json

## Command

    python3 scripts/report_writer.py

## Output File

- outputs/ket_qua.md

## Report Sections

1. Overview
2. Ensemble configuration
3. Parallel execution result
4. Explained anomalies
5. Conclusion
