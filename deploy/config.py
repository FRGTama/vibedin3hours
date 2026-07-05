from dataclasses import dataclass
import os


@dataclass(frozen=True)
class SyncConfig:
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    s3_bucket: str
    s3_prefix: str

    @classmethod
    def from_env(cls) -> "SyncConfig | None":
        aws_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_region = os.getenv("AWS_REGION")
        s3_bucket = os.getenv("S3_BUCKET")
        s3_prefix = os.getenv("S3_PREFIX", "state/")

        if not all([aws_key, aws_secret, aws_region, s3_bucket]):
            return None

        return cls(
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
            aws_region=aws_region,
            s3_bucket=s3_bucket,
            s3_prefix=s3_prefix,
        )
