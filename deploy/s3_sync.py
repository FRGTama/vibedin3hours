import logging
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from deploy.config import SyncConfig
from deploy.interfaces import StateSync

logger = logging.getLogger(__name__)


class S3StateSync(StateSync):
    def __init__(self, config: SyncConfig) -> None:
        self._bucket = config.s3_bucket
        self._prefix = config.s3_prefix.rstrip("/")
        self._s3 = boto3.client(
            "s3",
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
            region_name=config.aws_region,
        )

    def download_state(self, chroma_db_path: Path, state_path: Path) -> None:
        logger.info("Downloading state from s3://%s/%s", self._bucket, self._prefix)
        self._download_file(state_path)
        self._download_directory(chroma_db_path)

    def upload_state(self, chroma_db_path: Path, state_path: Path) -> None:
        logger.info("Uploading state to s3://%s/%s", self._bucket, self._prefix)
        self._upload_file(state_path)
        self._upload_directory(chroma_db_path)

    def _download_file(self, local_path: Path) -> None:
        key = f"{self._prefix}/{local_path.name}"
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            self._s3.download_file(self._bucket, key, str(local_path))
            logger.debug("Downloaded %s", key)
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "404":
                logger.info("No remote state file %s, starting fresh.", key)
            else:
                raise

    def _download_directory(self, local_dir: Path) -> None:
        try:
            response = self._s3.list_objects_v2(
                Bucket=self._bucket, Prefix=f"{self._prefix}/{local_dir.name}/"
            )
            for obj in response.get("Contents", []):
                key = obj["Key"]
                rel_path = key[len(f"{self._prefix}/") :]
                local_path = local_dir.parent / rel_path
                local_path.parent.mkdir(parents=True, exist_ok=True)
                self._s3.download_file(self._bucket, key, str(local_path))
                logger.debug("Downloaded %s", key)
        except ClientError as exc:
            logger.warning("Failed to list S3 directory: %s", exc)

    def _upload_file(self, local_path: Path) -> None:
        if not local_path.exists():
            logger.info("Local file %s does not exist, skipping upload.", local_path)
            return
        key = f"{self._prefix}/{local_path.name}"
        self._s3.upload_file(str(local_path), self._bucket, key)
        logger.debug("Uploaded %s", key)

    def _upload_directory(self, local_dir: Path) -> None:
        if not local_dir.exists():
            logger.info("Local directory %s does not exist, skipping upload.", local_dir)
            return
        for local_path in local_dir.rglob("*"):
            if local_path.is_file():
                rel_path = local_path.relative_to(local_dir.parent)
                key = f"{self._prefix}/{rel_path}"
                self._s3.upload_file(str(local_path), self._bucket, key)
                logger.debug("Uploaded %s", key)
