"""
ingest.py
Stage 1 of the pipeline: load raw documents from disk and return clean text.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Document:
    source_path: str
    text: str
    char_count: int


def load_document(file_path: str) -> Document:
    """Load a single document from an explicit path."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"No file found at {file_path}")

    text = path.read_text(encoding="utf-8")
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")

    return Document(source_path=str(path), text=text, char_count=len(text))


def load_documents_from_dir(dir_path: str, pattern: str = "*.md") -> list[Document]:
    """
    Load every document matching `pattern` in `dir_path`. This is the
    pipeline's real entry point -- as PRDs/Jira exports are added or removed
    from the folder, this picks them up automatically, no code changes.
    """
    dir_ = Path(dir_path)
    if not dir_.exists():
        raise FileNotFoundError(f"No directory found at {dir_path}")

    paths = sorted(dir_.glob(pattern))
    if not paths:
        raise FileNotFoundError(f"No files matching '{pattern}' found in {dir_path}")

    return [load_document(str(p)) for p in paths]


if __name__ == "__main__":
    from config import load_config

    cfg = load_config()
    docs = load_documents_from_dir(cfg.paths.raw_docs_dir)
    for doc in docs:
        print(f"Loaded {doc.char_count} characters from {doc.source_path}")