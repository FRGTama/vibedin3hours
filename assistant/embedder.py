import logging
import time

from google import genai
from google.genai import types as gemini_types

from assistant.config import AssistantConfig
from assistant.interfaces import Embedder

logger = logging.getLogger(__name__)

_MAX_BATCH_SIZE = 100
_BATCH_DELAY_SECONDS = 0.5


class GeminiEmbedder(Embedder):
    def __init__(self, config: AssistantConfig) -> None:
        self._client = genai.Client(api_key=config.gemini_api_key)
        self._model = config.embedding_model

    def embed(self, texts: list[str]) -> list[list[float]]:
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), _MAX_BATCH_SIZE):
            if i > 0:
                time.sleep(_BATCH_DELAY_SECONDS)
            batch = texts[i : i + _MAX_BATCH_SIZE]
            batch_embeddings = self._embed_batch(batch)
            all_embeddings.extend(batch_embeddings)
            logger.debug(
                "Embedded batch %d/%d (%d texts -> %d embeddings)",
                i // _MAX_BATCH_SIZE + 1,
                (len(texts) - 1) // _MAX_BATCH_SIZE + 1,
                len(batch),
                len(batch_embeddings),
            )
        logger.info("Embedded %d texts total.", len(all_embeddings))
        return all_embeddings

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        # Wrap each text as its own Content so the batch endpoint returns one
        # embedding per text instead of treating the list as parts of one content.
        contents = [
            gemini_types.Content(parts=[gemini_types.Part.from_text(text=text)])
            for text in texts
        ]
        response = self._client.models.embed_content(
            model=self._model,
            contents=contents,
        )
        return [emb.values for emb in response.embeddings if emb.values]
