import json
import re
from typing import Any

from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import ChatMessage, ChatSession, Scheme, UserProfile
from backend.schemas import SchemeCard
from backend.services.llm_orchestrator import LLMOrchestrator
from backend.services.vector_store import SchemeVectorStore


class ChatService:
    def __init__(self, vector_store: SchemeVectorStore, llm: LLMOrchestrator):
        self.vector_store = vector_store
        self.llm = llm
        # Keep eligibility intake lightweight: only block on high-signal fields.
        self.required_profile_fields = ["age", "income", "occupation"]

    def create_session(self, db: Session) -> ChatSession:
        session = ChatSession()
        db.add(session)
        db.flush()

        profile = UserProfile(session_id=session.id, profile_json="{}")
        db.add(profile)
        db.commit()
        db.refresh(session)
        return session

    def handle_message(self, db: Session, session_id: str, message: str) -> dict[str, Any]:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise ValueError("Session not found")

        profile_row = db.query(UserProfile).filter(UserProfile.session_id == session_id).first()
        profile = json.loads(profile_row.profile_json) if profile_row and profile_row.profile_json else {}

        db.add(ChatMessage(session_id=session_id, role="user", content=message))

        updates = self.llm.extract_profile_updates(message=message, current_profile=profile)
        profile.update(updates)

        if profile_row:
            profile_row.profile_json = json.dumps(profile)

        missing_fields = [f for f in self.required_profile_fields if not self._has_profile_value(profile, f)]

        schemes: list[Scheme] = []
        scheme_cards: list[SchemeCard] = []
        context = ""
        can_recommend = not missing_fields

        if can_recommend:
            schemes = self._get_relevant_schemes(db, message, profile)
            scheme_cards = [self._to_scheme_card(s, profile) for s in schemes]
            context = self._build_scheme_context(schemes)

        follow_up = self.llm.dynamic_follow_up_question(
            user_message=message,
            profile=profile,
            missing_fields=missing_fields,
            scheme_context=context,
        )

        reply = self.llm.compose_reply(
            user_message=message,
            profile=profile,
            scheme_context=context,
            follow_up_question=follow_up,
            can_recommend=can_recommend,
            missing_fields=missing_fields,
            scheme_count=len(scheme_cards),
        )

        db.add(ChatMessage(session_id=session_id, role="assistant", content=reply, meta_json=json.dumps({"follow_up": follow_up})))
        db.commit()

        return {
            "reply": reply,
            "follow_up_question": follow_up,
            "schemes": scheme_cards,
            "profile": profile,
        }

    def _has_profile_value(self, profile: dict[str, Any], field: str) -> bool:
        value = profile.get(field)
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        return True

    def get_history(self, db: Session, session_id: str) -> dict[str, Any]:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise ValueError("Session not found")

        profile_row = db.query(UserProfile).filter(UserProfile.session_id == session_id).first()
        profile = json.loads(profile_row.profile_json) if profile_row and profile_row.profile_json else {}

        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
            .all()
        )

        return {
            "profile": profile,
            "messages": messages,
        }

    def _get_relevant_schemes(self, db: Session, message: str, profile: dict[str, Any]) -> list[Scheme]:
        query_text = message
        if profile:
            query_text = f"{message} | profile: {profile}"

        candidate_k = max(settings.retrieval_top_k * 4, settings.retrieval_top_k)
        ids = self.vector_store.query(query_text, top_k=candidate_k)
        if not ids:
            candidates = db.query(Scheme).order_by(Scheme.confidence.desc()).limit(candidate_k).all()
        else:
            scheme_by_id = {
                scheme.id: scheme for scheme in db.query(Scheme).filter(Scheme.id.in_(ids)).all()
            }
            candidates = [scheme_by_id[i] for i in ids if i in scheme_by_id]

        filtered = [scheme for scheme in candidates if self._is_scheme_eligible(scheme, profile)]
        ranked = sorted(filtered, key=lambda scheme: self._score_scheme_match(scheme, profile), reverse=True)

        return ranked[: settings.retrieval_top_k]

    def _build_scheme_context(self, schemes: list[Scheme]) -> str:
        lines = []
        for scheme in schemes[:3]:
            lines.append(
                f"{scheme.scheme_name}: eligibility={scheme.eligibility_criteria}; "
                f"benefit={scheme.benefit_description}; amount={scheme.benefit_amount}; "
                f"docs={scheme.required_documents}; apply={scheme.application_process}"
            )
        return "\n".join(lines)

    def _to_scheme_card(self, scheme: Scheme, profile: dict[str, Any]) -> SchemeCard:
        reason_parts = []
        scheme_text = self._scheme_text(scheme)

        if profile.get("gender") and profile["gender"].lower() in scheme_text:
            reason_parts.append("Target beneficiaries match your profile")
        if profile.get("income") and scheme.income_limit:
            reason_parts.append(f"Scheme income note: {scheme.income_limit}")
        if profile.get("age") and scheme.age_range:
            reason_parts.append(f"Scheme age note: {scheme.age_range}")
        if profile.get("occupation") and "student" in str(profile["occupation"]).lower() and any(
            token in scheme_text for token in ["student", "scholarship", "education", "college", "school"]
        ):
            reason_parts.append("Education/student criteria appear relevant")
        if not reason_parts:
            reason_parts.append("Ranked relevant to your query")

        return SchemeCard(
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.scheme_name,
            scheme_level=scheme.scheme_level,
            administering_body=scheme.administering_body,
            target_beneficiaries=scheme.target_beneficiaries,
            eligibility_criteria=scheme.eligibility_criteria,
            income_limit=scheme.income_limit,
            age_range=scheme.age_range,
            benefit_description=scheme.benefit_description,
            benefit_amount=scheme.benefit_amount,
            application_process=scheme.application_process,
            required_documents=scheme.required_documents,
            application_url=scheme.application_url,
            source_url=scheme.source_url,
            confidence=scheme.confidence,
            match_reason=" | ".join(reason_parts),
        )

    def _scheme_text(self, scheme: Scheme) -> str:
        return " ".join(
            [
                scheme.scheme_name or "",
                scheme.target_beneficiaries or "",
                scheme.eligibility_criteria or "",
                scheme.age_range or "",
                scheme.income_limit or "",
                scheme.notes or "",
            ]
        ).lower()

    def _parse_amount(self, text: str) -> int | None:
        if not text:
            return None

        normalized = text.lower().replace(",", "")
        if any(token in normalized for token in ["no limit", "not applicable", "n/a"]):
            return None

        match = re.search(r"(\d+(?:\.\d+)?)\s*(k|thousand|lakh|lakhs|crore|crores)?", normalized)
        if not match:
            return None

        amount = float(match.group(1))
        unit = (match.group(2) or "").strip()
        multiplier = 1
        if unit in {"k", "thousand"}:
            multiplier = 1_000
        elif unit in {"lakh", "lakhs"}:
            multiplier = 100_000
        elif unit in {"crore", "crores"}:
            multiplier = 10_000_000

        return int(amount * multiplier)

    def _age_bounds_from_text(self, text: str) -> tuple[int | None, int | None]:
        if not text:
            return None, None

        normalized = text.lower()
        min_age = None
        max_age = None

        range_match = re.search(r"(\d{1,2})\s*(?:-|to)\s*(\d{1,2})", normalized)
        if range_match:
            min_age = int(range_match.group(1))
            max_age = int(range_match.group(2))

        min_match = re.search(r"(?:minimum|min|above|over)\s*(\d{1,2})", normalized)
        if min_match:
            min_age = int(min_match.group(1))

        max_match = re.search(r"(?:maximum|max|below|under)\s*(\d{1,2})", normalized)
        if max_match:
            max_age = int(max_match.group(1))

        if "senior citizen" in normalized:
            min_age = max(min_age or 60, 60)

        if any(token in normalized for token in ["girl child", "children", "child"]):
            if max_age is None:
                max_age = 18

        return min_age, max_age

    def _is_gender_restricted_out(self, profile_gender: str | None, scheme_text: str) -> bool:
        if not profile_gender:
            return False

        g = profile_gender.lower().strip()
        female_only_tokens = ["women", "woman", "female", "girl", "widow", "mother", "pregnant"]
        male_only_tokens = ["male", "men", "man", "boy"]
        transgender_only_tokens = ["transgender"]

        if g == "male" and any(token in scheme_text for token in female_only_tokens):
            return True
        if g == "female" and any(token in scheme_text for token in male_only_tokens):
            return True
        if g != "transgender" and any(token in scheme_text for token in transgender_only_tokens):
            return True

        return False

    def _is_scheme_eligible(self, scheme: Scheme, profile: dict[str, Any]) -> bool:
        scheme_text = self._scheme_text(scheme)

        if self._is_gender_restricted_out(profile.get("gender"), scheme_text):
            return False

        age = profile.get("age")
        if isinstance(age, (int, float)):
            min_age, max_age = self._age_bounds_from_text(" ".join([scheme.age_range or "", scheme.eligibility_criteria or "", scheme.scheme_name or ""]))
            if min_age is not None and age < min_age:
                return False
            if max_age is not None and age > max_age:
                return False

        income = profile.get("income")
        if isinstance(income, (int, float)):
            limit = self._parse_amount(" ".join([scheme.income_limit or "", scheme.eligibility_criteria or ""]))
            if limit is not None and income > limit:
                return False

        return True

    def _score_scheme_match(self, scheme: Scheme, profile: dict[str, Any]) -> float:
        score = float(scheme.confidence or 0.0)
        scheme_text = self._scheme_text(scheme)

        occupation = str(profile.get("occupation") or "").lower()
        if "student" in occupation and any(token in scheme_text for token in ["student", "scholarship", "education", "college", "school"]):
            score += 4.0

        caste = str(profile.get("caste") or "").lower()
        if caste and caste in scheme_text:
            score += 1.5
        elif caste == "mbc" and "bc" in scheme_text:
            score += 0.8

        income = profile.get("income")
        if isinstance(income, (int, float)):
            limit = self._parse_amount(" ".join([scheme.income_limit or "", scheme.eligibility_criteria or ""]))
            if limit is not None and income <= limit:
                score += 1.5

        age = profile.get("age")
        if isinstance(age, (int, float)):
            min_age, max_age = self._age_bounds_from_text(" ".join([scheme.age_range or "", scheme.eligibility_criteria or "", scheme.scheme_name or ""]))
            if (min_age is None or age >= min_age) and (max_age is None or age <= max_age):
                score += 1.0

        return score
