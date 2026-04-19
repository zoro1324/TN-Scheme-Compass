from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ACCEPTED_FIELDNAMES = [
    "scheme_id",
    "scheme_name",
    "scheme_level",
    "administering_body",
    "target_beneficiaries",
    "eligibility_criteria",
    "income_limit",
    "age_range",
    "benefit_description",
    "benefit_amount",
    "application_process",
    "required_documents",
    "application_url",
    "tamil_nadu_relevance_reason",
    "source_url",
    "source_domain",
    "evidence_snippet",
    "extraction_method",
    "confidence",
    "last_verified_on",
    "notes",
]

REVIEW_FIELDNAMES = [
    "source_url",
    "source_domain",
    "page_title",
    "reason",
    "confidence",
    "model_output_excerpt",
]


@dataclass
class SearchHit:
    query: str
    url: str
    title: str
    content: str
    score: float


@dataclass
class PageContent:
    url: str
    title: str
    text: str
    status_code: int | None
    error: str | None


@dataclass
class SchemeRecord:
    scheme_id: str
    scheme_name: str
    scheme_level: str
    administering_body: str
    target_beneficiaries: str
    eligibility_criteria: str
    income_limit: str
    age_range: str
    benefit_description: str
    benefit_amount: str
    application_process: str
    required_documents: str
    application_url: str
    tamil_nadu_relevance_reason: str
    source_url: str
    source_domain: str
    evidence_snippet: str
    extraction_method: str
    confidence: float
    last_verified_on: str
    notes: str


@dataclass
class ReviewRow:
    source_url: str
    source_domain: str
    page_title: str
    reason: str
    confidence: float
    model_output_excerpt: str


def build_review_row(
    source_url: str,
    source_domain: str,
    page_title: str,
    reason: str,
    confidence: float = 0.0,
    model_output_excerpt: str = "",
) -> ReviewRow:
    return ReviewRow(
        source_url=source_url,
        source_domain=source_domain,
        page_title=page_title,
        reason=reason,
        confidence=confidence,
        model_output_excerpt=model_output_excerpt,
    )


def model_excerpt(value: Any, max_chars: int = 500) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."
