---
name: llm-explanation
description: Explain highest-confidence syslog anomalies using DeepSeek.
---

# LLM Explanation Skill

## Purpose

Generate SOC-style explanations for high-confidence anomalies.

## Input File

- outputs/ensemble_results.json

## Command

    python3 scripts/explain_anomalies.py

## Output File

- outputs/anomaly_report.json

## Method

1. Load final anomalies from ensemble results.
2. Sort anomalies by ensemble score.
3. Deduplicate similar anomaly types using signature-based grouping.
4. Select representative high-confidence anomalies.
5. Send selected anomalies to DeepSeek for explanation.
6. Save structured JSON report.

## LLM Output Fields

- category
- severity
- explanation
- evidence
- recommended_actions

## Cost Control

Only unique high-confidence anomalies are explained.
Repeated logs of the same type are skipped.
