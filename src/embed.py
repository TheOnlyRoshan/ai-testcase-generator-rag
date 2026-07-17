"""
embed.py
Stage 3: convert chunk text into embedding vectors.

An embedding model maps a piece of text to a fixed-length vector of numbers
such that texts with similar meaning end up as vectors that are close
together in that vector space. This is the foundation the vector index
(next step) searches over.

Model choice matters for reproducibility: if you re-embed later with a
different model (or a different version of the same model), the new
vectors are NOT comparable to old ones already stored in an index. That's
why the model name is pinned in config.yaml rather than hardcoded here.
"""

from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer


def load_embedding_model(model_name: str) -> SentenceTransformer:
    return SentenceTransformer(model_name)


def embed_texts(texts: list[str], model: SentenceTransformer) -> np.ndarray:
    """
    Embed a list of texts into an (n_texts, embedding_dim) array.
    Batching all texts in one .encode() call is significantly faster than
    looping and encoding one string at a time.
    """
    return model.encode(texts, show_progress_bar=False)


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Cosine similarity computed by hand, no library shortcut -- so it's
    clear this is just the cosine of the angle between two vectors.
    1.0 = same direction (same meaning), 0.0 = unrelated, -1.0 = opposite.
    This is exactly what a vector database does internally on every
    similarity search -- we're doing it manually once so it's not magic.
    """
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    return dot_product / (norm_a * norm_b)


if __name__ == "__main__":
    from ingest import load_documents_from_dir
    from chunk import chunk_document
    from config import load_config

    cfg = load_config()
    docs = load_documents_from_dir(cfg.paths.raw_docs_dir)

    all_chunks = []
    for doc in docs:
        chunks = chunk_document(
            doc.text,
            chunk_size=cfg.chunking.max_chunk_size,
            chunk_overlap=cfg.chunking.overlap,
        )
        for c in chunks:
            c.metadata["source"] = doc.source_path
        all_chunks.extend(chunks)

    print(f"Loading embedding model: {cfg.embedding.model_name}")
    model = load_embedding_model(cfg.embedding.model_name)

    texts = [c.page_content for c in all_chunks]
    embeddings = embed_texts(texts, model)
    print(f"Embedded {len(texts)} chunks -> vector shape {embeddings.shape}\n")

    #--- one-time sanity check, superseded by RAGAS eval in eval/ ---
    # def find_chunk_index(keyword: str) -> int:
    #     for i, c in enumerate(all_chunks):
    #         if keyword in c.page_content:
    #             return i
    #     raise ValueError(f"No chunk found containing '{keyword}'")
    #
    # # FR3 (upgrade) and FR4 (downgrade) are different requirements but both
    # # about plan changes -- expect moderate-to-high similarity.
    # idx_fr3 = find_chunk_index("prorated_charge")
    # idx_fr4 = find_chunk_index("does NOT take")
    # # Rollout plan is a totally different topic -- expect clearly lower similarity.
    # idx_rollout = find_chunk_index("Phase 1 (Sprint 14)")
    #
    # sim_related = cosine_similarity(embeddings[idx_fr3], embeddings[idx_fr4])
    # sim_unrelated = cosine_similarity(embeddings[idx_fr3], embeddings[idx_rollout])
    #
    # print(f"Similarity FR3 (upgrade) <-> FR4 (downgrade): {sim_related:.4f}")
    # print(f"Similarity FR3 (upgrade) <-> Rollout plan:    {sim_unrelated:.4f}")