# ============================================================
# Interview Assistant — Rotas de Mensagens com Whisper
# Autor: Lucas Melo
# Licença: MIT
#
# Endpoints:
#   POST /messages/process-audio  → recebe áudio, transcreve com Whisper,
#                                   traduz com Claude, salva no PostgreSQL
#   POST /messages/process        → recebe texto direto (fallback/testes)
#   GET  /messages/{session_id}   → lista mensagens de uma sessão
# ============================================================

import time
import os
import json
import re
import tempfile
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
import anthropic
from openai import OpenAI
from dotenv import load_dotenv

from backend.database import get_db
from backend.models import Message, Session

load_dotenv()

router = APIRouter(prefix="/messages", tags=["messages"])

anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
openai_client    = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CLAUDE_SYSTEM_PROMPT = """You are an interview assistant helping a Brazilian Portuguese speaker during an English job interview.

The user will send you a transcribed English sentence they just heard.

Respond ONLY with a valid JSON object in this exact format (no markdown, no explanation outside the JSON):
{
  "original": "the corrected/cleaned up version of what was said in English",
  "translation": "tradução completa e natural para o português brasileiro",
  "suggested_response": "A natural, professional English response the user could say",
  "suggested_response_pt": "Tradução da resposta sugerida em português brasileiro"
}

Keep the suggested response concise (2-4 sentences), professional, and appropriate for a data analyst job interview context at a tech startup."""


class ProcessTextRequest(BaseModel):
    session_id: int
    transcript: str

class MessageOut(BaseModel):
    id: int
    session_id: int
    original_en: str
    translation_pt: str
    suggested_response_en: str
    suggested_response_pt: str
    processing_time_ms: Optional[float]
    whisper_transcript: Optional[str] = None

    class Config:
        from_attributes = True


def transcribe_with_whisper(audio_bytes: bytes, filename: str) -> str:
    suffix = ".webm" if "webm" in filename else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as audio_file:
            response = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en",
                response_format="text",
            )
        return response.strip()
    finally:
        os.unlink(tmp_path)


def process_with_claude(transcript: str) -> dict:
    response = anthropic_client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1000,
        system=CLAUDE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": transcript}]
    )
    raw = response.content[0].text
    clean = re.sub(r"```json|```", "", raw).strip()
    return json.loads(clean)


def save_message(db, session_id, parsed, whisper_raw, elapsed_ms):
    message = Message(
        session_id            = session_id,
        original_en           = parsed.get("original", whisper_raw),
        translation_pt        = parsed.get("translation", ""),
        suggested_response_en = parsed.get("suggested_response", ""),
        suggested_response_pt = parsed.get("suggested_response_pt", ""),
        processing_time_ms    = elapsed_ms,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.post("/process-audio", response_model=MessageOut, status_code=201)
async def process_audio(
    session_id: int = Form(...),
    audio: UploadFile = File(...),
    db: DBSession = Depends(get_db),
):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Arquivo de áudio vazio.")

    start = time.time()

    try:
        whisper_transcript = transcribe_with_whisper(audio_bytes, audio.filename or "audio.webm")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro no Whisper: {str(e)}")

    if not whisper_transcript.strip():
        raise HTTPException(status_code=422, detail="Whisper não detectou fala no áudio.")

    try:
        parsed = process_with_claude(whisper_transcript)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Resposta do Claude em formato inválido.")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro no Claude: {str(e)}")

    elapsed_ms = round((time.time() - start) * 1000, 2)
    message = save_message(db, session_id, parsed, whisper_transcript, elapsed_ms)

    return {**message.__dict__, "whisper_transcript": whisper_transcript}


@router.post("/process", response_model=MessageOut, status_code=201)
def process_text(payload: ProcessTextRequest, db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == payload.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")

    if not payload.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcrição vazia.")

    start = time.time()
    try:
        parsed = process_with_claude(payload.transcript)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro no Claude: {str(e)}")

    elapsed_ms = round((time.time() - start) * 1000, 2)
    message = save_message(db, payload.session_id, parsed, payload.transcript, elapsed_ms)
    return {**message.__dict__, "whisper_transcript": payload.transcript}


@router.get("/{session_id}", response_model=list[MessageOut])
def list_messages(session_id: int, db: DBSession = Depends(get_db)):
    messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return [{**m.__dict__, "whisper_transcript": None} for m in messages]
