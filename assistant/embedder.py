import logging

from google import genai

from assistant.config import AssistantConfig
from assistant.interfaces import Embedder

logger = logging.getLogger(__name__)

_MAX_BATCH_SIZE = 100


class GeminiEmbedder(Embedder):
    def __init__(self, config: AssistantConfig) -> None:
        self._client = genai.Client(api_key=config.gemini_api_key)
        self._model = config.embedding_model

    def embed(self, texts: list[str]) -> list[list[float]]:
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), _MAX_BATCH_SIZE):
            batch = texts[i : i + _MAX_BATCH_SIZE]
            batch_embeddings = self._embed_batch(batch)
            all_embeddings.extend(batch_embeddings)
            logger.debug(
                "Embedded batch %d/%d (%d texts)",
                i // _MAX_BATCH_SIZE + 1,
                (len(texts) - 1) // _MAX_BATCH_SIZE + 1,
                len(batch),
            )
        logger.info("Embedded %d texts total.", len(texts))
        return all_embeddings

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = self._client.models.embed_content(
            model=self._model,
            contents=texts,
        )
        return [emb.values for emb in response.embeddings if emb.values]
