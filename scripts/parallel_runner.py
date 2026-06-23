#!/usr/bin/env python3

import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "outputs"
LOG_DIR = BASE_DIR / "logs"

CENTROID_SCRIPT = BASE_DIR / "scripts" / "centroid_detector.py"
KNN_SCRIPT = BASE_DIR / "scripts" / "knn_detector.py"

TRACE_FILE = OUTPUT_DIR / "parallel_trace.json"


def write_log(message: str):
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / "pipeline.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [PARALLEL] {message}\n")

    print(message)


def run_script(name, script_path):

    write_log(f"Starting {name}")

    start = time.time()

    result = subprocess.run(
        ["python3", script_path],
        capture_output=True,
        text=True
    )

    end = time.time()

    duration = end - start

    write_log(
        f"{name} completed in {duration:.4f} seconds"
    )

    return {
        "name": name,
        "script": str(script_path),
        "status": "success" if result.returncode == 0 else "failed",
        "return_code": result.returncode,
        "duration_seconds": round(duration, 4),
        "stdout": result.stdout,
        "stderr": result.stderr
    }


def run_parallel():
    start_total = time.time()

    with ThreadPoolExecutor(max_workers=2) as executor:
        centroid_future = executor.submit(
            run_script,
            "centroid_detector",
            CENTROID_SCRIPT
        )

        knn_future = executor.submit(
            run_script,
            "knn_detector",
            KNN_SCRIPT
        )

        centroid_result = centroid_future.result()
        knn_result = knn_future.result()

    end_total = time.time()

    trace = {
        "mode": "parallel",
        "description": "Centroid and KNN detectors run independently in parallel.",
        "started_at": datetime.now().isoformat(),
        "total_duration_seconds": round(end_total - start_total, 4),
        "tasks": [
            centroid_result,
            knn_result
        ]
    }

    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(TRACE_FILE, "w", encoding="utf-8") as f:
        json.dump(trace, f, indent=2, ensure_ascii=False)

    write_log(f"Saved parallel trace to {TRACE_FILE}")

    if centroid_result["status"] == "success" and knn_result["status"] == "success":
        write_log("Parallel execution completed successfully")
    else:
        write_log("Parallel execution completed with errors")

    return trace


def main():
    write_log("Starting Parallel Execution phase")

    parallel_start = time.time()
    run_parallel()
    parallel_end = time.time()

    print(
        f"\nTotal parallel execution time: "
        f"{parallel_end - parallel_start:.4f} seconds"
    )


if __name__ == "__main__":
    main()
