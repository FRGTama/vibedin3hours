import json
import logging
from pathlib import Path

from scraper.config import Config
from scraper.interfaces import FileStorage, ProcessedArticle

logger = logging.getLogger(__name__)


class LocalFileStorage(FileStorage):
    def __init__(self, config: Config) -> None:
        self._dir = config.articles_dir
        self._state_path = config.state_path

    def save(self, processed: ProcessedArticle) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        filename = f"{processed.article.id}-{processed.slug}.md"
        filepath = self._dir / filename
        filepath.write_text(processed.markdown, encoding="utf-8")
        logger.debug("Saved: %s", filename)

    def load_state(self) -> dict[int, str]:
        if not self._state_path.exists():
            logger.info("No existing state file, starting fresh.")
            return {}
        try:
            raw = json.loads(self._state_path.read_text(encoding="utf-8"))
            return {int(k): v for k, v in raw.items()}
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Corrupt state file, starting fresh: %s", exc)
            return {}

    def save_state(self, state: dict[int, str]) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        serialized = {str(k): v for k, v in state.items()}
        self._state_path.write_text(
            json.dumps(serialized, indent=2), encoding="utf-8"
        )
        logger.info("State saved to %s", self._state_path)
