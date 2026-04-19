from __future__ import annotations

from typing import Any, Callable

from data_collection.src.models import SchemeRecord


def is_scheme_output(raw: dict[str, Any]) -> bool:
    value = raw.get("is_scheme", False)
    if isinstance(value, bool):
        return value

    normalized = str(value).strip().lower()
    return normalized in {"true", "yes", "1"}


def validate_scheme_record(
    record: SchemeRecord,
    min_confidence: float,
    official_url_check: Callable[[str], bool],
) -> list[str]:
    reasons: list[str] = []

    if len(record.scheme_name) < 4:
        reasons.append("missing-or-short scheme_name")

    if record.scheme_level not in {"STATE", "CENTRAL"}:
        reasons.append("invalid scheme_level")

    if not record.source_url:
        reasons.append("missing source_url")
    elif not official_url_check(record.source_url):
        reasons.append("source_url not official")

    if len(record.evidence_snippet) < 24:
        reasons.append("missing evidence_snippet")

    if not record.tamil_nadu_relevance_reason:
        reasons.append("missing tamil_nadu_relevance_reason")

    if not record.benefit_description:
        reasons.append("missing benefit_description")

    if record.confidence < min_confidence:
        reasons.append("confidence below threshold")

    return reasons
