"""
config.py
Loads pipeline settings from config.yaml so hyperparameters and paths live
in one place and can be logged alongside any index/output for reproducibility.
"""

from __future__ import annotations

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
    chroma_dir: Path


@dataclass
class ChunkingConfig:
    max_chunk_size: int
    overlap: int


@dataclass
class EmbeddingConfig:
    model_name: str


@dataclass
class IndexConfig:
    collection_name: str


@dataclass
class FeatureQuery:
    name: str
    query: str


@dataclass
class GenerationConfig:
    n_results: int
    output_dir: Path
    json_subdir: str
    csv_subdir: str
    filename_timestamp_format: str
    features: list[FeatureQuery]


@dataclass
class ExportConfig:
    target_json_file: str  # empty string means "use the most recently generated file"


@dataclass
class EvaluationConfig:
    golden_set_path: Path
    n_results: int
    faithfulness_output_subdir: str


@dataclass
class Config:
    paths: PathsConfig
    chunking: ChunkingConfig
    embedding: EmbeddingConfig
    index: IndexConfig
    generation: GenerationConfig
    export: ExportConfig
    evaluation: EvaluationConfig


def load_config(path: str | Path | None = None) -> Config:
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    raw = yaml.safe_load(config_path.read_text())
    features = [FeatureQuery(**f) for f in raw["generation"]["features"]]

    return Config(
        paths=PathsConfig(
            raw_docs_dir=PROJECT_ROOT / raw["paths"]["raw_docs_dir"],
            chroma_dir=PROJECT_ROOT / raw["paths"]["chroma_dir"],
        ),
        chunking=ChunkingConfig(**raw["chunking"]),
        embedding=EmbeddingConfig(**raw["embedding"]),
        index=IndexConfig(**raw["index"]),
        generation=GenerationConfig(
            n_results=raw["generation"]["n_results"],
            output_dir=PROJECT_ROOT / raw["generation"]["output_dir"],
            json_subdir=raw["generation"]["json_subdir"],
            csv_subdir=raw["generation"]["csv_subdir"],
            filename_timestamp_format=raw["generation"]["filename_timestamp_format"],
            features=features,
        ),
        export=ExportConfig(target_json_file=raw.get("export", {}).get("target_json_file", "")),
        evaluation=EvaluationConfig(
            golden_set_path=PROJECT_ROOT / raw["evaluation"]["golden_set_path"],
            n_results=raw["evaluation"]["n_results"],
            faithfulness_output_subdir=raw["evaluation"]["faithfulness_output_subdir"],
        ),
    )