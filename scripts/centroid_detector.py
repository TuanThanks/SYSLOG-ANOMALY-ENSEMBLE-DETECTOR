#!/usr/bin/env python3

import json
from pathlib import Path
from datetime import datetime

import numpy as np


BASE_DIR = Path(__file__).resolve().parents[1]

OUTPUT_DIR = BASE_DIR / "outputs"
LOG_DIR = BASE_DIR / "logs"

BASELINE_EMBEDDINGS_FILE = OUTPUT_DIR / "baseline_embeddings.json"
TEST_EMBEDDINGS_FILE = OUTPUT_DIR / "test_embeddings.json"

CENTROID_OUTPUT_FILE = OUTPUT_DIR / "centroid_scores.json"
CENTROID_MODEL_FILE = OUTPUT_DIR / "centroid_model.json"


def write_log(message: str):
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / "pipeline.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [CENTROID] {message}\n")

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


def cosine_distance(vector_a, vector_b):
    """
    Cosine distance = 1 - cosine similarity.

    Vì embedding đã normalize ở Phase 3,
    cosine distance có thể tính bằng 1 - dot product.
    Tuy nhiên vẫn viết an toàn phòng trường hợp vector chưa normalize.
    """

    norm_a = np.linalg.norm(vector_a)
    norm_b = np.linalg.norm(vector_b)

    if norm_a == 0 or norm_b == 0:
        return 1.0

    similarity = np.dot(vector_a, vector_b) / (norm_a * norm_b)

    distance = 1.0 - similarity

    return float(distance)


def normalize_scores(raw_scores):
    """
    Đưa score về khoảng 0 → 1 để sau này ensemble dễ hơn.
    """

    scores = np.array(raw_scores, dtype=np.float32)

    min_score = float(scores.min())
    max_score = float(scores.max())

    if max_score == min_score:
        return [0.0 for _ in raw_scores]

    normalized = (scores - min_score) / (max_score - min_score)

    return normalized.tolist()


def calculate_threshold(raw_scores):
    """
    Threshold đơn giản:
    mean + 2 * std

    Log nào có distance cao hơn threshold
    sẽ được xem là anomaly theo centroid detector.
    """

    scores = np.array(raw_scores, dtype=np.float32)

    mean = float(scores.mean())
    std = float(scores.std())

    threshold = mean + 1 * std

    return threshold, mean, std


def main():
    write_log("Starting Centroid Detector")

    baseline_records = load_embedding_records(BASELINE_EMBEDDINGS_FILE)
    test_records = load_embedding_records(TEST_EMBEDDINGS_FILE)

    write_log(f"Loaded {len(baseline_records)} baseline embeddings")
    write_log(f"Loaded {len(test_records)} test embeddings")

    baseline_matrix = records_to_matrix(baseline_records)

    centroid = baseline_matrix.mean(axis=0)

    write_log(f"Calculated centroid vector with dimension {len(centroid)}")

    raw_scores = []

    for record in test_records:
        test_vector = np.array(record["embedding"], dtype=np.float32)
        distance = cosine_distance(test_vector, centroid)
        raw_scores.append(distance)

    threshold, mean_score, std_score = calculate_threshold(raw_scores)
    normalized_scores = normalize_scores(raw_scores)

    results = []

    for record, raw_score, normalized_score in zip(
        test_records,
        raw_scores,
        normalized_scores
    ):
        is_anomaly = raw_score >= threshold

        results.append({
            "line": record["line"],
            "text": record["text"],
            "centroid_raw_score": raw_score,
            "centroid_score": normalized_score,
            "centroid_threshold": threshold,
            "centroid_is_anomaly": is_anomaly
        })

    output = {
        "detector": "centroid",
        "description": "Centroid-based anomaly detector using cosine distance to normal baseline centroid.",
        "statistics": {
            "baseline_count": len(baseline_records),
            "test_count": len(test_records),
            "embedding_dimension": int(len(centroid)),
            "mean_raw_score": mean_score,
            "std_raw_score": std_score,
            "threshold": threshold
        },
        "results": results
    }

    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(CENTROID_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    with open(CENTROID_MODEL_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "centroid": centroid.tolist(),
            "embedding_dimension": int(len(centroid)),
            "threshold": threshold
        }, f, indent=2)

    anomaly_count = sum(1 for item in results if item["centroid_is_anomaly"])

    write_log(f"Saved centroid scores to {CENTROID_OUTPUT_FILE}")
    write_log(f"Detected {anomaly_count} anomalies using centroid detector")
    write_log("Centroid Detector phase completed successfully")


if __name__ == "__main__":
    main()
