import logging

from scraper.interfaces import (
    DeltaDetector,
    DeltaLabel,
    DeltaResult,
    ProcessedArticle,
)

logger = logging.getLogger(__name__)


class SHA256DeltaDetector(DeltaDetector):
    def detect(
        self,
        processed: list[ProcessedArticle],
        old_state: dict[int, str],
    ) -> list[DeltaResult]:
        results: list[DeltaResult] = []
        for p in processed:
            aid = p.article.id
            old_hash = old_state.get(aid)
            if old_hash is None:
                label = DeltaLabel.ADDED
            elif old_hash != p.sha256:
                label = DeltaLabel.UPDATED
            else:
                label = DeltaLabel.SKIPPED
            results.append(DeltaResult(label=label, processed=p))
        self._log_summary(results)
        return results

    @staticmethod
    def _log_summary(results: list[DeltaResult]) -> None:
        added = sum(1 for r in results if r.label == DeltaLabel.ADDED)
        updated = sum(1 for r in results if r.label == DeltaLabel.UPDATED)
        skipped = sum(1 for r in results if r.label == DeltaLabel.SKIPPED)
        logger.info(
            "Delta: added=%d, updated=%d, skipped=%d",
            added,
            updated,
            skipped,
        )
