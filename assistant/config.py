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


_OPTIBOT_SYSTEM_PROMPT = """You are OptiBot, the customer-support bot for OptiSigns.com.
• Tone: helpful, factual, concise.
• Only answer using the uploaded docs.
• Max 5 bullet points; else link to the doc.
• Cite up to 3 "Article URL:" lines per reply."""


@dataclass(frozen=True)
class AssistantConfig:
    gemini_api_key: str
    gemini_model: str
    embedding_model: str
    chroma_db_path: Path
    chroma_collection: str
    chunk_max_tokens: int
    chunk_overlap_tokens: int
    top_k: int
    system_prompt: str
    articles_dir: Path

    @classmethod
    def from_env(cls) -> "AssistantConfig":
        return cls(
            gemini_api_key=_require("GEMINI_API_KEY"),
            gemini_model=_optional("GEMINI_MODEL", "gemini-2.0-flash"),
            embedding_model=_optional("EMBEDDING_MODEL", "gemini-embedding-001"),
            chroma_db_path=Path(_optional("CHROMA_DB_PATH", "chroma_db")),
            chroma_collection=_optional("CHROMA_COLLECTION", "optisigns_docs"),
            chunk_max_tokens=int(_optional("CHUNK_MAX_TOKENS", "800")),
            chunk_overlap_tokens=int(_optional("CHUNK_OVERLAP_TOKENS", "150")),
            top_k=int(_optional("TOP_K", "5")),
            system_prompt=_optional("SYSTEM_PROMPT", _OPTIBOT_SYSTEM_PROMPT),
            articles_dir=Path(_optional("ARTICLES_DIR", "articles")),
        )
