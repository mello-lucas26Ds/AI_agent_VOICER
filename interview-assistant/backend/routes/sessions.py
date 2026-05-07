# ============================================================
# Interview Assistant — Rotas de Sessões
# Autor: Lucas Melo
# Licença: MIT
#
# Endpoints:
#   POST   /sessions/           → cria nova sessão
#   GET    /sessions/           → lista todas as sessões
#   GET    /sessions/{id}       → detalha uma sessão com mensagens
#   PATCH  /sessions/{id}       → atualiza título ou encerra sessão
#   DELETE /sessions/{id}       → deleta sessão e todas as mensagens
# ============================================================

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel

from backend.database import get_db
from backend.models import Session, Message

router = APIRouter(prefix="/sessions", tags=["sessions"])


# ── Schemas Pydantic ──────────────────────────────────────────

class SessionCreate(BaseModel):
    title: str = "Sessão sem título"
    notes: Optional[str] = None

class SessionUpdate(BaseModel):
    title: Optional[str] = None
    notes: Optional[str] = None
    ended_at: Optional[datetime] = None

class MessageOut(BaseModel):
    id: int
    original_en: str
    translation_pt: str
    suggested_response_en: str
    suggested_response_pt: str
    created_at: datetime
    processing_time_ms: Optional[float]

    class Config:
        from_attributes = True

class SessionOut(BaseModel):
    id: int
    title: str
    started_at: datetime
    ended_at: Optional[datetime]
    notes: Optional[str]
    message_count: int = 0

    class Config:
        from_attributes = True

class SessionDetail(SessionOut):
    messages: List[MessageOut] = []


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/", response_model=SessionOut, status_code=201)
def create_session(payload: SessionCreate, db: DBSession = Depends(get_db)):
    """Cria uma nova sessão de prática ou entrevista."""
    session = Session(title=payload.title, notes=payload.notes)
    db.add(session)
    db.commit()
    db.refresh(session)
    return {**session.__dict__, "message_count": 0}


@router.get("/", response_model=List[SessionOut])
def list_sessions(db: DBSession = Depends(get_db)):
    """Lista todas as sessões, da mais recente para a mais antiga."""
    sessions = db.query(Session).order_by(Session.started_at.desc()).all()
    result = []
    for s in sessions:
        count = db.query(Message).filter(Message.session_id == s.id).count()
        result.append({**s.__dict__, "message_count": count})
    return result


@router.get("/{session_id}", response_model=SessionDetail)
def get_session(session_id: int, db: DBSession = Depends(get_db)):
    """Retorna uma sessão com todas as suas mensagens."""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    count = len(session.messages)
    return {**session.__dict__, "message_count": count, "messages": session.messages}


@router.patch("/{session_id}", response_model=SessionOut)
def update_session(session_id: int, payload: SessionUpdate, db: DBSession = Depends(get_db)):
    """Atualiza título, notas ou encerra uma sessão."""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    if payload.title is not None:
        session.title = payload.title
    if payload.notes is not None:
        session.notes = payload.notes
    if payload.ended_at is not None:
        session.ended_at = payload.ended_at
    db.commit()
    db.refresh(session)
    count = db.query(Message).filter(Message.session_id == session_id).count()
    return {**session.__dict__, "message_count": count}


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: int, db: DBSession = Depends(get_db)):
    """Deleta uma sessão e todas as mensagens associadas."""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    db.delete(session)
    db.commit()
