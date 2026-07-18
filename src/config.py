"""
config.py
Loads pipeline settings from config.yaml so hyperparameters and paths live
in one place and can be logged alongside any index/output for reproducibility.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml

# config.py lives in src/, so the project root is one level up. Resolving
# this from __file__ (not the current working directory) means every path
# below is correct no matter where the script is launched from -- a
# terminal in the project root, PyCharm's default (script's own folder),
# or a CI runner.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"


@dataclass
class PathsConfig:
    raw_docs_dir: Path

@dataclass
class EmbeddingConfig:
    model_name: str

@dataclass
class ChunkingConfig:
    max_chunk_size: int
    overlap: int

@dataclass
class PathsConfig:
    raw_docs_dir: Path
    chroma_dir: Path

@dataclass
class IndexConfig:
    collection_name: str

@dataclass
class Config:
    paths: PathsConfig
    chunking: ChunkingConfig
    embedding: EmbeddingConfig
    index: IndexConfig

def load_config(path: str | Path | None = None) -> Config:
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    raw = yaml.safe_load(config_path.read_text())

    return Config(
        paths=PathsConfig(
            raw_docs_dir=PROJECT_ROOT / raw["paths"]["raw_docs_dir"],
            chroma_dir=PROJECT_ROOT / raw["paths"]["chroma_dir"],
        ),
        chunking=ChunkingConfig(**raw["chunking"]),
        embedding=EmbeddingConfig(**raw["embedding"]),
        index=IndexConfig(**raw["index"]),
    )