#!/usr/bin/env python3

import json
from pathlib import Path
from datetime import datetime

import numpy as np
from sklearn.neighbors import NearestNeighbors


BASE_DIR = Path(__file__).resolve().parents[1]

OUTPUT_DIR = BASE_DIR / "outputs"
LOG_DIR = BASE_DIR / "logs"

BASELINE_EMBEDDINGS_FILE = OUTPUT_DIR / "baseline_embeddings.json"
TEST_EMBEDDINGS_FILE = OUTPUT_DIR / "test_embeddings.json"

KNN_OUTPUT_FILE = OUTPUT_DIR / "knn_scores.json"
KNN_MODEL_INFO_FILE = OUTPUT_DIR / "knn_model_info.json"

K_NEIGHBORS = 5


def write_log(message: str):
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / "pipeline.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [KNN] {message}\n")

    print(message)


def load_embedding_records(file_path: Path):
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def records_to_matrix(records):
    return np.array(
        [record["embedding"] for record in records],
        dtype=np.float32
    )


def normalize_scores(raw_scores):
    scores = np.array(raw_scores, dtype=np.float32)

    min_score = float(scores.min())
    max_score = float(scores.max())

    if max_score == min_score:
        return [0.0 for _ in raw_scores]

    normalized = (scores - min_score) / (max_score - min_score)

    return normalized.tolist()


def calculate_threshold(raw_scores):
    """
    Threshold = mean + std

    KNN score càng cao nghĩa là log càng xa các normal neighbors.
    """

    scores = np.array(raw_scores, dtype=np.float32)

    mean = float(scores.mean())
    std = float(scores.std())

    threshold = mean + std

    return threshold, mean, std


def main():
    write_log("Starting KNN Detector")

    baseline_records = load_embedding_records(BASELINE_EMBEDDINGS_FILE)
    test_records = load_embedding_records(TEST_EMBEDDINGS_FILE)

    write_log(f"Loaded {len(baseline_records)} baseline embeddings")
    write_log(f"Loaded {len(test_records)} test embeddings")

    baseline_matrix = records_to_matrix(baseline_records)
    test_matrix = records_to_matrix(test_records)

    write_log(f"Fitting KNN with k={K_NEIGHBORS}")

    knn = NearestNeighbors(
        n_neighbors=K_NEIGHBORS,
        metric="cosine"
    )

    knn.fit(baseline_matrix)

    distances, indices = knn.kneighbors(test_matrix)

    raw_scores = distances.mean(axis=1).tolist()

    threshold, mean_score, std_score = calculate_threshold(raw_scores)
    normalized_scores = normalize_scores(raw_scores)

    results = []

    for record, raw_score, normalized_score, neighbor_distances, neighbor_indices in zip(
        test_records,
        raw_scores,
        normalized_scores,
        distances,
        indices
    ):
        is_anomaly = raw_score >= threshold

        nearest_neighbors = []

        for dist, idx in zip(neighbor_distances, neighbor_indices):
            baseline_record = baseline_records[int(idx)]

            nearest_neighbors.append({
                "baseline_line": baseline_record["line"],
                "baseline_text": baseline_record["text"],
                "distance": float(dist)
            })

        results.append({
            "line": record["line"],
            "text": record["text"],
            "knn_raw_score": float(raw_score),
            "knn_score": float(normalized_score),
            "knn_threshold": float(threshold),
            "knn_is_anomaly": bool(is_anomaly),
            "nearest_neighbors": nearest_neighbors
        })

    output = {
        "detector": "knn",
        "description": "KNN-based anomaly detector using average cosine distance to nearest normal baseline logs.",
        "statistics": {
            "baseline_count": len(baseline_records),
            "test_count": len(test_records),
            "embedding_dimension": int(baseline_matrix.shape[1]),
            "k_neighbors": K_NEIGHBORS,
            "mean_raw_score": mean_score,
            "std_raw_score": std_score,
            "threshold": threshold
        },
        "results": results
    }

    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(KNN_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    with open(KNN_MODEL_INFO_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "model_type": "NearestNeighbors",
            "metric": "cosine",
            "k_neighbors": K_NEIGHBORS,
            "embedding_dimension": int(baseline_matrix.shape[1]),
            "threshold": threshold
        }, f, indent=2)

    anomaly_count = sum(1 for item in results if item["knn_is_anomaly"])

    write_log(f"Saved KNN scores to {KNN_OUTPUT_FILE}")
    write_log(f"Detected {anomaly_count} anomalies using KNN detector")
    write_log("KNN Detector phase completed successfully")


if __name__ == "__main__":
    main()
