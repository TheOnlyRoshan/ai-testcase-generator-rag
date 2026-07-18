# RAG-based test case generator

Generates QA test cases (happy path, edge case, negative) grounded in real
product docs — PRDs and Jira tickets — using retrieval-augmented generation.

Built as a learning project with a deliberate focus on the parts most RAG
demos skip: retrieval evaluation against a hand-labeled golden set, and
reproducibility (pinned embedding model, versioned index).

## Status

🚧 Work in progress — built incrementally, one pipeline stage at a time.

- [x] Document ingestion
- [x] Chunking
- [ ] Embedding
- [ ] Vector index (Chroma)
- [ ] Retrieval + generation
- [ ] Structured output (Pydantic)
- [ ] Evaluation (RAGAS + golden set)
- [ ] Reproducibility/versioning layer

## Architecture

\`\`\`
Source docs (PRDs, Jira) -> Chunking -> Embedding -> Vector index
                                                            |
                                                            v
Query -> Retrieval (top-k) -> LLM generation -> Structured test cases
                                                            |
                                                            v
                                                   Evaluation (RAGAS)
\`\`\`

## Project structure

\`\`\`
data/raw/         source documents
data/golden_set/  hand-labeled examples for evaluation
src/              pipeline stages
prompts/          versioned prompt templates
eval/             RAGAS evaluation scripts
config.yaml       pinned model versions, chunking params
\`\`\`

## Setup

\`\`\`bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
\`\`\`

Uses ChromaDB for local persistence and metadata-aware retrieval, suited
to this project's scale. At production scale (millions of chunks, high
query concurrency), teams typically move to a managed vector DB (Pinecone,
Weaviate, Qdrant) or pgvector if already on Postgres.

## Current limitations
- Ingests Markdown (`.md`) source documents only.
- Production RAG pipelines typically normalize PDF/DOCX/HTML to Markdown
  at ingestion time (e.g. via Docling or MarkItDown) before chunking —
  this project's chunking/retrieval logic is already built against that
  assumption, so adding a conversion adapter is a drop-in v2 extension,
  not a redesign.

## Known limitation: retrieval favors prose over checklist-style content

Evaluation (`eval/evaluate_retrieval.py`) surfaced one golden-set miss:
a question closely matching the PRD's Acceptance Criteria section
instead retrieved the Background section, which restates similar
content in prose form. Comparing the raw chunks confirmed this isn't a
chunking bug -- both chunks are well-formed -- but a real embedding
model limitation: dense narrative prose embeds more distinctly than
terse, structurally repetitive checklist bullets (`- [ ] ...`), even
when the checklist is the more precise answer. A production fix would
likely involve either a reranking step after initial retrieval, or
lightly rewriting checklist-style PRD sections into prose during
ingestion specifically to improve their embedding quality.