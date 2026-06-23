#!/usr/bin/env python3

import json
import os
import re
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(".env")

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "outputs"
LOG_DIR = BASE_DIR / "logs"

ENSEMBLE_FILE = OUTPUT_DIR / "ensemble_results.json"
REPORT_FILE = OUTPUT_DIR / "anomaly_report.json"

TOP_N = 10


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

EXPLANATION_MODEL = os.getenv("EXPLANATION_MODEL", "deepseek-chat")


def write_log(message: str):
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / "pipeline.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [EXPLAIN] {message}\n")

    print(message)


def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def make_signature(text: str) -> str:
    """
    Tạo signature để gom các log cùng loại.
    Ví dụ:
    - nhiều dòng Segfault khác timestamp vẫn gom lại 1 nhóm
    - nhiều dòng Shellshock vẫn gom lại 1 nhóm
    """

    text = text.lower()

    # Xóa timestamp đầu dòng kiểu Jun  9 00:55:03
    text = re.sub(r"^[a-z]{3}\s+\d+\s+\d+:\d+:\d+\s+", "", text)

    # Xóa số PID, port, IP, timestamp trong nginx
    text = re.sub(r"\[\d+\]", "[pid]", text)
    text = re.sub(r"\b\d{1,3}(\.\d{1,3}){3}\b", "[ip]", text)
    text = re.sub(r"\b\d{2}:\d{2}:\d{2}\b", "[time]", text)
    text = re.sub(r"\b\d+\b", "[num]", text)

    # Gom khoảng trắng
    text = re.sub(r"\s+", " ", text).strip()

    return text[:180]


def select_top_unique_anomalies(final_anomalies):
    """
    Chọn anomaly có score cao nhất nhưng không lặp cùng loại quá nhiều.
    """

    sorted_items = sorted(
        final_anomalies,
        key=lambda x: x["ensemble_score"],
        reverse=True
    )

    selected = []
    seen_signatures = set()

    for item in sorted_items:
        sig = make_signature(item["text"])

        if sig in seen_signatures:
            continue

        selected.append(item)
        seen_signatures.add(sig)

        if len(selected) >= TOP_N:
            break

    return selected


def build_prompt(item):
    return f"""
Analyze the following syslog anomaly as a senior SOC analyst.

Return JSON only with these fields:
- category: short attack or incident category
- severity: low, medium, high, or critical
- explanation: explain why this log is suspicious in 2-4 sentences
- evidence: list of concrete indicators from the log
- recommended_actions: list of immediate actions for a SOC analyst

Syslog anomaly:
{item["text"]}

Detection context:
- line: {item["line"]}
- ensemble_score: {item["ensemble_score"]}
- confidence: {item["confidence"]}
- vote_count: {item["vote_count"]}
- centroid_is_anomaly: {item["centroid_is_anomaly"]}
- knn_is_anomaly: {item["knn_is_anomaly"]}
"""


def safe_parse_json(text):
    """
    DeepSeek thường trả JSON, nhưng đôi khi bọc ```json.
    Hàm này làm sạch rồi parse.
    """

    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```json", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"^```", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "category": "unknown",
            "severity": "medium",
            "explanation": cleaned,
            "evidence": [],
            "recommended_actions": []
        }


def explain_with_deepseek(item):
    prompt = build_prompt(item)

    response = client.chat.completions.create(
        model=EXPLANATION_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior cybersecurity SOC analyst. "
                    "You analyze syslog anomalies and return valid JSON only. "
                    "Do not include markdown. Do not include extra commentary."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    content = response.choices[0].message.content
    return safe_parse_json(content)


def main():
    write_log("Starting LLM explanation phase")

    ensemble_data = load_json(ENSEMBLE_FILE)
    final_anomalies = ensemble_data["final_anomalies"]

    write_log(f"Loaded {len(final_anomalies)} final anomalies from ensemble")

    selected = select_top_unique_anomalies(final_anomalies)

    write_log(f"Selected {len(selected)} unique high-confidence anomalies for explanation")

    reports = []

    for index, item in enumerate(selected, start=1):
        write_log(f"Explaining anomaly {index}/{len(selected)} at line {item['line']}")

        llm_analysis = explain_with_deepseek(item)

        reports.append({
            "rank": index,
            "line": item["line"],
            "text": item["text"],
            "ensemble_score": item["ensemble_score"],
            "confidence": item["confidence"],
            "vote_count": item["vote_count"],
            "centroid_is_anomaly": item["centroid_is_anomaly"],
            "knn_is_anomaly": item["knn_is_anomaly"],
            "llm_analysis": llm_analysis
        })

    output = {
        "report_type": "syslog_anomaly_explanation",
        "model": EXPLANATION_MODEL,
        "total_final_anomalies": len(final_anomalies),
        "explained_anomalies": len(reports),
        "selection_strategy": "Top unique anomalies by ensemble_score with signature-based deduplication.",
        "reports": reports
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    write_log(f"Saved anomaly report to {REPORT_FILE}")
    write_log("LLM explanation phase completed successfully")


if __name__ == "__main__":
    main()
