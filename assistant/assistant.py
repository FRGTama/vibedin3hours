import hashlib
import logging
import re
from pathlib import Path

from assistant.config import AssistantConfig
from assistant.interfaces import (
    Answer,
    Chunk,
    Chunker,
    Embedder,
    Generator,
    IngestSummary,
    VectorStore,
)

logger = logging.getLogger(__name__)

_FILENAME_RE = re.compile(r"^(\d+)-(.+)\.md$")


class AssistantOrchestrator:
    def __init__(
        self,
        chunker: Chunker,
        embedder: Embedder,
        vector_store: VectorStore,
        generator: Generator,
        config: AssistantConfig,
    ) -> None:
        self._chunker = chunker
        self._embedder = embedder
        self._vector_store = vector_store
        self._generator = generator
        self._articles_dir = config.articles_dir

    def ingest(self, file_paths: list[Path]) -> IngestSummary:
        files_ingested = 0
        chunks_added = 0
        chunks_updated = 0
        chunks_skipped = 0
        all_changed_chunks: list[Chunk] = []

        # Phase 1: identify all changed chunks without any API calls.
        for fp in file_paths:
            parsed = _parse_filename(fp.name)
            if parsed is None:
                logger.warning("Skipping file with unparseable name: %s", fp)
                continue
            article_id, slug = parsed

            markdown = fp.read_text(encoding="utf-8")
            url = _build_url(article_id, slug)
            new_chunks = self._chunker.chunk(markdown, article_id, slug, url)
            if not new_chunks:
                continue

            existing_sha256s = self._vector_store.get_existing_sha256(article_id)
            for chunk in new_chunks:
                chunk_sha = _sha256(chunk.text)
                old_sha = existing_sha256s.get(chunk.chunk_index)
                if old_sha == chunk_sha:
                    chunks_skipped += 1
                else:
                    all_changed_chunks.append(chunk)
                    if old_sha is None:
                        chunks_added += 1
                    else:
                        chunks_updated += 1

            files_ingested += 1

        # Phase 2: batch embed and upsert all changed chunks together.
        if all_changed_chunks:
            texts = [c.text for c in all_changed_chunks]
            embeddings = self._embedder.embed(texts)
            self._vector_store.upsert(all_changed_chunks, embeddings)

        logger.info(
            "Ingest complete: files=%d, added=%d, updated=%d, skipped=%d",
            files_ingested,
            chunks_added,
            chunks_updated,
            chunks_skipped,
        )
        return IngestSummary(
            files_ingested=files_ingested,
            chunks_added=chunks_added,
            chunks_updated=chunks_updated,
            chunks_skipped=chunks_skipped,
        )

    def query(self, question: str, top_k: int | None = None) -> Answer:
        k = top_k or 5
        query_embeddings = self._embedder.embed([question])
        results = self._vector_store.query(query_embeddings[0], top_k=k)
        context_chunks = [r.chunk for r in results]
        logger.info(
            "Query: '%s' — retrieved %d chunks.", question[:80], len(context_chunks)
        )
        return self._generator.generate(question, context_chunks)

    def ingest_all(self) -> IngestSummary:
        md_files = sorted(self._articles_dir.glob("*.md"))
        logger.info("Found %d markdown files in %s.", len(md_files), self._articles_dir)
        return self.ingest(md_files)


def _parse_filename(filename: str) -> tuple[int, str] | None:
    match = _FILENAME_RE.match(filename)
    if not match:
        return None
    return int(match.group(1)), match.group(2)


def _build_url(article_id: int, slug: str) -> str:
    return f"https://support.optisigns.com/hc/en-us/articles/{article_id}-{slug}"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
