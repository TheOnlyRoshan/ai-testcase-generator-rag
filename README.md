# RAG-based test case generator

Generates QA test cases (happy path, edge case, negative) grounded in product
docs, PRDs today, Jira tickets as a planned extension using retrieval-
augmented generation with Claude.

Built end-to-end as a learning project, with a deliberate focus on the parts
most RAG demos skip: hand-built retrieval evaluation against a labeled golden
set, LLM-as-judge faithfulness evaluation, and reproducibility (pinned
embedding model, versioned index, config-driven everything, no hardcoded
paths, hyperparameters, or file names anywhere in the codebase).

## Status

All pipeline stages are complete and have been run end-to-end against a
real, complex PRD.

- [x] Document ingestion
- [x] Chunking (structure-aware, LangChain splitters)
- [x] Embedding (sentence-transformers, local, no API cost)
- [x] Vector index (ChromaDB, cosine distance, reproducibility manifest)
- [x] Retrieval + generation (Claude, multi-feature bulk generation)
- [x] Structured output (Pydantic-validated JSON)
- [x] CSV export (for TestRail/Xray-style import)
- [x] Retrieval evaluation (hand-built precision/recall/MRR + golden set)
- [x] Faithfulness evaluation (hand-built LLM-as-judge)

## Architecture

```
Source docs (PRDs, Jira*) -> Chunking -> Embedding -> Vector index (Chroma)
                                                              |
                                                              v
Query -> Retrieval (top-k, cosine) -> Claude -> Structured test cases (JSON)
                                                              |
                                                              v
                                                    CSV export | Evaluation
```
\* Jira ingestion is a planned extension; see Limitations below.

## Why this exists

Most "RAG over my docs" portfolio projects stop at "it retrieves something
and an LLM answers." This one exists to demonstrate the parts that actually
matter in production: *how do you know retrieval quality is good enough*,
and *can you show, with evidence, when generation isn't faithful to its
source*. Both questions are answered below with real numbers and named
examples, not just claimed.

## Project structure

```
data/raw/          source PRD(s)
data/golden_set/   12 hand-labeled question/expected-section pairs
src/                pipeline stages (ingest, chunk, embed, index, generate,
                    export_csv, schemas, config)
prompts/            versioned prompt templates (v1_test_case_gen.txt)
eval/               retrieval + faithfulness evaluation, own prompts/schemas
outputs/            sample generated output (JSON, CSV, faithfulness report)
config.yaml         every hyperparameter and path in the project
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Add your Anthropic API key to a `.env` file in the project root:
```
ANTHROPIC_API_KEY=sk-ant-...
```

## Running the pipeline

```bash
python src/ingest.py              # sanity-check document loading
python src/chunk.py               # inspect chunking output
python src/embed.py               # embed chunks, load model
python src/index.py               # build the Chroma index + run a sample query
python src/generate.py            # generate test cases for all configured features
python src/export_csv.py          # convert latest generated JSON to CSV
python eval/evaluate_retrieval.py     # retrieval metrics against the golden set
python eval/evaluate_faithfulness.py  # LLM-judged faithfulness of generated output
```

All hyperparameters (chunk size/overlap, embedding model, retrieval `k`,
which features to generate test cases for, output filename format) live in
`config.yaml`, no code changes needed to adjust any of them.

## Stack, and why

| Piece | Choice | Why |
|---|---|---|
| Chunking | LangChain's `MarkdownHeaderTextSplitter` + `RecursiveCharacterTextSplitter` | Started with a hand-built structure-aware chunker to understand the mid-word-cut and section-mixing failure modes firsthand, then swapped to the library version once the failure modes were understood, not before |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`), local | No API cost during development; fully reproducible via a pinned model name in config; embeddings never leave the machine |
| Vector store | ChromaDB | Purpose-built vector DB (HNSW under the hood) with metadata/ID/persistence handled for free, versus hand-rolling that on top of raw FAISS. At production scale (millions of chunks, high concurrency) teams typically move to a managed vector DB (Pinecone, Weaviate, Qdrant) or pgvector if already on Postgres |
| Generation | Claude (Anthropic API) | Structured JSON output, validated against a Pydantic schema so malformed output fails loudly rather than silently corrupting downstream data |
| Evaluation | Hand-built (not the `ragas` library) | See below |

### Why not the `ragas` library

Attempted first. Importing `ragas` triggers a broken dependency chain
(`ragas → langchain_community.chat_models.vertexai`, a module that no longer
exists in current `langchain_community`, which is itself being sunset).
Three different fixes were tried, installing `langchain_community`,
installing Google's Vertex AI SDK, pinning an older `langchain_community`
version — each one breaking a different downstream import. This is a real,
reproducible upstream issue, not a local misconfiguration.

Given that, evaluation was hand-built directly on the same Anthropic client
already used for generation: context precision/recall/MRR (pure set-overlap
math, no LLM needed) in `eval/evaluate_retrieval.py`, and an LLM-as-judge
faithfulness check (claim decomposition + per-claim support verification,
the same methodology `ragas.metrics.Faithfulness` uses internally) in
`eval/evaluate_faithfulness.py`. Same rigor, zero fragile dependencies, and
a clearer picture of what each metric actually measures.

## Evaluation results

**Retrieval** (12-example golden set, `eval/evaluate_retrieval.py`):

| Metric | Score |
|---|---|
| Hit rate | 91.7% (11/12) |
| Mean recall | 0.917 |
| Mean reciprocal rank | 0.778 |
| Mean precision | 0.196 (near the theoretical ceiling for k=5 with 1 expected section per question) |

**Faithfulness** (51 generated test cases, `eval/evaluate_faithfulness.py`):

| Metric | Score |
|---|---|
| Overall mean faithfulness | 0.588 |

Full per-example breakdowns are in `outputs/faithfulness/` and were used to
find and confirm two concrete failure cases below.

## Findings

**Retrieval favors prose over checklist-style content.** One golden-set
question ("what conditions must be true for self-serve customers to change
plans without contacting support") retrieved the PRD's Background section
instead of the more precise Acceptance Criteria section. Comparing the raw
chunks confirmed this isn't a chunking bug — both chunks are well-formed —
but a real embedding model limitation: dense narrative prose embeds more
distinctly than terse, structurally repetitive checklist bullets (`- [ ]
...`), even when the checklist is the more precise answer. A production fix
would likely involve a reranking step after initial retrieval, or lightly
rewriting checklist-style sections into prose during ingestion.

**A confirmed hallucination, caught by faithfulness evaluation.** A
generated test case, "Upgrade from Business (highest tier) attempted where
no higher plan exists," scored 0.00 — every claim flagged unsupported. A
full-text search of the source PRD for "highest," "no higher," and "top
tier" returned zero matches anywhere in the document. Claude generated a
plausible, sensible QA scenario from general SaaS-product knowledge, not
from anything actually retrieved. This is exactly the failure mode
faithfulness evaluation exists to catch, with concrete, reproducible
evidence rather than a suspicion.

## Current limitations

- Ingests Markdown (`.md`) source documents only. Production RAG pipelines
  typically normalize PDF/DOCX/HTML to Markdown at ingestion time (e.g. via
  Docling or MarkItDown) before chunking, this project's chunking/retrieval
  logic is already built against that assumption, so adding a conversion
  adapter is a drop-in v2 extension, not a redesign.
- Jira ticket ingestion is not implemented. Tickets are structured records
  (summary, description, acceptance criteria, comments, labels), not prose
  documents, and would need a separate ingestion adapter producing the same
  internal `Document` shape used today, plus metadata for filtering
  retrieval by ticket status/label.
- No reranking step. Retrieval is single-pass cosine similarity; the
  checklist-vs-prose finding above is the concrete case this would fix.
- Faithfulness evaluation re-retrieves context at eval time using the
  feature query stored in generated output, rather than snapshotting the
  exact chunks used at generation time. Correct as long as the index hasn't
  been rebuilt differently in between, but not fully self-contained.

## License

MIT
