---
name: syslog-embedding
description: Generate local embeddings for baseline and test syslog files using SentenceTransformer.
---

# Syslog Embedding Skill

## Purpose

Convert syslog text lines into numerical embedding vectors.

## Input Files

- data/baseline_normal.txt
- data/test_logs.txt

## Command

    python3 scripts/embed_logs.py

## Output Files

- outputs/baseline_embeddings.json
- outputs/test_embeddings.json

## Method

This skill uses a local SentenceTransformer model.

Default model:

    all-MiniLM-L6-v2

Each syslog line is converted into a 384-dimensional vector.

These embeddings are used by the Centroid Detector and KNN Detector.
