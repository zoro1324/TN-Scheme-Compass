from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from backend.models import Scheme


CSV_COLUMNS = {
    "scheme_id": "scheme_id",
    "scheme_name": "scheme_name",
    "scheme_level": "scheme_level",
    "administering_body": "administering_body",
    "target_beneficiaries": "target_beneficiaries",
    "eligibility_criteria": "eligibility_criteria",
    "income_limit": "income_limit",
    "age_range": "age_range",
    "benefit_description": "benefit_description",
    "benefit_amount": "benefit_amount",
    "application_process": "application_process",
    "required_documents": "required_documents",
    "application_url": "application_url",
    "tamil_nadu_relevance_reason": "tamil_nadu_relevance_reason",
    "source_url": "source_url",
    "source_domain": "source_domain",
    "evidence_snippet": "evidence_snippet",
    "extraction_method": "extraction_method",
    "confidence": "confidence",
    "last_verified_on": "last_verified_on",
    "notes": "notes",
}


def _clean(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none"}:
        return None
    return text


def load_schemes_if_empty(db: Session, csv_path: str) -> int:
    existing = db.query(Scheme.id).first()
    if existing:
        return 0

    file_path = Path(csv_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Scheme CSV not found: {csv_path}")

    df = pd.read_csv(file_path)
    inserted = 0

    for _, row in df.iterrows():
        scheme_id = _clean(row.get("scheme_id"))
        scheme_name = _clean(row.get("scheme_name"))
        if not scheme_id or not scheme_name:
            continue

        payload = {}
        for db_col, csv_col in CSV_COLUMNS.items():
            value = row.get(csv_col)
            if db_col == "confidence":
                try:
                    payload[db_col] = float(value) if pd.notna(value) else None
                except (TypeError, ValueError):
                    payload[db_col] = None
            else:
                payload[db_col] = _clean(value)

        db.add(Scheme(**payload))
        inserted += 1

    db.commit()
    return inserted
