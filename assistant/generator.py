import json
import logging

from google import genai
from google.genai import types as gemini_types

from assistant.config import AssistantConfig
from assistant.interfaces import Answer, Chunk, Generator

logger = logging.getLogger(__name__)

_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "title": {"type": "string"},
                },
                "required": ["url", "title"],
            },
            "maxItems": 3,
        },
    },
    "required": ["answer", "citations"],
}


class GeminiGenerator(Generator):
    def __init__(self, config: AssistantConfig) -> None:
        self._client = genai.Client(api_key=config.gemini_api_key)
        self._model = config.gemini_model
        self._system_prompt = config.system_prompt

    def generate(self, question: str, context_chunks: list[Chunk]) -> Answer:
        context_text = self._build_context(context_chunks)
        user_prompt = self._build_user_prompt(question, context_text)

        response = self._client.models.generate_content(
            model=self._model,
            contents=user_prompt,
            config=gemini_types.GenerateContentConfig(
                system_instruction=self._system_prompt,
                response_mime_type="application/json",
                response_json_schema=_RESPONSE_SCHEMA,
                temperature=0.2,
            ),
        )

        return self._parse_response(response.text, context_chunks)

    @staticmethod
    def _build_context(chunks: list[Chunk]) -> str:
        parts: list[str] = []
        for c in chunks:
            parts.append(f"--- Source: {c.url} ---\n{c.text}")
        return "\n\n".join(parts)

    @staticmethod
    def _build_user_prompt(question: str, context: str) -> str:
        return (
            "Answer the user's question using ONLY the documentation provided below.\n\n"
            "DOCUMENTATION:\n"
            f"{context}\n\n"
            f"USER QUESTION: {question}"
        )

    @staticmethod
    def _parse_response(
        raw_text: str, context_chunks: list[Chunk]
    ) -> Answer:
        try:
            data = json.loads(raw_text)
            answer_text = data.get("answer", raw_text)
            citations = data.get("citations", [])
        except json.JSONDecodeError:
            logger.warning("Gemini did not return valid JSON, using raw text.")
            answer_text = raw_text
            citations = [
                {"url": c.url, "title": ""} for c in context_chunks[:3]
            ]
        return Answer(answer=answer_text, citations=citations)
