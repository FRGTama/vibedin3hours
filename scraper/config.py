from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    import os

    value = os.getenv(name)
    if value is None:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _optional(name: str, default: str) -> str:
    import os

    return os.getenv(name, default)


@dataclass(frozen=True)
class Config:
    zendesk_subdomain: str
    zendesk_email: str
    zendesk_api_token: str
    articles_dir: Path
    state_file: Path
    rate_limit_delay: float
    max_retries: int

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            zendesk_subdomain=_require("ZENDESK_SUBDOMAIN"),
            zendesk_email=_require("ZENDESK_EMAIL"),
            zendesk_api_token=_require("ZENDESK_API_TOKEN"),
            articles_dir=Path(_optional("ARTICLES_DIR", "articles")),
            state_file=Path(_optional("STATE_FILE", "state.json")),
            rate_limit_delay=float(_optional("RATE_LIMIT_DELAY", "1.0")),
            max_retries=int(_optional("MAX_RETRIES", "3")),
        )

    @property
    def zendesk_base_url(self) -> str:
        return f"https://{self.zendesk_subdomain}.zendesk.com"

    @property
    def state_path(self) -> Path:
        return self.articles_dir / self.state_file
