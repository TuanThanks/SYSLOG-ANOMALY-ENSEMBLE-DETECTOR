#!/usr/bin/env python3

import json
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parents[1]

OUTPUT_DIR = BASE_DIR / "outputs"
LOG_DIR = BASE_DIR / "logs"

CENTROID_FILE = OUTPUT_DIR / "centroid_scores.json"
KNN_FILE = OUTPUT_DIR / "knn_scores.json"
ENSEMBLE_OUTPUT_FILE = OUTPUT_DIR / "ensemble_results.json"

CENTROID_WEIGHT = 0.5
KNN_WEIGHT = 0.5
ENSEMBLE_THRESHOLD = 0.7


def write_log(message: str):
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / "pipeline.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [ENSEMBLE] {message}\n")

    print(message)


def load_json(file_path: Path):
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def confidence_label(score):
    if score >= 0.85:
        return "high"
    elif score >= 0.7:
        return "medium"
    else:
        return "low"


def main():
    write_log("Starting Ensemble Voting phase")

    centroid_data = load_json(CENTROID_FILE)
    knn_data = load_json(KNN_FILE)

    centroid_results = centroid_data["results"]
    knn_results = knn_data["results"]

    knn_by_line = {
        item["line"]: item
        for item in knn_results
    }

    ensemble_results = []

    for c_item in centroid_results:
        line = c_item["line"]

        if line not in knn_by_line:
            continue

        k_item = knn_by_line[line]

        centroid_score = float(c_item["centroid_score"])
        knn_score = float(k_item["knn_score"])

        ensemble_score = (
            CENTROID_WEIGHT * centroid_score
            +
            KNN_WEIGHT * knn_score
        )

        centroid_flag = bool(c_item["centroid_is_anomaly"])
        knn_flag = bool(k_item["knn_is_anomaly"])

        vote_count = int(centroid_flag) + int(knn_flag)

        high_confidence = centroid_flag and knn_flag

        final_is_anomaly = (
            high_confidence
            or ensemble_score >= ENSEMBLE_THRESHOLD
        )

        if high_confidence:
            decision_reason = "Both centroid and KNN detectors flagged this log."
        elif ensemble_score >= ENSEMBLE_THRESHOLD:
            decision_reason = "Combined ensemble score exceeded threshold."
        else:
            decision_reason = "Insufficient detector agreement and score below threshold."

        ensemble_results.append({
            "line": line,
            "text": c_item["text"],

            "centroid_raw_score": c_item["centroid_raw_score"],
            "centroid_score": centroid_score,
            "centroid_is_anomaly": centroid_flag,

            "knn_raw_score": k_item["knn_raw_score"],
            "knn_score": knn_score,
            "knn_is_anomaly": knn_flag,

            "vote_count": vote_count,
            "ensemble_score": ensemble_score,
            "ensemble_threshold": ENSEMBLE_THRESHOLD,
            "final_is_anomaly": final_is_anomaly,
            "confidence": confidence_label(ensemble_score),
            "decision_reason": decision_reason
        })

    final_anomalies = [
        item for item in ensemble_results
        if item["final_is_anomaly"]
    ]

    final_anomalies = sorted(
        final_anomalies,
        key=lambda x: x["ensemble_score"],
        reverse=True
    )

    output = {
        "detector": "ensemble",
        "description": "Combines centroid and KNN anomaly scores using weighted voting.",
        "configuration": {
            "centroid_weight": CENTROID_WEIGHT,
            "knn_weight": KNN_WEIGHT,
            "ensemble_threshold": ENSEMBLE_THRESHOLD,
            "decision_rules": [
                "Flag as anomaly if both centroid and KNN agree.",
                "Flag as anomaly if weighted ensemble score exceeds threshold."
            ]
        },
        "statistics": {
            "total_logs": len(ensemble_results),
            "centroid_anomalies": sum(1 for x in ensemble_results if x["centroid_is_anomaly"]),
            "knn_anomalies": sum(1 for x in ensemble_results if x["knn_is_anomaly"]),
            "final_anomalies": len(final_anomalies),
            "both_detectors_agree": sum(
                1 for x in ensemble_results
                if x["centroid_is_anomaly"] and x["knn_is_anomaly"]
            )
        },
        "results": ensemble_results,
        "final_anomalies": final_anomalies
    }

    with open(ENSEMBLE_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    write_log(f"Saved ensemble results to {ENSEMBLE_OUTPUT_FILE}")
    write_log(f"Final anomalies detected: {len(final_anomalies)}")
    write_log("Ensemble Voting phase completed successfully")


if __name__ == "__main__":
    main()
