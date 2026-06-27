from abc import ABC, abstractmethod
from pathlib import Path


class BaseSource(ABC):
    """Interface every region's source module implements."""

    def __init__(self, region_config: dict, temp_dir: Path):
        self.region_config = region_config
        self.temp_dir = temp_dir

    @abstractmethod
    def discover(self) -> list[dict]:
        """Return a list of dicts describing available remote items
        (e.g. PDF links), not yet downloaded. Shape is source-specific
        but must include at minimum: 'filename' and a way to fetch it
        (e.g. 'url')."""
        raise NotImplementedError

    @abstractmethod
    def acquire(self, items: list[dict]) -> list[Path]:
        """Download the given items into self.temp_dir, return local paths."""
        raise NotImplementedError
