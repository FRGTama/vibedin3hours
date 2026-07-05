import logging
from pathlib import Path

from deploy.interfaces import StateSync

logger = logging.getLogger(__name__)


class NullStateSync(StateSync):
    def download_state(self, chroma_db_path: Path, state_path: Path) -> None:
        logger.info("No remote sync configured, using local state.")

    def upload_state(self, chroma_db_path: Path, state_path: Path) -> None:
        logger.info("No remote sync configured, skipping upload.")
