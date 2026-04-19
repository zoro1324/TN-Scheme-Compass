from __future__ import annotations

from typing import Iterable

import requests

from src.models import SearchHit


class TavilyClient:
    endpoint = "https://api.tavily.com/search"

    def __init__(self, api_key: str, timeout_seconds: int = 30) -> None:
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def search(
        self,
        query: str,
        include_domains: Iterable[str],
        max_results: int,
    ) -> list[SearchHit]:
        if not self.api_key:
            return []

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": max(1, max_results),
            "include_domains": list(include_domains),
            "include_raw_content": False,
        }

        response = requests.post(
            self.endpoint,
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

        data = response.json()
        raw_results = data.get("results", [])

        hits: list[SearchHit] = []
        for item in raw_results:
            url = str(item.get("url", "")).strip()
            if not url:
                continue

            hits.append(
                SearchHit(
                    query=query,
                    url=url,
                    title=str(item.get("title", "")).strip(),
                    content=str(item.get("content", "")).strip(),
                    score=_as_float(item.get("score", 0.0)),
                )
            )

        return hits


def _as_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
