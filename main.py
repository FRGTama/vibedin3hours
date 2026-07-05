import logging
import sys

from scraper.config import Config
from scraper.delta import SHA256DeltaDetector
from scraper.fetch import ZendeskArticleFetcher
from scraper.process import ZendeskArticleProcessor
from scraper.scraper import ScraperOrchestrator
from scraper.storage import LocalFileStorage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def main() -> None:
    try:
        config = Config.from_env()
    except ValueError as exc:
        logging.error("Configuration error: %s", exc)
        sys.exit(1)

    orchestrator = ScraperOrchestrator(
        fetcher=ZendeskArticleFetcher(config),
        processor=ZendeskArticleProcessor(),
        storage=LocalFileStorage(config),
        delta=SHA256DeltaDetector(),
    )

    summary = orchestrator.run()
    print(f"added={summary.added} updated={summary.updated} skipped={summary.skipped}")
    sys.exit(0)


if __name__ == "__main__":
    main()
