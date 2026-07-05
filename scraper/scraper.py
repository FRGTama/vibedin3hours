import logging
from dataclasses import dataclass

from scraper.interfaces import (
    ArticleFetcher,
    ArticleProcessor,
    DeltaDetector,
    DeltaLabel,
    FileStorage,
)

logger = logging.getLogger(__name__)


@dataclass
class ScrapeSummary:
    added: int
    updated: int
    skipped: int


class ScraperOrchestrator:
    def __init__(
        self,
        fetcher: ArticleFetcher,
        processor: ArticleProcessor,
        storage: FileStorage,
        delta: DeltaDetector,
    ) -> None:
        self._fetcher = fetcher
        self._processor = processor
        self._storage = storage
        self._delta = delta

    def run(self) -> ScrapeSummary:
        logger.info("Fetching articles...")
        articles = self._fetcher.fetch_all()

        logger.info("Processing articles...")
        processed = self._processor.process(articles)

        logger.info("Detecting delta...")
        old_state = self._storage.load_state()
        delta_results = self._delta.detect(processed, old_state)

        new_state: dict[int, str] = dict(old_state)
        added = updated = skipped = 0

        for result in delta_results:
            aid = result.processed.article.id
            if result.label == DeltaLabel.ADDED:
                self._storage.save(result.processed)
                new_state[aid] = result.processed.sha256
                added += 1
            elif result.label == DeltaLabel.UPDATED:
                self._storage.save(result.processed)
                new_state[aid] = result.processed.sha256
                updated += 1
            elif result.label == DeltaLabel.SKIPPED:
                skipped += 1

        self._storage.save_state(new_state)
        logger.info("Run complete: added=%d updated=%d skipped=%d", added, updated, skipped)
        return ScrapeSummary(added=added, updated=updated, skipped=skipped)
