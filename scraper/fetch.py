import logging
import time
from typing import Iterator

import requests

from scraper.config import Config
from scraper.interfaces import Article, ArticleFetcher

logger = logging.getLogger(__name__)


class ZendeskArticleFetcher(ArticleFetcher):
    def __init__(self, config: Config) -> None:
        self._base_url = config.zendesk_base_url
        self._auth = (f"{config.zendesk_email}/token", config.zendesk_api_token)
        self._delay = config.rate_limit_delay
        self._max_retries = config.max_retries

    def fetch_all(self) -> list[Article]:
        articles: list[Article] = []
        for batch in self._pages():
            articles.extend(batch)
        logger.info("Fetched %d articles total.", len(articles))
        return articles

    def _pages(self) -> Iterator[list[Article]]:
        url = f"{self._base_url}/api/v2/help_center/articles.json"
        page = 1
        per_page = 100

        while True:
            response = self._request_with_retry(
                "GET", url, params={"page": page, "per_page": per_page}
            )
            data = response.json()
            batch = self._parse_articles(data.get("articles", []))
            yield batch

            if data.get("next_page") is None:
                break
            page += 1

    def _parse_articles(self, raw: list[dict]) -> list[Article]:
        parsed: list[Article] = []
        for item in raw:
            if item.get("draft", False):
                continue
            try:
                parsed.append(
                    Article(
                        id=item["id"],
                        title=item["title"],
                        body_html=item["body"],
                        html_url=item["html_url"],
                        updated_at=item["updated_at"],
                    )
                )
            except KeyError as exc:
                logger.warning("Skipping article %s: missing field %s", item.get("id"), exc)
        return parsed

    def _request_with_retry(
        self, method: str, url: str, **kwargs
    ) -> requests.Response:
        attempt = 0
        while True:
            try:
                time.sleep(self._delay * attempt)
                response = requests.request(
                    method, url, auth=self._auth, timeout=30, **kwargs
                )
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    wait = int(retry_after) if retry_after else self._delay * (attempt + 1) * 10
                    logger.warning("Rate limited, waiting %ds...", wait)
                    time.sleep(wait)
                    attempt += 1
                    continue
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                attempt += 1
                if attempt > self._max_retries:
                    raise RuntimeError(
                        f"Request failed after {self._max_retries} retries: {exc}"
                    ) from exc
                logger.warning("Request failed (attempt %d/%d): %s", attempt, self._max_retries, exc)
