"""
PostgreSQL Connection Pool - Optimized
Gerencia pool de conexões de forma eficiente para reduzir overhead
"""

import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
import threading

DATABASE_URL = os.getenv("DATABASE_URL")

# Pool global com thread-safety
_pool = None
_pool_lock = threading.Lock()


def get_pool():
    """
    Retorna pool de conexões (thread-safe singleton).
    
    Pool configurado para:
    - Min 2 conexões (warm pool)
    - Max 20 conexões (suporta múltiplos requests simultâneos)
    - SSL obrigatório (Supabase)
    """
    global _pool
    
    if _pool is None:
        with _pool_lock:
            # Double-check locking
            if _pool is None:
                _pool = SimpleConnectionPool(
                    minconn=2,  # Mantém 2 conexões warm
                    maxconn=20,  # Aumentado para suportar concorrência
                    dsn=DATABASE_URL,
                    sslmode="require",
                    # Otimizações de performance
                    connect_timeout=5,
                    keepalives=1,
                    keepalives_idle=30,
                    keepalives_interval=10,
                    keepalives_count=5
                )
    return _pool


@contextmanager
def get_connection():
    """
    Context manager para obter conexão do pool.
    
    Uso recomendado:
    ```python
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT ...")
        # conn.commit() é automático se não houver erro
    ```
    
    Yields:
        conexão do pool (já com autocommit=False)
    """
    pool = get_pool()
    conn = pool.getconn()
    
    try:
        conn.autocommit = False
        yield conn
        conn.commit()  # Commit automático se não houver exceção
    except Exception:
        conn.rollback()
        raise
    finally:
        # Sempre devolve conexão ao pool (NÃO fecha)
        pool.putconn(conn)


def close_pool():
    """
    Fecha todas as conexões do pool.
    Deve ser chamado apenas no shutdown da aplicação.
    """
    global _pool
    
    if _pool is not None:
        with _pool_lock:
            if _pool is not None:
                _pool.closeall()
                _pool = None