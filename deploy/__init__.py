from deploy.config import SyncConfig
from deploy.interfaces import StateSync
from deploy.null_sync import NullStateSync
from deploy.s3_sync import S3StateSync


def create_syncer() -> StateSync:
    config = SyncConfig.from_env()
    if config is None:
        return NullStateSync()
    return S3StateSync(config)
