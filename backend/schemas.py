from datetime import datetime
from pydantic import BaseModel, Field


class SessionCreateResponse(BaseModel):
    session_id: str


class ChatMessageRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1, max_length=4000)
    language: str = Field(default="en", pattern="^(en|ta)$")


class SchemeCard(BaseModel):
    scheme_id: str
    scheme_name: str
    scheme_level: str | None = None
    administering_body: str | None = None
    target_beneficiaries: str | None = None
    eligibility_criteria: str | None = None
    income_limit: str | None = None
    age_range: str | None = None
    benefit_description: str | None = None
    benefit_amount: str | None = None
    application_process: str | None = None
    required_documents: str | None = None
    application_url: str | None = None
    source_url: str | None = None
    confidence: float | None = None
    match_reason: str | None = None


class ChatMessageResponse(BaseModel):
    session_id: str
    reply: str
    follow_up_question: str | None = None
    schemes: list[SchemeCard] = []


class ChatHistoryMessage(BaseModel):
    role: str
    content: str
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    session_id: str
    profile: dict
    messages: list[ChatHistoryMessage]
