"""
Base repository with support for both SQLite and PostgreSQL.

Automatically detects database type from environment and uses appropriate connection.
"""

from __future__ import annotations

import os
import shutil
from typing import Optional, List, Dict, Any, Iterator
from pathlib import Path
import pandas as pd
from contextlib import contextmanager

# Determine database type from environment
DB_TYPE = os.getenv('DB_TYPE', 'sqlite').lower()


class BaseRepository:
    """Base repository with multi-database support (SQLite + PostgreSQL)."""

    def __init__(self, filepath: str, schema: List[str], table_name: Optional[str] = None):
        """Initialize repository.

        Args:
            filepath: (legacy) path to CSV file for table name derivation
            schema: list of column names
            table_name: optional explicit table name
        """
        self.filepath = filepath
        self.schema = list(schema)
        self.table_name = table_name or Path(filepath).stem
        self.db_type = DB_TYPE

    # ------------------ Connection Management ------------------
    @contextmanager
    def get_conn(self, path: Optional[Path] = None) -> Iterator:
        """Context manager yielding database connection (SQLite or PostgreSQL)."""
        if self.db_type == 'postgresql':
            from src.database.postgres_connection import get_connection
            with get_connection() as conn:
                yield conn
        else:
            # SQLite
            from src.database.connection import get_connection as sqlite_conn
            conn = sqlite_conn(path)
            try:
                yield conn
            finally:
                conn.close()

    def _get_cursor(self, conn):
        """Get appropriate cursor for database type."""
        if self.db_type == 'postgresql':
            import psycopg2.extras
            return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            # SQLite already has row_factory configured
            return conn.cursor()

    # ------------------ SQL Compatibility Layer ------------------
    def _placeholder(self, n: int = 1) -> str:
        """Get SQL placeholder for parameters."""
        if self.db_type == 'postgresql':
            # PostgreSQL usa %s (psycopg2), NÃO $1, $2, $3
            return ', '.join(['%s'] * n)
        else:
            # SQLite usa ?
            return ', '.join(['?'] * n)

    def _quote_identifier(self, name: str) -> str:
        """Quote identifier appropriately for database."""
        if self.db_type == 'postgresql':
            # PostgreSQL uses double quotes for case-sensitive identifiers
            return f'"{name}"'
        else:
            return f'"{name}"'

    def _returning_clause(self) -> str:
        """Get RETURNING clause for INSERT statements."""
        if self.db_type == 'postgresql':
            return ' RETURNING *'
        else:
            return ''

    # ------------------ Low-level SQL Helpers ------------------
    def _table_exists(self) -> bool:
        """Check if table exists."""
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            
            if self.db_type == 'postgresql':
                cur.execute(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
                    (self.table_name,)
                )
                result = cur.fetchone()
                # PostgreSQL with RealDictCursor returns dict-like object
                if hasattr(result, 'get'):
                    return result.get('exists', False)
                elif hasattr(result, '__getitem__'):
                    try:
                        return result['exists']
                    except (KeyError, TypeError):
                        return result[0] if len(result) > 0 else False
                return bool(result[0]) if result else False
            else:
                cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (self.table_name,)
                )
                return cur.fetchone() is not None

    def find_all(self) -> List[Dict[str, Any]]:
        """Return all rows from the table as list of dicts."""
        if not self._table_exists():
            return []
        
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            cur.execute(f'SELECT * FROM {self._quote_identifier(self.table_name)}')
            rows = cur.fetchall()
            
            if self.db_type == 'postgresql':
                return [dict(r) for r in rows]
            else:
                return [dict(r) for r in rows]

    def find_by_id(self, pk_value: Any) -> Optional[Dict[str, Any]]:
        """Find a row by primary key."""
        pk_col = self._guess_pk_column()
        if not self._table_exists():
            return None
        
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            
            if self.db_type == 'postgresql':
                sql = f'SELECT * FROM {self._quote_identifier(self.table_name)} WHERE {self._quote_identifier(pk_col)} = %s LIMIT 1'
                cur.execute(sql, (pk_value,))
            else:
                sql = f'SELECT * FROM {self._quote_identifier(self.table_name)} WHERE {self._quote_identifier(pk_col)} = ? LIMIT 1'
                cur.execute(sql, (pk_value,))
            
            row = cur.fetchone()
            if row:
                return dict(row) if isinstance(row, dict) else dict(zip([d[0] for d in cur.description], row))
            return None

    def insert(self, data: Dict[str, Any]) -> int:
        """Insert a record. Uses UPSERT for idempotency."""
        cols = [c for c in self.schema if c in data]
        if not cols:
            raise ValueError('No columns to insert')
        
        values = [self._normalize_value(data.get(c)) for c in cols]
        cols_quoted = ','.join([self._quote_identifier(c) for c in cols])
        
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            
            if self.db_type == 'postgresql':
                pk_col = self._guess_pk_column()
                placeholders = ','.join(['%s' for _ in range(len(cols))])
                
                # 🔍 DEBUG - ADICIONE ISSO
                print(f"DEBUG: placeholders = {placeholders}")
                print(f"DEBUG: db_type = {self.db_type}")
                print(f"DEBUG: len(cols) = {len(cols)}")
                
                update_cols = [c for c in cols if c != pk_col]
                update_clause = ','.join([f'{self._quote_identifier(c)} = EXCLUDED.{self._quote_identifier(c)}' for c in update_cols])
                
                sql = f'''
                    INSERT INTO {self._quote_identifier(self.table_name)} ({cols_quoted})
                    VALUES ({placeholders})
                    ON CONFLICT ({self._quote_identifier(pk_col)}) DO UPDATE SET {update_clause}
                    RETURNING *
                '''
                
                # 🔍 DEBUG - ADICIONE ISSO TAMBÉM
                print(f"DEBUG SQL: {sql}")
                
                cur.execute(sql, values)
                conn.commit()
                return 1

    def update(self, pk_value: Any, updates: Dict[str, Any]) -> bool:
        """Update columns for row identified by primary key."""
        pk_col = self._guess_pk_column()
        set_cols = [c for c in updates.keys() if c in self.schema]
        
        if not set_cols:
            raise ValueError('No valid columns to update')
        
        values = [self._normalize_value(updates[c]) for c in set_cols]
        
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            
            if self.db_type == 'postgresql':
                set_clause = ','.join([f'{self._quote_identifier(c)} = %s' for c in set_cols])
                sql = f'UPDATE {self._quote_identifier(self.table_name)} SET {set_clause} WHERE {self._quote_identifier(pk_col)} = %s'
                cur.execute(sql, values + [pk_value])
            else:
                set_clause = ','.join([f'{self._quote_identifier(c)} = ?' for c in set_cols])
                sql = f'UPDATE {self._quote_identifier(self.table_name)} SET {set_clause} WHERE {self._quote_identifier(pk_col)} = ?'
                cur.execute(sql, values + [pk_value])
            
            conn.commit()
            return cur.rowcount > 0

    def delete(self, pk_value: Any) -> bool:
        """Delete row by primary key."""
        pk_col = self._guess_pk_column()
        
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            
            if self.db_type == 'postgresql':
                sql = f'DELETE FROM {self._quote_identifier(self.table_name)} WHERE {self._quote_identifier(pk_col)} = %s'
                cur.execute(sql, (pk_value,))
            else:
                sql = f'DELETE FROM {self._quote_identifier(self.table_name)} WHERE {self._quote_identifier(pk_col)} = ?'
                cur.execute(sql, (pk_value,))
            
            conn.commit()
            return cur.rowcount > 0

    # ------------------ CSV Compatibility Methods ------------------
    def _read_csv(self) -> pd.DataFrame:
        """Return table contents as pandas DataFrame (for backward compatibility)."""
        if not self._table_exists():
            return pd.DataFrame(columns=self.schema)
        
        with self.get_conn() as conn:
            df = pd.read_sql_query(f'SELECT * FROM {self._quote_identifier(self.table_name)}', conn)
            
            # Ensure columns exist and order
            for col in self.schema:
                if col not in df.columns:
                    df[col] = ''
            df = df[self.schema]
            df = df.fillna('')
            return df

    def _write_csv(self, df: pd.DataFrame) -> None:
        """Persist DataFrame to table (atomic transaction)."""
        if not all(col in df.columns for col in self.schema):
            raise ValueError(f"DataFrame missing required columns. Expected: {self.schema}")

        df = df[self.schema]

        if not self._table_exists():
            raise RuntimeError(f"Table '{self.table_name}' does not exist")

        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            
            # Delete all rows
            cur.execute(f'DELETE FROM {self._quote_identifier(self.table_name)}')
            
            if not df.empty:
                cols = ','.join([self._quote_identifier(c) for c in self.schema])
                
                if self.db_type == 'postgresql':
                    placeholders = ','.join([f'%s' for _ in self.schema])
                    sql = f'INSERT INTO {self._quote_identifier(self.table_name)} ({cols}) VALUES ({placeholders})'
                    
                    rows = []
                    for _, row in df.iterrows():
                        rows.append([self._normalize_value(row.get(c)) for c in self.schema])
                    
                    cur.executemany(sql, rows)
                else:
                    placeholders = ','.join(['?' for _ in self.schema])
                    sql = f'INSERT INTO {self._quote_identifier(self.table_name)} ({cols}) VALUES ({placeholders})'
                    
                    rows = []
                    for _, row in df.iterrows():
                        rows.append([self._normalize_value(row.get(c)) for c in self.schema])
                    
                    cur.executemany(sql, rows)
            
            conn.commit()

    def get_all(self) -> pd.DataFrame:
        """Get all rows as DataFrame."""
        return self._read_csv()

    def count(self) -> int:
        """Count total rows."""
        if not self._table_exists():
            return 0
        
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            cur.execute(f'SELECT COUNT(*) as c FROM {self._quote_identifier(self.table_name)}')
            result = cur.fetchone()
            
            if self.db_type == 'postgresql':
                # RealDictCursor returns dict
                if isinstance(result, dict):
                    return result['c']
                return result[0]
            else:
                return result['c']

    def backup(self) -> Optional[str]:
        """Create backup (SQLite only)."""
        if self.db_type != 'sqlite':
            print("⚠️ Backup not implemented for PostgreSQL (use Supabase backups)")
            return None
        
        from src.database.connection import get_db_path
        db_path = get_db_path()
        
        if not db_path.exists():
            return None
        
        backup_path = str(db_path) + '.backup'
        shutil.copy2(db_path, backup_path)
        return backup_path

    # ------------------ Utilities ------------------
    def _guess_pk_column(self) -> str:
        """Guess primary key column name."""
        if 'CODIGO' in self.schema:
            return 'CODIGO'
        for c in self.schema:
            if c.startswith('ID_'):
                return c
        return self.schema[0]

    @staticmethod
    def _normalize_value(v: Any) -> Any:
        """Normalize value for database storage."""
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == '':
            return None
        return v

    def find_all_as_df(self) -> pd.DataFrame:
        """Alias for get_all()."""
        return self.get_all()

    def find_all_as_list(self) -> List[Dict[str, Any]]:
        """Alias for find_all()."""
        return self.find_all()