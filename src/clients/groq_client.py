from __future__ import annotations

import json
import re
import time
from typing import Any

import requests


class GroqClient:
    endpoint = "https://api.groq.com/openai/v1/chat/completions"

    SYSTEM_PROMPT = (
        "You extract welfare scheme records from official Indian government webpages. "
        "Return only JSON with the exact keys requested. "
        "Use only facts found in provided page text. Do not invent data. "
        "If the page is not a scheme page, set is_scheme to false and fill only notes, source_url, confidence."
    )

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: int = 40,
        max_retries: int = 4,
        base_backoff_seconds: float = 1.5,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max(0, max_retries)
        self.base_backoff_seconds = max(0.1, base_backoff_seconds)

    def extract_scheme(self, page_url: str, page_title: str, page_text: str) -> dict[str, Any]:
        if not self.api_key:
            return {
                "is_scheme": False,
                "notes": "Missing GROQ_API_KEY",
                "source_url": page_url,
                "confidence": 0.0,
            }

        user_prompt = self._build_user_prompt(page_url, page_title, page_text)

        payload = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 1200,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error_note = ""
        data: dict[str, Any] | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    self.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout_seconds,
                )

                if response.status_code == 429 or response.status_code >= 500:
                    error_body = _short_text(response.text)
                    last_error_note = (
                        f"Groq transient error status={response.status_code} body={error_body}"
                    )
                    if attempt < self.max_retries:
                        sleep_seconds = self.base_backoff_seconds * (2**attempt)
                        retry_after = response.headers.get("Retry-After", "").strip()
                        if retry_after:
                            try:
                                sleep_seconds = max(sleep_seconds, float(retry_after))
                            except ValueError:
                                pass
                        time.sleep(sleep_seconds)
                        continue

                response.raise_for_status()
                data = response.json()
                break
            except Exception as exc:
                last_error_note = f"Groq request failed: {exc}"
                if attempt < self.max_retries:
                    sleep_seconds = self.base_backoff_seconds * (2**attempt)
                    time.sleep(sleep_seconds)
                    continue

        if data is None:
            return {
                "is_scheme": False,
                "notes": last_error_note or "Groq request failed",
                "source_url": page_url,
                "confidence": 0.0,
            }

        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        try:
            parsed = _extract_json_object(content)
        except Exception:
            return {
                "is_scheme": False,
                "notes": "Groq returned non-JSON output",
                "source_url": page_url,
                "confidence": 0.0,
                "raw_output": content,
            }

        if "source_url" not in parsed or not str(parsed.get("source_url", "")).strip():
            parsed["source_url"] = page_url

        if "confidence" not in parsed:
            parsed["confidence"] = 0.0

        return parsed

    @staticmethod
    def _build_user_prompt(page_url: str, page_title: str, page_text: str) -> str:
        truncated_text = page_text[:12000]

        schema = {
            "is_scheme": "boolean",
            "scheme_name": "string",
            "scheme_level": "STATE or CENTRAL",
            "administering_body": "string",
            "target_beneficiaries": "string",
            "eligibility_criteria": "string",
            "income_limit": "string",
            "age_range": "string",
            "benefit_description": "string",
            "benefit_amount": "string",
            "application_process": "string",
            "required_documents": ["string"],
            "application_url": "string",
            "tamil_nadu_relevance_reason": "string",
            "source_url": "string",
            "evidence_snippet": "string",
            "confidence": "number between 0 and 1",
            "notes": "string",
        }

        return (
            "Extract one welfare-scheme record from this page.\n"
            "If not a welfare scheme page, set is_scheme=false.\n"
            "Return strict JSON only.\n\n"
            f"Required keys: {json.dumps(schema, ensure_ascii=True)}\n\n"
            f"PAGE_URL: {page_url}\n"
            f"PAGE_TITLE: {page_title}\n"
            "PAGE_TEXT_START\n"
            f"{truncated_text}\n"
            "PAGE_TEXT_END\n"
        )


def _extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end < 0 or end <= start:
        raise ValueError("No JSON object found")

    return json.loads(cleaned[start : end + 1])


def _short_text(value: str, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", (value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."
