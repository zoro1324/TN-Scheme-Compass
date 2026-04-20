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
        # Deterministic single-question flow to avoid multi-part or repetitive prompts.
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
        can_recommend: bool,
        missing_fields: list[str],
        scheme_count: int,
    ) -> str:
        if not can_recommend:
            llm_response = self._chat(
                "You are a Tamil Nadu welfare eligibility intake assistant.",
                (
                    "You must collect required user details before recommending schemes.\n"
                    f"User message: {user_message}\n"
                    f"Known profile: {json.dumps(profile)}\n"
                    f"Missing fields: {missing_fields}\n"
                    f"Follow-up question to end with: {follow_up_question or 'None'}\n"
                    "Rules: Do not list or suggest any scheme yet.\n"
                    "Briefly explain you need profile details to find the best eligible match.\n"
                    "Ask only one follow-up question at the end.\n"
                    "No bullet list. Keep it concise and friendly."
                ),
                max_tokens=170,
                temperature=0.3,
            )
            if llm_response:
                return llm_response

            if follow_up_question:
                return (
                    "I can find the best scheme matches for you, but I need a few profile details first to avoid blind recommendations. "
                    f"{follow_up_question}"
                )

            return "I can match you accurately once I have your basic eligibility details."

        if scheme_count == 0:
            return (
                "I could not find a confident exact match from the currently indexed schemes for your profile. "
                "Try asking for student scholarships, education assistance, or skill-development schemes in Tamil Nadu, "
                "and I can refine the search further."
            )

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

        age_match = re.search(
            r"\bage\s*(?:is|:)?\s*(\d{1,2})\b|\b(?:i am|i'm)\s*(\d{1,2})\b|\b(\d{1,2})\s*(?:year old|years old|yr old|yrs old|yo)\b",
            text,
        )
        if age_match:
            age_text = age_match.group(1) or age_match.group(2) or age_match.group(3)
            age = int(age_text)
            if 0 < age < 120:
                updates["age"] = age

        income_match = re.search(
            r"(?:income|salary|earn(?:ing)?s?|annual|family income|father'?s income|mother'?s income).*?(\d[\d,]*(?:\.\d+)?)\s*(k|thousand|lakh|lakhs|crore|crores)?",
            text,
        )
        if income_match:
            amount = float(income_match.group(1).replace(",", ""))
            unit = (income_match.group(2) or "").strip()
            multiplier = 1
            if unit in {"k", "thousand"}:
                multiplier = 1_000
            elif unit in {"lakh", "lakhs"}:
                multiplier = 100_000
            elif unit in {"crore", "crores"}:
                multiplier = 10_000_000

            updates["income"] = int(amount * multiplier)

        residence_match = re.search(r"(?:lived|living|residing|residence).*?(\d{1,2})\s*(?:years|yrs)", text)
        if residence_match:
            updates["residence_years"] = int(residence_match.group(1))
        elif re.search(r"\b(?:native|origin|from tamil nadu|born in tamil nadu)\b", text):
            # Treat explicit Tamil Nadu nativity as long-term residence for ranking hints.
            updates["residence_years"] = 99

        for gender in ["male", "female", "transgender", "other"]:
            if re.search(rf"\b{gender}\b", text):
                updates["gender"] = gender
                break

        caste_tokens = {"obc": "OBC", "sc": "SC", "st": "ST", "general": "General", "bc": "BC", "mbc": "MBC"}
        for token, normalized in caste_tokens.items():
            if re.search(rf"\b{token}\b", text):
                updates["caste"] = normalized
                break

        occupation_match = re.search(r"(?:i am|i'm|working as|occupation is)\s+([^\n\.,;]{2,60})", text)
        if occupation_match:
            raw = occupation_match.group(1).strip()
            raw = re.split(r"\band\b|\bmy\b|\bage\b|\bincome\b", raw)[0].strip()
            raw = re.sub(r"^(a|an)\s+", "", raw).strip()
            if raw:
                updates["occupation"] = raw

        return updates
