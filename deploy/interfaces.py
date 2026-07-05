from abc import ABC, abstractmethod
from pathlib import Path


class StateSync(ABC):
    @abstractmethod
    def download_state(self, chroma_db_path: Path, state_path: Path) -> None:
        raise NotImplementedError

    @abstractmethod
    def upload_state(self, chroma_db_path: Path, state_path: Path) -> None:
        raise NotImplementedError
