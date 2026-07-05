from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


@dataclass(frozen=True)
class Article:
    id: int
    title: str
    body_html: str
    html_url: str
    updated_at: str


@dataclass(frozen=True)
class ProcessedArticle:
    article: Article
    slug: str
    markdown: str
    sha256: str


class DeltaLabel(Enum):
    ADDED = "added"
    UPDATED = "updated"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class DeltaResult:
    label: DeltaLabel
    processed: ProcessedArticle


class ArticleFetcher(ABC):
    @abstractmethod
    def fetch_all(self) -> list[Article]:
        raise NotImplementedError


class ArticleProcessor(ABC):
    @abstractmethod
    def process(self, articles: list[Article]) -> list[ProcessedArticle]:
        raise NotImplementedError


class FileStorage(ABC):
    @abstractmethod
    def save(self, processed: ProcessedArticle) -> None:
        raise NotImplementedError

    @abstractmethod
    def load_state(self) -> dict[int, str]:
        raise NotImplementedError

    @abstractmethod
    def save_state(self, state: dict[int, str]) -> None:
        raise NotImplementedError


class DeltaDetector(ABC):
    @abstractmethod
    def detect(
        self,
        processed: list[ProcessedArticle],
        old_state: dict[int, str],
    ) -> list[DeltaResult]:
        raise NotImplementedError
