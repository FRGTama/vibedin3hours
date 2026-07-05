import logging
import sys

from deploy import create_syncer
from scraper.config import Config as ScraperConfig
from scraper.delta import SHA256DeltaDetector
from scraper.fetch import ZendeskArticleFetcher
from scraper.process import ZendeskArticleProcessor
from scraper.scraper import ScraperOrchestrator
from scraper.storage import LocalFileStorage

from assistant.chunker import RecursiveChunker
from assistant.config import AssistantConfig
from assistant.embedder import GeminiEmbedder
from assistant.generator import GeminiGenerator
from assistant.vector_store import ChromaVectorStore
from assistant.assistant import AssistantOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("main")


def main() -> None:
    syncer = create_syncer()

    try:
        scraper_cfg = ScraperConfig.from_env()
    except ValueError as exc:
        logger.error("Scraper configuration error: %s", exc)
        sys.exit(1)

    try:
        assistant_cfg = AssistantConfig.from_env()
    except ValueError:
        logger.warning(
            "Assistant configuration not found (GEMINI_API_KEY missing). "
            "Skipping vector store ingestion."
        )
        assistant_cfg = None

    syncer.download_state(
        chroma_db_path=assistant_cfg.chroma_db_path if assistant_cfg else None,
        state_path=scraper_cfg.state_path,
    )

    scraper = ScraperOrchestrator(
        fetcher=ZendeskArticleFetcher(scraper_cfg),
        processor=ZendeskArticleProcessor(),
        storage=LocalFileStorage(scraper_cfg),
        delta=SHA256DeltaDetector(),
    )

    summary = scraper.run()
    print(f"scraper: added={summary.added} updated={summary.updated} skipped={summary.skipped}")

    if assistant_cfg is not None:
        assistant = AssistantOrchestrator(
            chunker=RecursiveChunker(
                max_tokens=assistant_cfg.chunk_max_tokens,
                overlap_tokens=assistant_cfg.chunk_overlap_tokens,
            ),
            embedder=GeminiEmbedder(assistant_cfg),
            vector_store=ChromaVectorStore(assistant_cfg),
            generator=GeminiGenerator(assistant_cfg),
            config=assistant_cfg,
        )
        ingest = assistant.ingest_all()
        print(
            f"assistant: files={ingest.files_ingested} "
            f"chunks_added={ingest.chunks_added} "
            f"chunks_updated={ingest.chunks_updated} "
            f"chunks_skipped={ingest.chunks_skipped}"
        )

    syncer.upload_state(
        chroma_db_path=assistant_cfg.chroma_db_path if assistant_cfg else None,
        state_path=scraper_cfg.state_path,
    )

    sys.exit(0)


if __name__ == "__main__":
    main()
