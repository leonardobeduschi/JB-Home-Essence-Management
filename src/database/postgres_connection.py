"""PostgreSQL connection helper for Supabase using DATABASE_URL.

Fornece um context manager simples para conexões seguras com Supabase.
Recomendado para produção (ex: Hugging Face Spaces).
"""
import os
import psycopg2
from contextlib import contextmanager

# Pega a URL completa do ambiente (obrigatória)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL não definida no ambiente. "
        "Defina-a nas variáveis de ambiente do Hugging Face Spaces "
        "(ou onde estiver rodando). Exemplo: postgresql://postgres.[seu-ref]:sua-senha@..."
    )


@contextmanager
def get_connection():
    """Context manager que entrega uma conexão psycopg2 usando DATABASE_URL."""
    # sslmode=require é forçado aqui para garantir segurança (Supabase exige SSL)
    conn = psycopg2.connect(
        DATABASE_URL,
        sslmode="require"
    )
    conn.set_session(autocommit=False)  # Mantém o comportamento transacional

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()