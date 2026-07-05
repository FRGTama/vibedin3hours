import hashlib
import logging

import chromadb

from assistant.config import AssistantConfig
from assistant.interfaces import (
    Chunk,
    RetrievalResult,
    VectorStore,
)

logger = logging.getLogger(__name__)


class ChromaVectorStore(VectorStore):
    def __init__(self, config: AssistantConfig) -> None:
        self._path = str(config.chroma_db_path)
        self._collection_name = config.chroma_collection
        self._client = chromadb.PersistentClient(path=self._path)
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> int:
        ids = [c.id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [
            {
                "article_id": c.article_id,
                "slug": c.slug,
                "url": c.url,
                "heading_path": c.heading_path,
                "sha256": _sha256(c.text),
            }
            for c in chunks
        ]
        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info("Upserted %d chunks into collection '%s'.", len(ids), self._collection_name)
        return len(ids)

    def query(
        self, query_embedding: list[float], top_k: int
    ) -> list[RetrievalResult]:
        raw = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        results: list[RetrievalResult] = []
        if not raw["ids"][0]:
            return results

        for idx, chunk_id in enumerate(raw["ids"][0]):
            meta = raw["metadatas"][0][idx]
            results.append(
                RetrievalResult(
                    chunk=Chunk(
                        article_id=int(meta["article_id"]),
                        slug=meta["slug"],
                        url=meta["url"],
                        heading_path=meta["heading_path"],
                        chunk_index=_parse_chunk_index(chunk_id),
                        text=raw["documents"][0][idx],
                    ),
                    distance=raw["distances"][0][idx],
                )
            )
        return results

    def get_existing_sha256(self, article_id: int) -> dict[int, str]:
        try:
            existing = self._collection.get(
                where={"article_id": article_id},
                include=["metadatas"],
            )
        except Exception:
            return {}

        result: dict[int, str] = {}
        for chunk_id, meta in zip(existing.get("ids", []), existing.get("metadatas", [])):
            chunk_idx = _parse_chunk_index(str(chunk_id))
            result[chunk_idx] = meta.get("sha256", "")
        return result

    def delete_by_article_id(self, article_id: int) -> None:
        try:
            existing = self._collection.get(
                where={"article_id": article_id},
            )
            ids = existing.get("ids", [])
            if ids:
                self._collection.delete(ids=ids)
                logger.debug("Deleted %d chunks for article %d.", len(ids), article_id)
        except Exception as exc:
            logger.warning("Failed to delete chunks for article %d: %s", article_id, exc)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_chunk_index(chunk_id: str) -> int:
    return int(chunk_id.rsplit("-", 1)[-1])
