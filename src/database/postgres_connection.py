"""PostgreSQL connection helper for Supabase.

Provides connection factory and schema initialization for PostgreSQL.
"""
from __future__ import annotations

import os
import psycopg2
import psycopg2.extras
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

DEFAULT_SCHEMA = Path(__file__).resolve().parent / 'schema_postgres.sql'


def get_connection_params() -> dict:
    """Get PostgreSQL connection parameters from environment variables."""
    return {
        'host': os.getenv('SUPABASE_DB_HOST'),
        'port': int(os.getenv('SUPABASE_DB_PORT', 5432)),
        'database': os.getenv('SUPABASE_DB_NAME', 'postgres'),
        'user': os.getenv('SUPABASE_DB_USER'),
        'password': os.getenv('SUPABASE_DB_PASSWORD'),
        'sslmode': os.getenv('SUPABASE_DB_SSLMODE', 'require')
    }


@contextmanager
def get_connection():
    """Context manager yielding a psycopg2 connection with dict cursor."""
    params = get_connection_params()
    
    # Validate required params
    if not all([params['host'], params['user'], params['password']]):
        raise ValueError(
            "Missing required Supabase credentials. "
            "Check SUPABASE_DB_HOST, SUPABASE_DB_USER, SUPABASE_DB_PASSWORD"
        )
    
    conn = psycopg2.connect(**params)
    conn.set_session(autocommit=False)
    
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(schema_path: Optional[str | Path] = None) -> None:
    """Initialize database using the PostgreSQL schema SQL file."""
    schema_file = Path(schema_path) if schema_path else DEFAULT_SCHEMA
    
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    
    print(f"✅ PostgreSQL database initialized successfully")


if __name__ == '__main__':
    print("Initializing PostgreSQL database...")
    init_db()
    print("Done.")