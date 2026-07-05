import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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


def cmd_ingest(config: AssistantConfig) -> None:
    orchestrator = build_orchestrator(config)
    summary = orchestrator.ingest_all()
    logger.info(
        "Ingest: files=%d added=%d updated=%d skipped=%d",
        summary.files_ingested,
        summary.chunks_added,
        summary.chunks_updated,
        summary.chunks_skipped,
    )


def cmd_ask(config: AssistantConfig, question: str) -> None:
    orchestrator = build_orchestrator(config)
    answer = orchestrator.query(question)
    print(json.dumps(answer.to_json(), indent=2, ensure_ascii=False))


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage:", file=sys.stderr)
        print("  python -m assistant.cli ingest", file=sys.stderr)
        print("  python -m assistant.cli ask <question>", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    try:
        config = AssistantConfig.from_env()
    except ValueError as exc:
        logger.error("Configuration error: %s", exc)
        sys.exit(1)

    if command == "ingest":
        cmd_ingest(config)
    elif command == "ask":
        if len(sys.argv) < 3:
            print("Usage: python -m assistant.cli ask <question>", file=sys.stderr)
            sys.exit(1)
        question = " ".join(sys.argv[2:])
        cmd_ask(config, question)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print("Use 'ingest' or 'ask'.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
