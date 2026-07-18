"""
evaluate_faithfulness.py
Hand-built LLM-as-judge faithfulness metric -- the same definition RAGAS
uses: break the generated answer into atomic claims, check each claim
against the retrieved context, faithfulness = supported_claims / total.

Built directly on our existing Anthropic client (same one generate.py
uses) rather than the ragas library, after ragas's import chain proved
broken in this environment (dependency conflict in langchain_community's
deprecated Vertex AI integration -- reproducible, not user error). Same
core LLM-as-judge methodology, no fragile dependency chain.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from anthropic import Anthropic
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from judge_schemas import FaithfulnessJudgement

load_dotenv()

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "faithfulness_judge_v1.txt"


def build_judge_prompt(expected_result: str, context: str) -> str:
    template = PROMPT_PATH.read_text()
    prompt = template.replace("{{expected_result}}", expected_result)
    prompt = prompt.replace("{{context}}", context)
    return prompt


def parse_judge_response(raw_text: str) -> FaithfulnessJudgement:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return FaithfulnessJudgement(**json.loads(text))


def judge_faithfulness(expected_result: str, context: str, model_name: str = "claude-sonnet-5") -> FaithfulnessJudgement:
    client = Anthropic()
    prompt = build_judge_prompt(expected_result, context)

    response = client.messages.create(
        model=model_name,
        max_tokens=1024,
        thinking={"type": "disabled"},
        messages=[{"role": "user", "content": prompt}],
    )

    text_blocks = [block.text for block in response.content if block.type == "text"]
    raw_text = "".join(text_blocks)
    return parse_judge_response(raw_text)


if __name__ == "__main__":
    from config import load_config
    from embed import load_embedding_model, embed_texts
    from index import query_index
    from export_csv import resolve_json_path

    cfg = load_config()
    json_dir = cfg.generation.output_dir / cfg.generation.json_subdir
    source_json = resolve_json_path(json_dir, None, cfg.export.target_json_file)
    print(f"Evaluating faithfulness of: {source_json.name}\n")

    data = json.loads(source_json.read_text())
    embed_model = load_embedding_model(cfg.embedding.model_name)

    feature_reports = []
    all_scores = []

    for feature in data["features"]:
        query_embedding = embed_texts([feature["feature_query"]], embed_model)[0]
        retrieved = query_index(
            str(cfg.paths.chroma_dir), cfg.index.collection_name,
            query_embedding.tolist(), n_results=cfg.generation.n_results,
        )
        context = "\n\n".join(retrieved["documents"][0])

        print(f"--- {feature['feature_name']} ---")
        test_case_reports = []
        for tc in feature["test_cases"]:
            judgement = judge_faithfulness(tc["expected_result"], context)
            all_scores.append(judgement.score)
            print(f"  [{judgement.score:.2f}] {tc['title']}")

            test_case_reports.append({
                "title": tc["title"],
                "expected_result": tc["expected_result"],
                "score": judgement.score,
                "claims": [c.model_dump() for c in judgement.claims],
            })
        print()

        feature_reports.append({
            "feature_name": feature["feature_name"],
            "test_cases": test_case_reports,
        })

    overall = sum(all_scores) / len(all_scores) if all_scores else 0.0
    print(f"--- Overall mean faithfulness: {overall:.3f} across {len(all_scores)} test cases ---")

    output = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "source_json": source_json.name,
        "overall_mean_faithfulness": overall,
        "total_test_cases": len(all_scores),
        "features": feature_reports,
    }

    ist_now = datetime.now(ZoneInfo("Asia/Kolkata"))
    out_dir = cfg.generation.output_dir / cfg.evaluation.faithfulness_output_subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"faithfulness_{ist_now.strftime(cfg.generation.filename_timestamp_format)}.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\nWrote results to {out_path}")