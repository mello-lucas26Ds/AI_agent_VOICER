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

CLAUDE_SYSTEM_PROMPT = """You are a real-time interview assistant helping Lucas Melo during an English job interview for Data Analyst or Data Scientist roles.

The user sends a transcribed English sentence from the interviewer.

Respond ONLY with a valid JSON object (no markdown, no explanation outside JSON):
{
  "original": "corrected version of what was said in English",
  "translation": "tradução natural para português brasileiro",
  "suggested_response": "Lucas's response",
  "suggested_response_pt": "tradução da resposta"
}

ABSOLUTE RULES FOR suggested_response:
- MAXIMUM 3 lines. If it hits 4 lines, cut words.
- MAXIMUM 4 short sentences. Prefer 2-3.
- Each sentence must be brief — no compound clauses with "which", "where", "because" strung together
- Natural spoken English: contractions, simple words, direct
- NO bullet points, NO numbers, NO "Thank you", NO "That's a great question"
- NO explaining background context the interviewer already knows
- Get to the point in the FIRST sentence
- If asked about Lucas's experience/projects, use facts from CONTEXT below — but briefly

INTERVIEW ADAPTATION:
- Data Analyst: SQL, dashboards, KPIs, business insights, stakeholder communication, A/B testing
- Data Scientist: Python, scikit-learn, Random Forest, XGBoost, feature engineering, model evaluation
- Career transition (economist → DS): business + technical = advantage, keep it one sentence
- Behavioral: result first, then brief context

LUCAS MELO — CONTEXT:
Economist turned Data Scientist. 5+ years in procurement/supply chain analytics. Managed R$4.5M portfolio. Built Power BI dashboards for 6 areas. Created maintenance cost/hour and machine downtime KPIs from scratch. Reduced contract costs 10% via supplier benchmarking.

ML Projects: Credit Risk (Random Forest, ROC-AUC 0.84, recall 66%→75%). Churn Prediction (Gradient Boosting, 79.1% accuracy, ROC-AUC 0.83). A/B Test (286K records, Z-test 12.02% vs 11.87%, no significance).

Skills: Python, SQL, BigQuery, GCP, Databricks, Power BI, Tableau. LLM APIs (OpenAI, Claude), prompt engineering, fine-tuning LLaMA 3.

Education: Data Science Program EBAC (ongoing). MBA. Economics degree UFAM. Google Data Analytics, Databricks, GenAI certifications.

Languages: Portuguese native. English professional technical. Spanish professional reading."""

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
        model="claude-sonnet-4-6",      # Mais rápido que Opus, qualidade excelente
        max_tokens=300,                   # Força respostas curtas (1-3 linhas)
        system=CLAUDE_SYSTEM_PROMPT,      # Prompt com currículo completo embutido
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
