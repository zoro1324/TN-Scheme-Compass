from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    tavily_api_key: str
    groq_api_key: str
    groq_model: str
    llm_provider: str
    ollama_model: str
    ollama_base_url: str
    groq_max_retries: int
    groq_backoff_seconds: float
    request_timeout_seconds: int
    max_results_per_query: int
    max_pages: int
    min_confidence: float
    user_agent: str


def load_settings() -> Settings:
    load_dotenv(override=False)

    tavily_api_key = os.getenv("TAVILY_API_KEY", "").strip()
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()

    return Settings(
        tavily_api_key=tavily_api_key,
        groq_api_key=groq_api_key,
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
        or "llama-3.3-70b-versatile",
        llm_provider=os.getenv("LLM_PROVIDER", "groq").strip().lower() or "groq",
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3:8b").strip() or "llama3:8b",
        ollama_base_url=(
            os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
            or "http://localhost:11434"
        ),
        groq_max_retries=_env_int("GROQ_MAX_RETRIES", 4),
        groq_backoff_seconds=_env_float("GROQ_BACKOFF_SECONDS", 1.5),
        request_timeout_seconds=_env_int("REQUEST_TIMEOUT_SECONDS", 30),
        max_results_per_query=_env_int("MAX_RESULTS_PER_QUERY", 20),
        max_pages=_env_int("MAX_PAGES", 250),
        min_confidence=_env_float("MIN_CONFIDENCE", 0.55),
        user_agent=os.getenv(
            "USER_AGENT", "TN-Scheme-Compass/1.0 (+official-schemes-extractor)"
        ).strip()
        or "TN-Scheme-Compass/1.0 (+official-schemes-extractor)",
    )
