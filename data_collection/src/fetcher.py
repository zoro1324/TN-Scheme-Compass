from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from data_collection.src.models import PageContent


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def fetch_page_content(
    url: str,
    timeout_seconds: int,
    user_agent: str,
    max_chars: int = 16000,
) -> PageContent:
    headers = {
        "User-Agent": user_agent,
        "Accept-Language": "en-IN,en;q=0.9",
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout_seconds)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag_name in ["script", "style", "noscript", "svg", "iframe", "form"]:
            for node in soup.find_all(tag_name):
                node.decompose()

        title = ""
        if soup.title and soup.title.get_text(strip=True):
            title = _normalize_text(soup.title.get_text(" ", strip=True))

        main_node = soup.find("main") or soup.find("article")
        text_source = main_node.get_text(" ", strip=True) if main_node else soup.get_text(" ", strip=True)
        text = _normalize_text(text_source)

        if len(text) > max_chars:
            text = text[:max_chars]

        return PageContent(
            url=url,
            title=title,
            text=text,
            status_code=response.status_code,
            error=None,
        )
    except Exception as exc:
        return PageContent(
            url=url,
            title="",
            text="",
            status_code=None,
            error=str(exc),
        )
