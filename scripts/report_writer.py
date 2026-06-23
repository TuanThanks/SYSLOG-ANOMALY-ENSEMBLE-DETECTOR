#!/usr/bin/env python3

import json
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "outputs"
LOG_DIR = BASE_DIR / "logs"

ANOMALY_REPORT_FILE = OUTPUT_DIR / "anomaly_report.json"
ENSEMBLE_FILE = OUTPUT_DIR / "ensemble_results.json"
PARALLEL_TRACE_FILE = OUTPUT_DIR / "parallel_trace.json"
MARKDOWN_REPORT_FILE = OUTPUT_DIR / "ket_qua.md"


def write_log(message: str):
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / "pipeline.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [REPORT] {message}\n")

    print(message)


def load_json(path: Path):
    if not path.exists():
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_list(items):
    if not items:
        return "- Không có dữ liệu\n"

    return "".join([f"- {item}\n" for item in items])


def main():
    write_log("Starting Markdown report generation")

    anomaly_report = load_json(ANOMALY_REPORT_FILE)
    ensemble = load_json(ENSEMBLE_FILE)
    parallel = load_json(PARALLEL_TRACE_FILE)

    if anomaly_report is None:
        raise FileNotFoundError(f"Missing {ANOMALY_REPORT_FILE}")

    if ensemble is None:
        raise FileNotFoundError(f"Missing {ENSEMBLE_FILE}")

    stats = ensemble.get("statistics", {})
    config = ensemble.get("configuration", {})

    md = []

    md.append("# Syslog Anomaly Ensemble Detector — Kết quả chạy\n\n")

    md.append("## 1. Thông tin tổng quan\n\n")
    md.append(f"- Thời gian sinh báo cáo: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n")
    md.append(f"- Model giải thích: `{anomaly_report.get('model', 'N/A')}`\n")
    md.append(f"- Tổng số log test: `{stats.get('total_logs', 'N/A')}`\n")
    md.append(f"- Số anomaly do Centroid phát hiện: `{stats.get('centroid_anomalies', 'N/A')}`\n")
    md.append(f"- Số anomaly do KNN phát hiện: `{stats.get('knn_anomalies', 'N/A')}`\n")
    md.append(f"- Số anomaly cuối cùng sau Ensemble: `{stats.get('final_anomalies', 'N/A')}`\n")
    md.append(f"- Số anomaly được cả hai detector đồng ý: `{stats.get('both_detectors_agree', 'N/A')}`\n")
    md.append(f"- Số anomaly được LLM giải thích sau deduplication: `{anomaly_report.get('explained_anomalies', 'N/A')}`\n\n")

    md.append("## 2. Cấu hình Ensemble Voting\n\n")
    md.append(f"- Centroid weight: `{config.get('centroid_weight', 'N/A')}`\n")
    md.append(f"- KNN weight: `{config.get('knn_weight', 'N/A')}`\n")
    md.append(f"- Ensemble threshold: `{config.get('ensemble_threshold', 'N/A')}`\n\n")

    md.append("Quy tắc quyết định:\n\n")
    for rule in config.get("decision_rules", []):
        md.append(f"- {rule}\n")
    md.append("\n")

    if parallel:
        md.append("## 3. Kết quả Parallel Execution\n\n")
        md.append(f"- Chế độ chạy: `{parallel.get('mode', 'N/A')}`\n")
        md.append(f"- Tổng thời gian chạy song song: `{parallel.get('total_duration_seconds', 'N/A')}` giây\n\n")

        md.append("| Task | Status | Duration |\n")
        md.append("|---|---|---:|\n")

        for task in parallel.get("tasks", []):
            md.append(
                f"| {task.get('name')} | {task.get('status')} | {task.get('duration_seconds')}s |\n"
            )

        md.append("\n")

    md.append("## 4. Danh sách anomaly được giải thích\n\n")

    for report in anomaly_report.get("reports", []):
        analysis = report.get("llm_analysis", {})

        md.append(f"### #{report.get('rank')} — Line {report.get('line')}\n\n")
        md.append(f"**Log:**\n\n```text\n{report.get('text')}\n```\n\n")

        md.append(f"- Ensemble score: `{round(report.get('ensemble_score', 0), 4)}`\n")
        md.append(f"- Confidence: `{report.get('confidence')}`\n")
        md.append(f"- Vote count: `{report.get('vote_count')}`\n")
        md.append(f"- Centroid flag: `{report.get('centroid_is_anomaly')}`\n")
        md.append(f"- KNN flag: `{report.get('knn_is_anomaly')}`\n\n")

        md.append(f"**Threat category:** `{analysis.get('category', 'unknown')}`\n\n")
        md.append(f"**Severity:** `{analysis.get('severity', 'unknown')}`\n\n")

        md.append("**Explanation:**\n\n")
        md.append(f"{analysis.get('explanation', 'No explanation provided.')}\n\n")

        md.append("**Evidence:**\n\n")
        md.append(format_list(analysis.get("evidence", [])))
        md.append("\n")

        md.append("**Recommended actions:**\n\n")
        md.append(format_list(analysis.get("recommended_actions", [])))
        md.append("\n---\n\n")

    md.append("## 5. Kết luận\n\n")
    md.append(
        "Pipeline đã phát hiện anomaly bằng hai detector độc lập gồm Centroid-based Detector "
        "và KNN-based Detector. Hai detector được chạy song song để giảm thời gian scoring, "
        "sau đó kết quả được kết hợp bằng Ensemble Voting. Cuối cùng, hệ thống chỉ gửi các "
        "anomaly có độ tin cậy cao và đã được deduplicate sang LLM để sinh giải thích bảo mật.\n"
    )

    with open(MARKDOWN_REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("".join(md))

    write_log(f"Saved Markdown report to {MARKDOWN_REPORT_FILE}")
    write_log("Markdown report generation completed successfully")


if __name__ == "__main__":
    main()
