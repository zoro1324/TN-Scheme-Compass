import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import Base, SessionLocal, engine, get_db
from backend.schemas import (
    ChatHistoryMessage,
    ChatHistoryResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    SessionCreateResponse,
)
from backend.services.chat_service import ChatService
from backend.services.llm_orchestrator import LLMOrchestrator
from backend.services.scheme_loader import load_schemes_if_empty
from backend.services.vector_store import SchemeVectorStore
from backend.models import Scheme


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_store = SchemeVectorStore()
llm = LLMOrchestrator()
chat_service = ChatService(vector_store=vector_store, llm=llm)


@app.on_event("startup")
def startup_event() -> None:
    try:
        Base.metadata.create_all(bind=engine)

        db = SessionLocal()
        try:
            inserted = load_schemes_if_empty(db=db, csv_path=settings.scheme_csv_path)
            if inserted:
                logger.info("Loaded %s schemes into MySQL", inserted)

            schemes = db.query(Scheme).all()
            indexed = vector_store.index_schemes(schemes)
            logger.info("Indexed %s schemes in Chroma", indexed)
        finally:
            db.close()
    except OperationalError as exc:
        logger.error(
            "Database startup failed. Check MYSQL_URL or MYSQL_HOST/MYSQL_USER/MYSQL_PASSWORD in .env and verify database exists. Effective DB URL='%s'.",
            settings.database_url,
        )
        raise RuntimeError("MySQL connection failed during startup.") from exc


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}


@app.post("/api/chat/session", response_model=SessionCreateResponse)
def create_session(db: Session = Depends(get_db)) -> SessionCreateResponse:
    session = chat_service.create_session(db)
    return SessionCreateResponse(session_id=session.id)


@app.post("/api/chat/message", response_model=ChatMessageResponse)
def chat_message(payload: ChatMessageRequest, db: Session = Depends(get_db)) -> ChatMessageResponse:
    try:
        result = chat_service.handle_message(db=db, session_id=payload.session_id, message=payload.message)
        return ChatMessageResponse(
            session_id=payload.session_id,
            reply=result["reply"],
            follow_up_question=result["follow_up_question"],
            schemes=result["schemes"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/chat/history/{session_id}", response_model=ChatHistoryResponse)
def chat_history(session_id: str, db: Session = Depends(get_db)) -> ChatHistoryResponse:
    try:
        result = chat_service.get_history(db=db, session_id=session_id)
        return ChatHistoryResponse(
            session_id=session_id,
            profile=result["profile"],
            messages=[
                ChatHistoryMessage(role=m.role, content=m.content, created_at=m.created_at)
                for m in result["messages"]
            ],
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
