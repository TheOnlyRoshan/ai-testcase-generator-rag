"""
evaluate_retrieval.py
Hand-implemented retrieval metrics (context precision, context recall,
mean reciprocal rank) run against the hand-labeled golden set.

These are simple set-overlap and ranking calculations -- no LLM judge
needed, no extra API cost -- which is exactly why they're worth building
by hand rather than reaching straight for the ragas library: they're
cheap to run on every change, and understanding them directly explains
what "retrieval quality" concretely means before layering the harder,
LLM-judged metrics (faithfulness) on top separately.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


@dataclass
class GoldenExample:
    id: str
    question: str
    expected_sections: list[str]


@dataclass
class RetrievalResult:
    example_id: str
    question: str
    expected_sections: list[str]
    retrieved_sections: list[str]
    precision: float
    recall: float
    reciprocal_rank: float  # 1/rank of first correct hit, 0 if none found


def load_golden_set(path: Path) -> list[GoldenExample]:
    raw = yaml.safe_load(path.read_text())
    return [GoldenExample(**item) for item in raw]


def compute_metrics(expected: list[str], retrieved: list[str]) -> tuple[float, float, float]:
    """
    precision = of what we retrieved, how much was actually relevant
    recall    = of what's actually relevant, how much did we retrieve
    reciprocal_rank = 1 / (position of the first correct hit), 0 if missed
                       -- rewards ranking a correct result near the top,
                       not just including it somewhere in the top-k
    """
    expected_set = set(expected)
    retrieved_set = set(retrieved)

    hits = expected_set & retrieved_set
    precision = len(hits) / len(retrieved_set) if retrieved_set else 0.0
    recall = len(hits) / len(expected_set) if expected_set else 0.0

    reciprocal_rank = 0.0
    for rank, section in enumerate(retrieved, start=1):
        if section in expected_set:
            reciprocal_rank = 1.0 / rank
            break

    return precision, recall, reciprocal_rank


def evaluate(golden_set: list[GoldenExample], retrieve_fn) -> list[RetrievalResult]:
    """
    retrieve_fn: a function(question: str) -> list[str] of retrieved
    section names, in ranked order. Injected as a parameter so this module
    stays testable without needing a live embedding model or Chroma index.
    """
    results = []
    for example in golden_set:
        retrieved_sections = retrieve_fn(example.question)
        precision, recall, rr = compute_metrics(example.expected_sections, retrieved_sections)
        results.append(RetrievalResult(
            example_id=example.id,
            question=example.question,
            expected_sections=example.expected_sections,
            retrieved_sections=retrieved_sections,
            precision=precision,
            recall=recall,
            reciprocal_rank=rr,
        ))
    return results


def summarize(results: list[RetrievalResult]) -> dict:
    n = len(results)
    return {
        "mean_precision": sum(r.precision for r in results) / n,
        "mean_recall": sum(r.recall for r in results) / n,
        "mean_reciprocal_rank": sum(r.reciprocal_rank for r in results) / n,
        "hit_rate": sum(1 for r in results if r.recall > 0) / n,
    }


if __name__ == "__main__":
    from config import load_config
    from embed import load_embedding_model, embed_texts
    from index import query_index

    cfg = load_config()
    golden_set = load_golden_set(cfg.evaluation.golden_set_path)
    print(f"Loaded {len(golden_set)} golden examples\n")

    model = load_embedding_model(cfg.embedding.model_name)

    def retrieve_fn(question: str) -> list[str]:
        query_embedding = embed_texts([question], model)[0]
        results = query_index(
            str(cfg.paths.chroma_dir), cfg.index.collection_name,
            query_embedding.tolist(), n_results=cfg.evaluation.n_results,
        )
        sections = []
        for meta in results["metadatas"][0]:
            sections.append(meta.get("h3", meta.get("h2", "unknown section")))
        return sections

    results = evaluate(golden_set, retrieve_fn)

    for r in results:
        status = "HIT" if r.recall > 0 else "MISS"
        print(f"[{status}] {r.example_id}: {r.question}")
        print(f"       expected: {r.expected_sections}")
        print(f"       retrieved: {r.retrieved_sections}")
        print(f"       precision={r.precision:.2f} recall={r.recall:.2f} rr={r.reciprocal_rank:.2f}\n")

    summary = summarize(results)
    print("--- Summary ---")
    for k, v in summary.items():
        print(f"{k}: {v:.3f}")