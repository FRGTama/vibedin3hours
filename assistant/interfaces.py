from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scraper.interfaces import DeltaResult


@dataclass(frozen=True)
class Chunk:
    article_id: int
    slug: str
    url: str
    heading_path: str
    chunk_index: int
    text: str

    @property
    def id(self) -> str:
        return f"{self.article_id}-{self.chunk_index}"


@dataclass(frozen=True)
class RetrievalResult:
    chunk: Chunk
    distance: float


@dataclass(frozen=True)
class Answer:
    answer: str
    citations: list[dict]

    def to_json(self) -> dict:
        return {"answer": self.answer, "citations": self.citations}


@dataclass
class IngestSummary:
    files_ingested: int
    chunks_added: int
    chunks_updated: int
    chunks_skipped: int


class Chunker(ABC):
    @abstractmethod
    def chunk(self, markdown: str, article_id: int, slug: str, url: str) -> list[Chunk]:
        raise NotImplementedError


class Embedder(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> int:
        raise NotImplementedError

    @abstractmethod
    def query(self, query_embedding: list[float], top_k: int) -> list[RetrievalResult]:
        raise NotImplementedError

    @abstractmethod
    def get_existing_sha256(self, article_id: int) -> dict[int, str]:
        raise NotImplementedError

    @abstractmethod
    def delete_by_article_id(self, article_id: int) -> None:
        raise NotImplementedError


class Generator(ABC):
    @abstractmethod
    def generate(self, question: str, context_chunks: list[Chunk]) -> Answer:
        raise NotImplementedError
