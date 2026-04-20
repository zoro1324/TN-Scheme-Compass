import json
import logging
import re
from typing import Any

from backend.config import settings

logger = logging.getLogger(__name__)


PROFILE_FIELDS = ["age", "income", "gender", "caste", "occupation", "residence_years"]


class LLMOrchestrator:
    def __init__(self):
        self.client = None
        if settings.groq_api_key:
            try:
                from groq import Groq

                self.client = Groq(api_key=settings.groq_api_key)
            except Exception as exc:
                logger.warning("Groq client init failed: %s", exc)

    def _chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 350, temperature: float = 0.3) -> str | None:
        if self.client is None:
            return None

        try:
            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            logger.warning("Groq call failed: %s", exc)
            return None

    def extract_profile_updates(self, message: str, current_profile: dict[str, Any]) -> dict[str, Any]:
        updates = self._extract_profile_regex(message)

        llm_response = self._chat(
            "You extract welfare eligibility profile fields in strict JSON. Return only JSON object.",
            (
                "Given the user message and current profile, extract only fields that are explicitly stated.\n"
                f"Allowed keys: {PROFILE_FIELDS}\n"
                f"Current profile: {json.dumps(current_profile)}\n"
                f"User message: {message}\n"
                "Rules: age/income/residence_years must be numbers. Do not guess values."
            ),
            max_tokens=220,
            temperature=0.0,
        )

        if llm_response:
            try:
                parsed = json.loads(llm_response)
                if isinstance(parsed, dict):
                    for key, value in parsed.items():
                        if key in PROFILE_FIELDS and value not in (None, ""):
                            updates[key] = value
            except json.JSONDecodeError:
                pass

        return updates

    def dynamic_follow_up_question(
        self,
        user_message: str,
        profile: dict[str, Any],
        missing_fields: list[str],
        scheme_context: str,
    ) -> str | None:
        if not missing_fields:
            return None

        llm_response = self._chat(
            "You are an eligibility assistant. Ask exactly one concise follow-up question.",
            (
                "Ask one next-best question based on user intent and missing profile fields.\n"
                f"Missing fields: {missing_fields}\n"
                f"Known profile: {json.dumps(profile)}\n"
                f"Recent user message: {user_message}\n"
                f"Top scheme context: {scheme_context}\n"
                "Constraints: ask only one question, no bullet list, no preamble, under 25 words."
            ),
            max_tokens=80,
            temperature=0.5,
        )
        if llm_response:
            return llm_response

        field = missing_fields[0]
        fallback_questions = {
            "age": "What is your age?",
            "income": "What is your annual household income in rupees?",
            "gender": "What is your gender?",
            "caste": "Which caste category do you belong to (General, OBC, SC, ST)?",
            "occupation": "What is your occupation right now?",
            "residence_years": "How many years have you lived in Tamil Nadu?",
        }
        return fallback_questions.get(field, "Could you share a bit more about your profile for eligibility matching?")

    def compose_reply(
        self,
        user_message: str,
        profile: dict[str, Any],
        scheme_context: str,
        follow_up_question: str | None,
    ) -> str:
        llm_response = self._chat(
            "You are a Tamil Nadu welfare schemes expert assistant.",
            (
                "Respond with useful details from the matched schemes.\n"
                f"User message: {user_message}\n"
                f"User profile: {json.dumps(profile)}\n"
                f"Scheme context: {scheme_context}\n"
                f"Follow-up question to end with (if present): {follow_up_question or 'None'}\n"
                "Rules: Explain concrete scheme details (benefits, eligibility, documents, application process)."
            ),
            max_tokens=420,
            temperature=0.35,
        )
        if llm_response:
            return llm_response

        base = (
            "I found relevant Tamil Nadu schemes based on your message and shared profile. "
            "I have included eligibility, benefits, required documents, and application links below."
        )
        if follow_up_question:
            return f"{base} {follow_up_question}"
        return base

    def _extract_profile_regex(self, message: str) -> dict[str, Any]:
        text = message.lower()
        updates: dict[str, Any] = {}

        age_match = re.search(r"\b(?:age\s*(?:is|:)?\s*)?(\d{1,2})\b", text)
        if age_match:
            age = int(age_match.group(1))
            if 0 < age < 120:
                updates["age"] = age

        income_match = re.search(r"(?:income|salary|earn|annual).*?(\d[\d,]*)", text)
        if income_match:
            updates["income"] = int(income_match.group(1).replace(",", ""))

        residence_match = re.search(r"(?:lived|living|residing|residence).*?(\d{1,2})\s*(?:years|yrs)", text)
        if residence_match:
            updates["residence_years"] = int(residence_match.group(1))

        for gender in ["male", "female", "transgender", "other"]:
            if re.search(rf"\b{gender}\b", text):
                updates["gender"] = gender
                break

        caste_tokens = {"obc": "OBC", "sc": "SC", "st": "ST", "general": "General", "bc": "BC", "mbc": "MBC"}
        for token, normalized in caste_tokens.items():
            if re.search(rf"\b{token}\b", text):
                updates["caste"] = normalized
                break

        occupation_match = re.search(r"(?:i am|i'm|working as|occupation is)\s+([a-z ]{3,40})", text)
        if occupation_match:
            updates["occupation"] = occupation_match.group(1).strip()

        return updates
