# ============================================================
# Interview Assistant — Servidor Principal
# Autor: Lucas Melo
# Licença: MIT
#
# Para rodar:
#   uvicorn backend.main:app --reload
#
# Documentação automática:
#   http://localhost:8000/docs
# ============================================================

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from backend.database import init_db, check_connection
from backend.routes import sessions, messages

load_dotenv()

# ── Inicialização do App ──────────────────────────────────────

app = FastAPI(
    title="Interview Assistant API",
    description="Agente Assistente para entrevistas em qualquer idioma — by Lucas Melo",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS — permite que o frontend acesse o backend ───────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # em produção, substituir pelo domínio real
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rotas da API ─────────────────────────────────────────────

app.include_router(sessions.router, prefix="/api")
app.include_router(messages.router, prefix="/api")

# ── Servir o frontend estático ────────────────────────────────

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

# ── Eventos de inicialização ──────────────────────────────────

@app.on_event("startup")
def startup():
    print("🚀 Interview Assistant iniciando...")
    if check_connection():
        init_db()
    else:
        print("⚠️  Verifique as credenciais do PostgreSQL no arquivo .env")


@app.on_event("shutdown")
def shutdown():
    print("👋 Interview Assistant encerrado.")


# ── Health check ──────────────────────────────────────────────

@app.get("/api/health", tags=["health"])
def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "author": "Lucas Melo",
    }
