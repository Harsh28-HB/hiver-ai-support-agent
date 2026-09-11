"""Configuration and paths for the reproducible pipeline."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
    root: Path
    sample_rows: int = 50_000
    chunk_size: int = 100_000
    random_seed: int = 42
    max_representative_rows: int = 5

    @property
    def raw_dir(self) -> Path:
        return self.root / "data" / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.root / "data" / "processed"

    @property
    def golden_dir(self) -> Path:
        return self.root / "data" / "golden"

    @property
    def results_dir(self) -> Path:
        return self.root / "results"


def get_config(root: Path | None = None) -> PipelineConfig:
    """Return repository-relative paths without depending on the current directory."""
    project_root = (root or Path(__file__).resolve().parents[1]).resolve()
    return PipelineConfig(root=project_root)
