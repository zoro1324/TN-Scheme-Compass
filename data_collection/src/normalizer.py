from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any

from data_collection.src.models import SchemeRecord
from data_collection.src.source_registry import domain_from_url
def normalize_scheme_record(
    raw: dict[str, Any],
    fallback_source_url: str,
    extraction_method: str = "llm+official_source",
) -> SchemeRecord:
    scheme_name = _clean(raw.get("scheme_name", ""))
    scheme_level = _normalize_scheme_level(_clean(raw.get("scheme_level", "")))

    source_url = _clean(raw.get("source_url", "")) or fallback_source_url
    source_domain = domain_from_url(source_url)

    required_documents = _list_to_text(raw.get("required_documents", ""))
    confidence = _as_float(raw.get("confidence", 0.0))

    scheme_id = _build_scheme_id(
        scheme_name=scheme_name,
        scheme_level=scheme_level,
        source_url=source_url,
    )

    return SchemeRecord(
        scheme_id=scheme_id,
        scheme_name=scheme_name,
        scheme_level=scheme_level,
        administering_body=_clean(raw.get("administering_body", "")),
        target_beneficiaries=_clean(raw.get("target_beneficiaries", "")),
        eligibility_criteria=_clean(raw.get("eligibility_criteria", "")),
        income_limit=_clean(raw.get("income_limit", "")),
        age_range=_clean(raw.get("age_range", "")),
        benefit_description=_clean(raw.get("benefit_description", "")),
        benefit_amount=_clean(raw.get("benefit_amount", "")),
        application_process=_clean(raw.get("application_process", "")),
        required_documents=required_documents,
        application_url=_clean(raw.get("application_url", "")) or source_url,
        tamil_nadu_relevance_reason=_clean(raw.get("tamil_nadu_relevance_reason", "")),
        source_url=source_url,
        source_domain=source_domain,
        evidence_snippet=_clean(raw.get("evidence_snippet", "")),
        extraction_method=_clean(extraction_method) or "llm+official_source",
        confidence=confidence,
        last_verified_on=datetime.utcnow().strftime("%Y-%m-%d"),
        notes=_clean(raw.get("notes", "")),
    )


def deduplicate_records(records: list[SchemeRecord]) -> list[SchemeRecord]:
    best_by_key: dict[str, SchemeRecord] = {}

    for record in records:
        key = _dedupe_key(record)
        existing = best_by_key.get(key)
        if existing is None or record.confidence > existing.confidence:
            best_by_key[key] = record

    return list(best_by_key.values())


def _dedupe_key(record: SchemeRecord) -> str:
    scheme_name = re.sub(r"[^a-z0-9]+", "", record.scheme_name.lower())
    body = re.sub(r"[^a-z0-9]+", "", record.administering_body.lower())
    return f"{record.scheme_level}|{scheme_name}|{body}"


def _build_scheme_id(scheme_name: str, scheme_level: str, source_url: str) -> str:
    material = f"{scheme_name}|{scheme_level}|{source_url}".encode("utf-8")
    digest = hashlib.sha1(material).hexdigest()[:12]
    return f"TNWEL-{digest.upper()}"


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    return re.sub(r"\s+", " ", text).strip()


def _list_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(_clean(v) for v in value if _clean(v))
    return _clean(value)


def _as_float(value: Any) -> float:
    try:
        output = float(value)
    except (ValueError, TypeError):
        return 0.0

    if output < 0:
        return 0.0
    if output > 1:
        return 1.0
    return output


def _normalize_scheme_level(value: str) -> str:
    upper = value.strip().upper()
    if upper in {"STATE", "CENTRAL"}:
        return upper
    if "STATE" in upper:
        return "STATE"
    if "CENTRAL" in upper or "UNION" in upper:
        return "CENTRAL"
    return "UNKNOWN"
