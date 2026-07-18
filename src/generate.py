"""
generate.py
Stage 5: retrieve relevant chunks for a feature/question, then ask an LLM
to generate structured test cases grounded only in that retrieved context.
"""

from __future__ import annotations

import json

from anthropic import Anthropic
from dotenv import load_dotenv

from config import load_config, PROJECT_ROOT
from embed import load_embedding_model, embed_texts
from index import query_index
from schemas import TestCaseSet

load_dotenv()

PROMPT_VERSION = "v1"
PROMPT_PATH = PROJECT_ROOT / "prompts" / f"{PROMPT_VERSION}_test_case_gen.txt"


def retrieve_context(query: str, cfg, model, n_results: int = 5) -> list[dict]:
    query_embedding = embed_texts([query], model)[0]
    results = query_index(
        str(cfg.paths.chroma_dir), cfg.index.collection_name, query_embedding.tolist(), n_results=n_results
    )
    chunks = []
    for doc_text, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        section = meta.get("h3", meta.get("h2", "unknown section"))
        chunks.append({"text": doc_text, "section": section, "distance": dist})
    return chunks


def build_prompt(feature_query: str, context_chunks: list[dict]) -> str:
    template = PROMPT_PATH.read_text()
    context_block = "\n\n".join(f"[Section: {c['section']}]\n{c['text']}" for c in context_chunks)
    prompt = template.replace("{{feature_query}}", feature_query)
    prompt = prompt.replace("{{context}}", context_block)
    return prompt


def parse_llm_response(raw_text: str) -> TestCaseSet:
    """
    Strip markdown code fences if the model added them despite being told
    not to -- LLMs do this often enough that handling it defensively is
    worth the few extra lines, rather than the pipeline failing on
    something this predictable.
    """
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse LLM response as JSON ({e}).\n"
            f"This usually means the response was cut off by max_tokens.\n"
            f"--- Raw response (last 500 chars) ---\n{text[-500:]}"
        ) from e

    return TestCaseSet(**parsed)


def generate_test_cases(feature_query: str, context_chunks: list[dict], model_name: str = "claude-sonnet-5") -> TestCaseSet:
    client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    prompt = build_prompt(feature_query, context_chunks)

    response = client.messages.create(
        model=model_name,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    text_blocks = [block.text for block in response.content if block.type == "text"]
    raw_text = "".join(text_blocks)
    return parse_llm_response(raw_text)


if __name__ == "__main__":
    cfg = load_config()
    embed_model = load_embedding_model(cfg.embedding.model_name)

    feature_query = "How does proration work when a customer upgrades or downgrades their plan?"
    context_chunks = retrieve_context(feature_query, cfg, embed_model, n_results=5)

    print(f"Retrieved {len(context_chunks)} chunks for grounding:\n")
    for c in context_chunks:
        print(f" - {c['section']} (distance={c['distance']:.4f})")

    print("\nGenerating test cases...\n")
    result = generate_test_cases(feature_query, context_chunks)

    print(f"Feature: {result.feature}\n")
    for i, tc in enumerate(result.test_cases, 1):
        print(f"{i}. [{tc.category.value}] {tc.title}")
        print(f"   Preconditions: {tc.preconditions}")
        print(f"   Steps: {tc.steps}")
        print(f"   Expected: {tc.expected_result}")
        print(f"   Source: {tc.source_section}\n")