#!/usr/bin/env python3

import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

GROUND_TRUTH_FILE = BASE_DIR / "data" / "ground_truth.json"

ENSEMBLE_FILE = BASE_DIR / "outputs" / "ensemble_results.json"

OUTPUT_FILE = BASE_DIR / "outputs" / "evaluation_metrics.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():

    ground_truth_list = load_json(GROUND_TRUTH_FILE)

    ground_truth = {
    	str(item["line"]): item
    	for item in ground_truth_list
    	if item.get("label") == "anomaly"
    }

    ensemble = load_json(ENSEMBLE_FILE)

    results = ensemble["results"]

    TP = TN = FP = FN = 0

    for item in results:

        line = str(item["line"])

        predicted = item["final_is_anomaly"]

        actual = line in ground_truth

        if actual and predicted:
            TP += 1

        elif (not actual) and predicted:
            FP += 1

        elif actual and (not predicted):
            FN += 1

        else:
            TN += 1

    precision = (
        TP / (TP + FP)
        if (TP + FP) > 0 else 0
    )

    recall = (
        TP / (TP + FN)
        if (TP + FN) > 0 else 0
    )

    f1 = (
        2 * precision * recall /
        (precision + recall)
        if (precision + recall) > 0 else 0
    )

    accuracy = (
        (TP + TN) /
        (TP + TN + FP + FN)
    )

    metrics = {

        "TP": TP,
        "FP": FP,
        "FN": FN,
        "TN": TN,

        "precision": round(
            precision,
            4
        ),

        "recall": round(
            recall,
            4
        ),

        "f1_score": round(
            f1,
            4
        ),

        "accuracy": round(
            accuracy,
            4
        )
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            metrics,
            f,
            indent=2
        )

    print("\nEvaluation Results\n")

    for k, v in metrics.items():

        print(
            f"{k}: {v}"
        )


if __name__ == "__main__":

    main()
