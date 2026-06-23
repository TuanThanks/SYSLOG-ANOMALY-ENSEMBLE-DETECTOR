#!/usr/bin/env python3

import json
import subprocess
import time
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "outputs"

PIPELINE_TRACE_FILE = OUTPUT_DIR / "pipeline_trace.json"

STEPS = [
    {
        "name": "Embedding Engine",
        "script": "scripts/embed_logs.py",
        "expected_outputs": [
            "outputs/baseline_embeddings.json",
            "outputs/test_embeddings.json"
        ]
    },
    {
        "name": "Parallel Detector Execution",
        "script": "scripts/parallel_runner.py",
        "expected_outputs": [
            "outputs/centroid_scores.json",
            "outputs/knn_scores.json",
            "outputs/parallel_trace.json"
        ]
    },
    {
        "name": "Ensemble Voting",
        "script": "scripts/ensemble_detector.py",
        "expected_outputs": [
            "outputs/ensemble_results.json"
        ]
    },
    {
        "name": "LLM Explanation",
        "script": "scripts/explain_anomalies.py",
        "expected_outputs": [
            "outputs/anomaly_report.json"
        ]
    },
    {
        "name": "Markdown Report",
        "script": "scripts/report_writer.py",
        "expected_outputs": [
            "outputs/ket_qua.md"
        ]
    },
    {
        "name": "Evaluation",
        "script": "scripts/evaluate.py",
        "expected_outputs": [
            "outputs/evaluation_metrics.json"
        ]
    }
]


def write_log(message: str):
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / "pipeline.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [RUN_PIPELINE] {message}\n")

    print(message)


def check_file_exists(relative_path: str) -> bool:
    return (BASE_DIR / relative_path).exists()


def run_step(step: dict) -> dict:
    start = time.time()

    write_log(f"Starting step: {step['name']}")

    script_path = BASE_DIR / step["script"]

    if not script_path.exists():
        duration = round(time.time() - start, 4)

        return {
            "name": step["name"],
            "script": step["script"],
            "status": "failed",
            "return_code": -1,
            "duration_seconds": duration,
            "stdout": "",
            "stderr": f"Script not found: {script_path}",
            "expected_outputs": step.get("expected_outputs", []),
            "missing_outputs": step.get("expected_outputs", [])
        }

    result = subprocess.run(
        ["python3", str(script_path)],
        cwd=BASE_DIR,
        capture_output=True,
        text=True
    )

    duration = round(time.time() - start, 4)

    expected_outputs = step.get("expected_outputs", [])

    missing_outputs = [
        output
        for output in expected_outputs
        if not check_file_exists(output)
    ]

    status = "success"

    if result.returncode != 0:
        status = "failed"
    elif missing_outputs:
        status = "failed"

    write_log(
        f"Finished step: {step['name']} | "
        f"status={status} | duration={duration}s"
    )

    if missing_outputs:
        write_log(
            f"Missing outputs for {step['name']}: {missing_outputs}"
        )

    return {
        "name": step["name"],
        "script": step["script"],
        "status": status,
        "return_code": result.returncode,
        "duration_seconds": duration,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "expected_outputs": expected_outputs,
        "missing_outputs": missing_outputs
    }


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)

    write_log("=" * 70)
    write_log("Starting full Syslog Anomaly Ensemble Detector pipeline")

    pipeline_start = time.time()
    started_at = datetime.now().isoformat()

    step_results = []

    for step in STEPS:
        result = run_step(step)
        step_results.append(result)

        if result["status"] != "success":
            write_log(f"Pipeline stopped because step failed: {step['name']}")
            break

    total_duration = round(time.time() - pipeline_start, 4)

    success = all(
        result["status"] == "success"
        for result in step_results
    ) and len(step_results) == len(STEPS)

    trace = {
        "pipeline": "Syslog Anomaly Ensemble Detector",
        "status": "success" if success else "failed",
        "started_at": started_at,
        "finished_at": datetime.now().isoformat(),
        "total_duration_seconds": total_duration,
        "steps_total": len(STEPS),
        "steps_completed": len(step_results),
        "steps": step_results
    }

    with open(PIPELINE_TRACE_FILE, "w", encoding="utf-8") as f:
        json.dump(trace, f, indent=2, ensure_ascii=False)

    if success:
        write_log("Full pipeline completed successfully")
    else:
        write_log("Full pipeline completed with errors")

    write_log(f"Saved pipeline trace to {PIPELINE_TRACE_FILE}")
    write_log("=" * 70)

    print()
    print("Pipeline Summary")
    print("-" * 70)
    print(f"Status: {trace['status']}")
    print(f"Total duration: {total_duration}s")
    print(f"Trace file: {PIPELINE_TRACE_FILE}")
    print()

    for result in step_results:
        print(
            f"[{result['status'].upper()}] "
            f"{result['name']} "
            f"({result['duration_seconds']}s)"
        )

    print()

    if success:
        print("Important output files:")
        print("- outputs/ensemble_results.json")
        print("- outputs/anomaly_report.json")
        print("- outputs/ket_qua.md")
        print("- outputs/evaluation_metrics.json")
        print("- outputs/pipeline_trace.json")


if __name__ == "__main__":
    main()
