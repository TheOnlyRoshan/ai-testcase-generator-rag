"""
index.py
Stage 4: build and query a persistent vector index (Chroma).

Chroma stores each chunk's embedding vector alongside its text and
metadata, and lets us search "find the chunks whose vectors are closest to
this query vector" -- the same similarity idea hand-verified in embed.py,
but indexed so it stays fast even over a huge collection.

We pass in embeddings we've already computed ourselves (via embed.py)
rather than letting Chroma compute its own -- this keeps us in control of
exactly which model produced them, which matters for the reproducibility
manifest written alongside the index.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import chromadb


def build_chunk_id(source_path: str, chunk_index: int) -> str:
    """
    Deterministic ID derived from source file + position, not a random
    UUID. Re-running the pipeline on unchanged docs produces the same IDs,
    so re-adding overwrites the existing entry instead of duplicating it.
    """
    return hashlib.sha256(f"{source_path}::{chunk_index}".encode()).hexdigest()[:16]


def build_index(chroma_dir: str, collection_name: str, chunks, embeddings, model_name: str, chunk_size: int, overlap: int):
    client = chromadb.PersistentClient(path=chroma_dir)

    # Drop and recreate so re-running always reflects the current config
    # and document set exactly -- no stale entries from a previous run
    # with different chunking parameters.
    existing = [c.name for c in client.list_collections()]
    if collection_name in existing:
        client.delete_collection(collection_name)
    collection = client.create_collection(collection_name, metadata={"hnsw:space": "cosine"})
    ids = [build_chunk_id(c.metadata["source"], i) for i, c in enumerate(chunks)]
    documents = [c.page_content for c in chunks]
    metadatas = [c.metadata for c in chunks]

    collection.add(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=documents,
        metadatas=metadatas,
    )

    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "embedding_model": model_name,
        "chunk_size": chunk_size,
        "chunk_overlap": overlap,
        "num_chunks": len(chunks),
        "source_docs": sorted(set(c.metadata["source"] for c in chunks)),
    }
    Path(chroma_dir).mkdir(parents=True, exist_ok=True)
    (Path(chroma_dir) / "index_manifest.json").write_text(json.dumps(manifest, indent=2))

    return collection


def query_index(chroma_dir: str, collection_name: str, query_embedding, n_results: int = 3):
    client = chromadb.PersistentClient(path=chroma_dir)
    collection = client.get_collection(collection_name)
    return collection.query(query_embeddings=[query_embedding], n_results=n_results)


if __name__ == "__main__":
    from ingest import load_documents_from_dir
    from chunk import chunk_document
    from embed import load_embedding_model, embed_texts
    from config import load_config

    cfg = load_config()
    docs = load_documents_from_dir(cfg.paths.raw_docs_dir)

    all_chunks = []
    for doc in docs:
        chunks = chunk_document(doc.text, chunk_size=cfg.chunking.max_chunk_size, chunk_overlap=cfg.chunking.overlap)
        for c in chunks:
            c.metadata["source"] = doc.source_path
        all_chunks.extend(chunks)

    model = load_embedding_model(cfg.embedding.model_name)
    embeddings = embed_texts([c.page_content for c in all_chunks], model)

    collection = build_index(
        str(cfg.paths.chroma_dir),
        cfg.index.collection_name,
        all_chunks,
        embeddings,
        cfg.embedding.model_name,
        cfg.chunking.max_chunk_size,
        cfg.chunking.overlap,
    )
    print(f"Indexed {collection.count()} chunks into {cfg.paths.chroma_dir}")

    # A real query, this time -- no hand-picked chunk index, just a
    # question in plain English embedded and searched like any user query
    # would be.
    question = "How does proration work when a customer upgrades?"
    query_embedding = embed_texts([question], model)[0]
    results = query_index(str(cfg.paths.chroma_dir), cfg.index.collection_name, query_embedding.tolist(), n_results=3)

    print(f"\nQuery: {question}\n")
    for i, (doc_text, meta, dist) in enumerate(zip(results["documents"][0], results["metadatas"][0], results["distances"][0])):
        section = meta.get("h3", meta.get("h2", "unknown section"))
        print(f"--- Result {i + 1} (distance={dist:.4f}, section: {section}) ---")
        print(doc_text[:200].replace("\n", " ") + "...\n")