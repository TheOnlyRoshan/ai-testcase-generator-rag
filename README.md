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

## Current limitations
- Ingests Markdown (`.md`) source documents only.
- Production RAG pipelines typically normalize PDF/DOCX/HTML to Markdown
  at ingestion time (e.g. via Docling or MarkItDown) before chunking —
  this project's chunking/retrieval logic is already built against that
  assumption, so adding a conversion adapter is a drop-in v2 extension,
  not a redesign.