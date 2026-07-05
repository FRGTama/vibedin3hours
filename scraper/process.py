import hashlib
import logging
import re
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from markdownify import markdownify as _markdownify

from scraper.interfaces import Article, ArticleProcessor, ProcessedArticle

logger = logging.getLogger(__name__)

_ARTICLE_URL_PATTERN = re.compile(r"/articles/(\d+)")
_CLEAN_SLUG_PATTERN = re.compile(r"[^\w\-]+")


class ZendeskArticleProcessor(ArticleProcessor):
    def process(self, articles: list[Article]) -> list[ProcessedArticle]:
        id_to_slug = {a.id: _make_slug(a.title) for a in articles}
        results: list[ProcessedArticle] = []

        for article in articles:
            slug = id_to_slug[article.id]
            cleaned_html = self._extract_body(article.body_html)
            resolved_html = self._resolve_links(cleaned_html, article.html_url, id_to_slug)
            markdown = self._to_markdown(resolved_html, article.html_url)
            sha256 = hashlib.sha256(markdown.encode("utf-8")).hexdigest()

            results.append(
                ProcessedArticle(
                    article=article,
                    slug=slug,
                    markdown=markdown,
                    sha256=sha256,
                )
            )

        logger.info("Processed %d articles.", len(results))
        return results

    @staticmethod
    def _extract_body(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        body = soup.select_one(".article-body")
        if body is not None:
            return str(body)
        logger.debug("No .article-body found, using full HTML body.")
        return html

    @staticmethod
    def _resolve_links(
        html: str, base_url: str, id_to_slug: dict[int, str]
    ) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for a_tag in soup.find_all("a", href=True):
            resolved = _resolve_href(str(a_tag["href"]), base_url, id_to_slug)
            if resolved is not None:
                a_tag["href"] = resolved
        return str(soup)

    @staticmethod
    def _to_markdown(html: str, base_url: str) -> str:
        md = _markdownify(
            html,
            heading_style="ATX",
            bullets="-",
            strip=["script", "style"],
        )
        return md.strip()


def _make_slug(title: str) -> str:
    slug = title.lower().strip()
    slug = _CLEAN_SLUG_PATTERN.sub("-", slug)
    slug = slug.strip("-")
    return slug


def _resolve_href(
    href: str,
    base_url: str,
    id_to_slug: dict[int, str],
) -> Optional[str]:
    article_id = _extract_article_id(href)
    if article_id is None:
        return None
    if article_id not in id_to_slug:
        return None
    return f"{article_id}-{id_to_slug[article_id]}.md"


def _extract_article_id(url: str) -> Optional[int]:
    parsed = urlparse(url)
    path = parsed.path
    match = _ARTICLE_URL_PATTERN.search(path)
    if match is None:
        return None
    return int(match.group(1))
