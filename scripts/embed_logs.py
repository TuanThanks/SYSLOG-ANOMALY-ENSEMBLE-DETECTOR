#!/usr/bin/env python3

import json
import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
LOG_DIR = BASE_DIR / "logs"

BASELINE_FILE = DATA_DIR / "baseline_normal.txt"
TEST_FILE = DATA_DIR / "test_logs.txt"

BASELINE_OUTPUT = OUTPUT_DIR / "baseline_embeddings.json"
TEST_OUTPUT = OUTPUT_DIR / "test_embeddings.json"

LOCAL_MODEL_NAME = os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")


def write_log(message: str):
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / "pipeline.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [EMBEDDING] {message}\n")

    print(message)


def load_logs(file_path: Path):
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    logs = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            text = line.strip()

            if text:
                logs.append({
                    "line": line_no,
                    "text": text
                })

    return logs


def embed_logs(log_items, model):
    texts = [item["text"] for item in log_items]

    write_log(f"Embedding {len(texts)} log lines using model: {LOCAL_MODEL_NAME}")

    vectors = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    results = []

    for item, vector in zip(log_items, vectors):
        results.append({
            "line": item["line"],
            "text": item["text"],
            "embedding": vector.tolist()
        })

    return results


def save_json(data, output_path: Path):
    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    write_log(f"Saved embeddings to {output_path}")


def main():
    write_log("Starting local embedding engine")

    model = SentenceTransformer(LOCAL_MODEL_NAME)

    baseline_logs = load_logs(BASELINE_FILE)
    test_logs = load_logs(TEST_FILE)

    write_log(f"Loaded {len(baseline_logs)} baseline logs")
    write_log(f"Loaded {len(test_logs)} test logs")

    baseline_embeddings = embed_logs(baseline_logs, model)
    test_embeddings = embed_logs(test_logs, model)

    save_json(baseline_embeddings, BASELINE_OUTPUT)
    save_json(test_embeddings, TEST_OUTPUT)

    write_log("Embedding phase completed successfully")


if __name__ == "__main__":
    main()
