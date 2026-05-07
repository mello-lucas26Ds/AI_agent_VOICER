# ============================================================
# Interview Assistant — Modelos do Banco de Dados
# Autor: Lucas Melo
# Licença: MIT
#
# Tabelas:
#   - sessions: cada sessão de prática/entrevista
#   - messages: cada frase processada dentro de uma sessão
# ============================================================

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from backend.database import Base


class Session(Base):
    """
    Representa uma sessão de entrevista ou prática.
    Uma sessão agrupa várias mensagens processadas.
    
    Exemplo: "Entrevista Empresa X v — 24/02/2025"
    """
    __tablename__ = "sessions"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(255), nullable=False, default="Sessão sem título")
    started_at  = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at    = Column(DateTime, nullable=True)
    notes       = Column(Text, nullable=True)  # anotações livres sobre a sessão

    # Relacionamento: uma sessão tem muitas mensagens
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Session id={self.id} title='{self.title}'>"


class Message(Base):
    """
    Representa cada frase processada pelo assistente dentro de uma sessão.
    
    Guarda:
    - O que foi transcrito (inglês original)
    - A tradução para português
    - A resposta sugerida em inglês
    - A tradução da resposta sugerida
    - Quando foi processado
    """
    __tablename__ = "messages"

    id                      = Column(Integer, primary_key=True, index=True)
    session_id              = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)

    # Conteúdo processado pela IA
    original_en             = Column(Text, nullable=False)   # transcrição em inglês
    translation_pt          = Column(Text, nullable=False)   # tradução para português
    suggested_response_en   = Column(Text, nullable=False)   # resposta sugerida em inglês
    suggested_response_pt   = Column(Text, nullable=False)   # tradução da resposta sugerida

    # Metadados
    created_at              = Column(DateTime, default=datetime.utcnow, nullable=False)
    processing_time_ms      = Column(Float, nullable=True)   # tempo de resposta da IA em ms

    # Relacionamento inverso
    session = relationship("Session", back_populates="messages")

    def __repr__(self):
        return f"<Message id={self.id} session_id={self.session_id}>"
