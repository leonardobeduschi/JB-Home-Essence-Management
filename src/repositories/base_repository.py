"""
Base Repository - Optimized for Performance

Mudanças principais:
1. Reutiliza conexões do pool em operações múltiplas
2. Elimina uso de Pandas onde possível
3. Queries otimizadas com projeção de colunas
4. Bug fix no placeholder do PostgreSQL
"""

from __future__ import annotations

import os
from typing import Optional, List, Dict, Any
from pathlib import Path
from contextlib import contextmanager

# Determine database type from environment
DB_TYPE = os.getenv('DB_TYPE', 'sqlite').lower()


class BaseRepository:
    """Base repository com suporte a SQLite e PostgreSQL otimizado."""

    def __init__(self, filepath: str, schema: List[str], table_name: Optional[str] = None):
        self.filepath = filepath
        self.schema = list(schema)
        self.table_name = table_name or Path(filepath).stem
        self.db_type = DB_TYPE

    # ------------------ Connection Management ------------------
    
    @contextmanager
    def get_conn(self):
        """
        Context manager otimizado para conexões.
        
        IMPORTANTE: Usa o mesmo pool connection durante todo o bloco.
        Commit/rollback é automático.
        """
        if self.db_type == 'postgresql':
            from src.database.postgres_connection import get_connection
            
            with get_connection() as conn:
                yield conn
        else:
            from src.database.connection import get_connection
            
            conn = get_connection()
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def _get_cursor(self, conn):
        """Retorna cursor apropriado para o tipo de banco."""
        if self.db_type == 'postgresql':
            import psycopg2.extras
            return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            return conn.cursor()

    # ------------------ SQL Compatibility Layer ------------------
    
    def _placeholder(self, n: int = 1) -> str:
        """Retorna placeholders SQL."""
        if self.db_type == 'postgresql':
            return ', '.join(['%s'] * n)
        else:
            return ', '.join(['?'] * n)

    def _quote_identifier(self, name: str) -> str:
        """Quote identifier para case-sensitivity."""
        return f'"{name}"'

    # ------------------ Core CRUD Operations ------------------
    
    def _table_exists(self) -> bool:
        """Verifica se tabela existe."""
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            
            if self.db_type == 'postgresql':
                cur.execute(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
                    (self.table_name,)
                )
                result = cur.fetchone()
                return bool(result['exists'] if hasattr(result, 'get') else result[0])
            else:
                cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (self.table_name,)
                )
                return cur.fetchone() is not None

    def find_all(self, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Retorna todas as linhas (ou colunas específicas).
        
        Args:
            columns: Lista de colunas para projeção. Se None, usa SELECT *.
        """
        if not self._table_exists():
            return []
        
        # Projeção de colunas para reduzir tráfego de rede
        if columns:
            cols = ','.join([self._quote_identifier(c) for c in columns if c in self.schema])
        else:
            cols = '*'
        
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            cur.execute(f'SELECT {cols} FROM {self._quote_identifier(self.table_name)}')
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def find_by_id(self, pk_value: Any) -> Optional[Dict[str, Any]]:
        """Busca por primary key."""
        pk_col = self._guess_pk_column()
        if not self._table_exists():
            return None
        
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            
            placeholder = '%s' if self.db_type == 'postgresql' else '?'
            sql = f'SELECT * FROM {self._quote_identifier(self.table_name)} WHERE {self._quote_identifier(pk_col)} = {placeholder} LIMIT 1'
            cur.execute(sql, (pk_value,))
            
            row = cur.fetchone()
            return dict(row) if row else None

    def insert(self, data: Dict[str, Any]) -> int:
        """
        Insert com UPSERT para idempotência.
        
        BUG FIX: Corrigido placeholders no PostgreSQL.
        """
        cols = [c for c in self.schema if c in data]
        if not cols:
            raise ValueError('No columns to insert')
        
        values = [self._normalize_value(data.get(c)) for c in cols]
        cols_quoted = ','.join([self._quote_identifier(c) for c in cols])
        
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            
            if self.db_type == 'postgresql':
                pk_col = self._guess_pk_column()
                
                # BUG FIX: usar self._placeholder() em vez de recriar string
                placeholders = self._placeholder(len(cols))
                
                update_cols = [c for c in cols if c != pk_col]
                update_clause = ','.join([
                    f'{self._quote_identifier(c)} = EXCLUDED.{self._quote_identifier(c)}'
                    for c in update_cols
                ])
                
                sql = f'''
                    INSERT INTO {self._quote_identifier(self.table_name)} ({cols_quoted})
                    VALUES ({placeholders})
                    ON CONFLICT ({self._quote_identifier(pk_col)}) 
                    DO UPDATE SET {update_clause}
                    RETURNING *
                '''
                cur.execute(sql, values)
                return 1
            else:
                placeholders = self._placeholder(len(cols))
                sql = f'INSERT INTO {self._quote_identifier(self.table_name)} ({cols_quoted}) VALUES ({placeholders})'
                cur.execute(sql, values)
                return cur.lastrowid

    def update(self, pk_value: Any, updates: Dict[str, Any]) -> bool:
        """Atualiza registro por PK."""
        pk_col = self._guess_pk_column()
        set_cols = [c for c in updates.keys() if c in self.schema]
        
        if not set_cols:
            raise ValueError('No valid columns to update')
        
        values = [self._normalize_value(updates[c]) for c in set_cols]
        
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            
            placeholder = '%s' if self.db_type == 'postgresql' else '?'
            set_clause = ','.join([f'{self._quote_identifier(c)} = {placeholder}' for c in set_cols])
            sql = f'UPDATE {self._quote_identifier(self.table_name)} SET {set_clause} WHERE {self._quote_identifier(pk_col)} = {placeholder}'
            
            cur.execute(sql, values + [pk_value])
            return cur.rowcount > 0

    def delete(self, pk_value: Any) -> bool:
        """Deleta registro por PK."""
        pk_col = self._guess_pk_column()
        
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            
            placeholder = '%s' if self.db_type == 'postgresql' else '?'
            sql = f'DELETE FROM {self._quote_identifier(self.table_name)} WHERE {self._quote_identifier(pk_col)} = {placeholder}'
            cur.execute(sql, (pk_value,))
            return cur.rowcount > 0

    def count(self) -> int:
        """Conta total de registros."""
        if not self._table_exists():
            return 0
        
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            cur.execute(f'SELECT COUNT(*) as c FROM {self._quote_identifier(self.table_name)}')
            result = cur.fetchone()
            
            if self.db_type == 'postgresql':
                return int(result['c'] if isinstance(result, dict) else result[0])
            else:
                return int(result['c'])

    # ------------------ Utilities ------------------
    
    def _guess_pk_column(self) -> str:
        """Infere coluna de primary key."""
        if 'CODIGO' in self.schema:
            return 'CODIGO'
        for c in self.schema:
            if c.startswith('ID_'):
                return c
        return self.schema[0]

    @staticmethod
    def _normalize_value(v: Any) -> Any:
        """Normaliza valores para storage."""
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == '':
            return None
        return v

    # ------------------ Legacy Compatibility (DEPRECATED) ------------------
    
    def get_all(self):
        """
        DEPRECATED: Usa find_all() para evitar Pandas.
        
        Mantido apenas para compatibilidade com código legado.
        """
        import pandas as pd
        
        rows = self.find_all()
        if not rows:
            return pd.DataFrame(columns=self.schema)
        
        return pd.DataFrame(rows)