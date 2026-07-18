"""
export_csv.py
Converts a generated test-case JSON file into CSV -- the format most
test-management tools (TestRail, Xray, Zephyr) expect for import. JSON
stays the canonical output; this is a downstream export, not a
replacement.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from config import load_config


def find_latest_json(json_dir: Path) -> Path:
    """No hardcoded filename -- picks whichever JSON file in json_dir was
    written most recently."""
    files = sorted(json_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"No JSON files found in {json_dir}")
    return files[-1]


def json_to_csv(json_path: Path, csv_path: Path) -> int:
    data = json.loads(json_path.read_text())

    rows = []
    for feature in data["features"]:
        for tc in feature["test_cases"]:
            rows.append({
                "feature_name": feature["feature_name"],
                "title": tc["title"],
                "category": tc["category"],
                "preconditions": "; ".join(tc["preconditions"]),
                "steps": "; ".join(tc["steps"]),
                "expected_result": tc["expected_result"],
                "source_section": tc["source_section"],
            })

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


if __name__ == "__main__":
    cfg = load_config()
    json_dir = cfg.generation.output_dir / cfg.generation.json_subdir
    csv_dir = cfg.generation.output_dir / cfg.generation.csv_subdir

    latest_json = find_latest_json(json_dir)
    csv_path = csv_dir / latest_json.with_suffix(".csv").name

    count = json_to_csv(latest_json, csv_path)
    print(f"Converted {latest_json.name} -> {csv_path} ({count} rows)")