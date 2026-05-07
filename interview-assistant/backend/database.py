# ============================================================
# Interview Assistant — Conexão com PostgreSQL
# Autor: Lucas Melo
# Licença: MIT
# ============================================================

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Monta a URL de conexão com o PostgreSQL
DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:"
    f"{os.getenv('POSTGRES_PORT')}/"
    f"{os.getenv('POSTGRES_DB')}"
)

# Cria o engine de conexão
engine = create_engine(DATABASE_URL, echo=False)

# Fábrica de sessões para uso nas rotas
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os models ORM
Base = declarative_base()


def get_db():
    """
    Dependency injection para o FastAPI.
    Garante que a sessão é fechada após cada request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Cria todas as tabelas no banco se ainda não existirem.
    Chamado na inicialização do servidor.
    """
    from backend.models import Session, Message  # noqa: F401 — importa para registrar os models
    Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados PostgreSQL conectado e tabelas criadas.")


def check_connection():
    """
    Testa a conexão com o banco na inicialização.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Conexão com PostgreSQL estabelecida com sucesso.")
        return True
    except Exception as e:
        print(f"❌ Erro ao conectar ao PostgreSQL: {e}")
        return False
