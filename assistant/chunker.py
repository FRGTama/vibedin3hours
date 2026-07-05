import logging
import re

from assistant.interfaces import Chunk, Chunker

logger = logging.getLogger(__name__)

_CHARS_PER_TOKEN = 4
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


class RecursiveChunker(Chunker):
    def __init__(self, max_tokens: int, overlap_tokens: int) -> None:
        self._max_chars = max_tokens * _CHARS_PER_TOKEN
        self._overlap_chars = overlap_tokens * _CHARS_PER_TOKEN

    def chunk(
        self, markdown: str, article_id: int, slug: str, url: str
    ) -> list[Chunk]:
        sections = self._split_by_headings(markdown)
        raw_chunks = self._split_sections(sections)

        chunks: list[Chunk] = []
        for idx, raw in enumerate(raw_chunks):
            chunks.append(
                Chunk(
                    article_id=article_id,
                    slug=slug,
                    url=url,
                    heading_path=raw["heading"],
                    chunk_index=idx,
                    text=raw["text"],
                )
            )

        logger.debug(
            "Article %d: %d sections → %d chunks", article_id, len(sections), len(chunks)
        )
        return chunks

    def _split_by_headings(self, markdown: str) -> list[tuple[str, str]]:
        matches = list(_HEADING_RE.finditer(markdown))
        if not matches:
            return [(markdown.strip(), "")]

        sections: list[tuple[str, str]] = []
        heading_stack: list[str] = []

        for i, match in enumerate(matches):
            level = len(match.group(1))
            heading_text = match.group(2).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)

            while heading_stack and self._stack_level(heading_stack) >= level:
                heading_stack.pop()
            heading_stack.append(heading_text)

            body = markdown[start:end].strip()
            path = " > ".join(heading_stack)
            sections.append((body, path))

        return sections

    @staticmethod
    def _stack_level(stack: list[str]) -> int:
        return len(stack)

    def _split_sections(
        self, sections: list[tuple[str, str]]
    ) -> list[dict]:
        all_chunks: list[dict] = []
        for body, heading in sections:
            sub_chunks = self._split_block(body, heading)
            all_chunks.extend(sub_chunks)
        return self._apply_overlap(all_chunks)

    def _split_block(self, text: str, heading: str) -> list[dict]:
        if not text:
            return []

        if len(text) <= self._max_chars:
            return [{"heading": heading, "text": text}]

        return self._split_paragraphs(text, heading)

    def _split_paragraphs(self, text: str, heading: str) -> list[dict]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            return []

        results: list[dict] = []
        for para in paragraphs:
            if len(para) <= self._max_chars:
                results.append({"heading": heading, "text": para})
            else:
                results.extend(self._split_sentences(para, heading))
        return results

    def _split_sentences(self, text: str, heading: str) -> list[dict]:
        sentences = [s.strip() for s in _SENTENCE_RE.split(text) if s.strip()]
        results: list[dict] = []
        buffer: list[str] = []
        buf_len = 0

        for sentence in sentences:
            s_len = len(sentence)
            if buf_len + s_len > self._max_chars and buffer:
                results.append({"heading": heading, "text": " ".join(buffer)})
                buffer = [sentence]
                buf_len = s_len
            else:
                buffer.append(sentence)
                buf_len += s_len

        if buffer:
            results.append({"heading": heading, "text": " ".join(buffer)})
        return results

    def _apply_overlap(self, chunks: list[dict]) -> list[dict]:
        if self._overlap_chars <= 0 or len(chunks) < 2:
            return chunks

        for i in range(1, len(chunks)):
            prev = chunks[i - 1]["text"]
            if len(prev) > self._overlap_chars:
                overlap = prev[-self._overlap_chars :]
                chunks[i]["text"] = overlap + "\n\n" + chunks[i]["text"]

        return chunks
