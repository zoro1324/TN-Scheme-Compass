from __future__ import annotations

import json
import re
from typing import Any

import requests


class OllamaClient:
    SYSTEM_PROMPT = (
        "You extract welfare scheme records from official Indian government webpages. "
        "Return only JSON with the exact keys requested. "
        "Use only facts found in provided page text. Do not invent data. "
        "If the page is not a scheme page, set is_scheme to false and fill only notes, source_url, confidence."
    )

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434",
        timeout_seconds: int = 60,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.endpoint = f"{self.base_url}/api/chat"

    def extract_scheme(self, page_url: str, page_title: str, page_text: str) -> dict[str, Any]:
        user_prompt = self._build_user_prompt(page_url, page_title, page_text)

        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "options": {
                "temperature": 0,
            },
        }

        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            return {
                "is_scheme": False,
                "notes": f"Ollama request failed: {exc}",
                "source_url": page_url,
                "confidence": 0.0,
            }

        content = (
            data.get("message", {})
            .get("content", "")
            .strip()
        )

        try:
            parsed = _extract_json_object(content)
        except Exception:
            return {
                "is_scheme": False,
                "notes": "Ollama returned non-JSON output",
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