"""
export_csv.py
Converts a generated test-case JSON file into CSV -- the format most
test-management tools (TestRail, Xray, Zephyr) expect for import. JSON
stays the canonical output; this is a downstream export, not a
replacement.

Which JSON file gets converted is resolved in this priority order:
  1. --file command-line argument (one-off override, no config edit needed)
  2. export.target_json_file in config.yaml (a standing choice)
  3. the most recently generated file in outputs/json/ (default fallback)
Nothing is ever hardcoded in this file itself.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from config import load_config


def find_latest_json(json_dir: Path) -> Path:
    files = sorted(json_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"No JSON files found in {json_dir}")
    return files[-1]


def resolve_json_path(json_dir: Path, cli_file: str | None, config_file: str) -> Path:
    """
    Priority: CLI arg > config.yaml setting > latest file in json_dir.
    Both CLI and config values may be a bare filename (resolved inside
    json_dir) or a full path.
    """
    chosen = cli_file or config_file or None

    if chosen:
        candidate = Path(chosen)
        if not candidate.is_absolute():
            candidate = json_dir / candidate
        if not candidate.exists():
            raise FileNotFoundError(f"Specified JSON file not found: {candidate}")
        return candidate

    return find_latest_json(json_dir)


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
    parser = argparse.ArgumentParser(description="Convert a generated test-case JSON file to CSV.")
    parser.add_argument(
        "--file",
        default=None,
        help="Specific JSON filename (in outputs/json/) or full path to convert. Overrides config.yaml.",
    )
    args = parser.parse_args()

    cfg = load_config()
    json_dir = cfg.generation.output_dir / cfg.generation.json_subdir
    csv_dir = cfg.generation.output_dir / cfg.generation.csv_subdir

    source_json = resolve_json_path(json_dir, args.file, cfg.export.target_json_file)
    csv_path = csv_dir / source_json.with_suffix(".csv").name

    count = json_to_csv(source_json, csv_path)
    print(f"Converted {source_json.name} -> {csv_path} ({count} rows)")