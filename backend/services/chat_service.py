import json
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

        ids = self.vector_store.query(query_text, top_k=settings.retrieval_top_k)
        if not ids:
            return db.query(Scheme).order_by(Scheme.confidence.desc()).limit(settings.retrieval_top_k).all()

        scheme_by_id = {
            scheme.id: scheme for scheme in db.query(Scheme).filter(Scheme.id.in_(ids)).all()
        }
        return [scheme_by_id[i] for i in ids if i in scheme_by_id]

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
        if profile.get("gender") and scheme.target_beneficiaries and profile["gender"].lower() in scheme.target_beneficiaries.lower():
            reason_parts.append("Target beneficiaries match your profile")
        if profile.get("income") and scheme.income_limit:
            reason_parts.append(f"Scheme income note: {scheme.income_limit}")
        if profile.get("age") and scheme.age_range:
            reason_parts.append(f"Scheme age note: {scheme.age_range}")
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
