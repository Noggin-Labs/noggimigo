"""Small HTTP adapter for the deterministic Noggimigo tutoring engine.

Run with: uvicorn noggimigo.api:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import os
from collections import OrderedDict
from threading import RLock
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from .curriculum import CURRICULUM
from .session import NoggimigoSession

MAX_SESSIONS = 250


class CreateSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lesson_id: str = Field(min_length=1, max_length=80)


class SubmitAnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str = Field(min_length=1, max_length=200)


def create_app() -> FastAPI:
    """Create an API app with isolated, process-local tutoring sessions."""
    app = FastAPI(
        title="Noggimigo API",
        version="0.1.0",
        description=(
            "HTTP adapter for Noggimigo's deterministic tutoring engine. "
            "Sessions are temporary and stored in this process only."
        ),
    )
    allowed_origins = [
        origin.strip()
        for origin in os.getenv("NOGGIMIGO_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    sessions: OrderedDict[str, NoggimigoSession] = OrderedDict()
    lock = RLock()

    def get_session(session_id: str) -> NoggimigoSession:
        try:
            parsed_id = str(UUID(session_id))
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Tutoring session not found.") from exc
        with lock:
            session = sessions.get(parsed_id)
            if session is None:
                raise HTTPException(status_code=404, detail="Tutoring session not found.")
            sessions.move_to_end(parsed_id)
            return session

    def serialize(session_id: str, session: NoggimigoSession, result: dict | None = None) -> dict:
        return {
            "session_id": session_id,
            "lesson_id": session.lesson_id,
            "lesson": {
                "title": session.lesson["title"],
                "subject": session.lesson["subject"],
                "topic": session.lesson["topic"],
                "objective": session.lesson["objective"],
            },
            "prompt": session.current_prompt(),
            "model_enabled": session.model is not None,
            **({"result": result} if result is not None else {}),
        }

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "noggimigo"}

    @app.post("/api/sessions", status_code=201)
    def create_session(payload: CreateSessionRequest) -> dict:
        if payload.lesson_id not in CURRICULUM:
            supported = ", ".join(CURRICULUM)
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported lesson. Available lessons: {supported}.",
            )
        session_id = str(uuid4())
        session = NoggimigoSession(payload.lesson_id, history_limit=0)
        with lock:
            sessions[session_id] = session
            while len(sessions) > MAX_SESSIONS:
                sessions.popitem(last=False)
        return serialize(session_id, session)

    @app.get("/api/sessions/{session_id}")
    def read_session(session_id: str) -> dict:
        session = get_session(session_id)
        with lock:
            return serialize(str(UUID(session_id)), session)

    @app.post("/api/sessions/{session_id}/hint")
    def request_hint(session_id: str) -> dict:
        session = get_session(session_id)
        with lock:
            result = session.request_hint()
            return serialize(str(UUID(session_id)), session, result)

    @app.post("/api/sessions/{session_id}/answer")
    def submit_answer(session_id: str, payload: SubmitAnswerRequest) -> dict:
        answer = payload.answer.strip()
        if not answer:
            raise HTTPException(status_code=422, detail="Answer must not be blank.")
        session = get_session(session_id)
        with lock:
            result = session.submit(answer)
            return serialize(str(UUID(session_id)), session, result)

    return app


app = create_app()
