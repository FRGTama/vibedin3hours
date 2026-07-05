import json
import logging
import sys

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

logger = logging.getLogger("cli")


def build_orchestrator(config: AssistantConfig) -> AssistantOrchestrator:
    return AssistantOrchestrator(
        chunker=RecursiveChunker(
            max_tokens=config.chunk_max_tokens,
            overlap_tokens=config.chunk_overlap_tokens,
        ),
        embedder=GeminiEmbedder(config),
        vector_store=ChromaVectorStore(config),
        generator=GeminiGenerator(config),
        config=config,
    )


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python assistant/cli.py <question>", file=sys.stderr)
        print("Example: python assistant/cli.py \"How do I add a YouTube video?\"", file=sys.stderr)
        sys.exit(1)

    question = " ".join(sys.argv[1:])

    try:
        config = AssistantConfig.from_env()
    except ValueError as exc:
        logger.error("Configuration error: %s", exc)
        sys.exit(1)

    orchestrator = build_orchestrator(config)
    summary = orchestrator.ingest_all()
    logger.info(
        "Ingest: files=%d added=%d updated=%d skipped=%d",
        summary.files_ingested,
        summary.chunks_added,
        summary.chunks_updated,
        summary.chunks_skipped,
    )

    answer = orchestrator.query(question)
    print(json.dumps(answer.to_json(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
