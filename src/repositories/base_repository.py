"""
Base repository for SQLite operations.

This module provides a light-weight repository base that speaks to the
SQLite database created by `src.database.schema.sql`. It preserves the
API surface expected by existing child repositories (in particular
methods like `_read_csv`, `_write_csv`, `get_all`, `count`, `save`,
`exists`, etc.) but **implements them using SQLite**.

Additionally, it exposes generic CRUD helpers: `find_all`, `find_by_id`,
`insert`, `update`, `delete` and a connection context manager so child
repositories can use direct SQL if needed.
"""

from __future__ import annotations

import shutil
from typing import Optional, List, Dict, Any, Iterator
from pathlib import Path
import pandas as pd
import sqlite3
from contextlib import contextmanager

from src.database.connection import get_connection, get_db_path


class BaseRepository:
    """Base repository backed by SQLite.

    Designed to be backward-compatible with the existing CSV-based
    repositories by providing `_read_csv` and `_write_csv` methods that
    return/accept pandas.DataFrame objects. In addition, it provides
    generic SQL helpers and safer connection handling.
    """

    def __init__(self, filepath: str, schema: List[str], table_name: Optional[str] = None):
        """Initialize repository.

        Args:
            filepath: (legacy) path to CSV file. Kept for compatibility and
                      to derive a sane default `table_name` when not provided.
            schema: list of column names (kept to validate DataFrame columns)
            table_name: optional explicit table name in the SQLite DB
        """
        self.filepath = filepath
        self.schema = list(schema)
        self.table_name = table_name or Path(filepath).stem

    # ------------------ Connection helpers ------------------
    @contextmanager
    def get_conn(self, path: Optional[Path] = None) -> Iterator[sqlite3.Connection]:
        """Context manager yielding a sqlite3.Connection with foreign keys on."""
        conn = get_connection(path)
        try:
            yield conn
        finally:
            conn.close()

    # ------------------ Low-level SQL helpers ------------------
    def _table_exists(self) -> bool:
        with self.get_conn() as conn:
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (self.table_name,))
            return cur.fetchone() is not None

    def find_all(self) -> List[Dict[str, Any]]:
        """Return all rows from the table as list of dicts."""
        if not self._table_exists():
            return []
        with self.get_conn() as conn:
            cur = conn.execute(f'SELECT * FROM "{self.table_name}"')
            rows = [dict(r) for r in cur.fetchall()]
        return rows

    def find_by_id(self, pk_value: Any) -> Optional[Dict[str, Any]]:
        """Find a row by the table primary key.

        The primary key column is guessed by common patterns: 'CODIGO',
        or the first column starting with 'ID_' in schema, otherwise the
        first column in schema.
        """
        pk_col = self._guess_pk_column()
        if not self._table_exists():
            return None
        with self.get_conn() as conn:
            cur = conn.execute(f'SELECT * FROM "{self.table_name}" WHERE "{pk_col}" = ?', (pk_value,))
            row = cur.fetchone()
            return dict(row) if row else None

    def insert(self, data: Dict[str, Any]) -> int:
        """Insert a record into the table. Returns lastrowid or 0 on replace.

        Uses INSERT OR REPLACE so the operation is idempotent for rows with
        primary keys.
        """
        cols = [c for c in self.schema if c in data]
        if not cols:
            raise ValueError('No columns to insert')
        placeholders = ','.join(['?'] * len(cols))
        cols_quoted = ','.join([f'"{c}"' for c in cols])
        values = [self._normalize_value(data.get(c)) for c in cols]
        with self.get_conn() as conn:
            cur = conn.execute(f'INSERT OR REPLACE INTO "{self.table_name}" ({cols_quoted}) VALUES ({placeholders})', values)
            conn.commit()
            return cur.lastrowid or 0

    def update(self, pk_value: Any, updates: Dict[str, Any]) -> bool:
        """Update columns for the row identified by primary key."""
        pk_col = self._guess_pk_column()
        set_cols = [c for c in updates.keys() if c in self.schema]
        if not set_cols:
            raise ValueError('No valid columns to update')
        set_clause = ','.join([f'"{c}" = ?' for c in set_cols])
        values = [self._normalize_value(updates[c]) for c in set_cols] + [pk_value]
        with self.get_conn() as conn:
            cur = conn.execute(f'UPDATE "{self.table_name}" SET {set_clause} WHERE "{pk_col}" = ?', values)
            conn.commit()
            return cur.rowcount > 0

    def delete(self, pk_value: Any) -> bool:
        pk_col = self._guess_pk_column()
        with self.get_conn() as conn:
            cur = conn.execute(f'DELETE FROM "{self.table_name}" WHERE "{pk_col}" = ?', (pk_value,))
            conn.commit()
            return cur.rowcount > 0

    # ------------------ Compatibility methods (CSV API) ------------------
    def _read_csv(self) -> pd.DataFrame:
        """Return the table contents as a pandas DataFrame (column order = schema).

        This method preserves the old CSV-based contract for child
        repositories that expect a DataFrame. Missing tables return an
        empty DataFrame with the expected columns.
        """
        if not self._table_exists():
            return pd.DataFrame(columns=self.schema)
        with self.get_conn() as conn:
            df = pd.read_sql_query(f'SELECT * FROM "{self.table_name}"', conn)
            # Ensure columns exist and order
            for col in self.schema:
                if col not in df.columns:
                    df[col] = ''
            df = df[self.schema]
            # Replace NaN with empty string for backward compatibility
            df = df.fillna('')
            return df

    def _write_csv(self, df: pd.DataFrame) -> None:
        """Persist the whole DataFrame into the table (atomic in a transaction).

        This mirrors previous behaviour where the entire CSV file was
        replaced by a new DataFrame. The function deletes current rows
        and inserts the new ones within a single transaction.
        """
        # Validate schema
        if not all(col in df.columns for col in self.schema):
            raise ValueError(f"DataFrame missing required columns. Expected: {self.schema}")

        # Ensure columns order
        df = df[self.schema]

        if not self._table_exists():
            raise RuntimeError(f"Table '{self.table_name}' does not exist in the DB")

        with self.get_conn() as conn:
            cur = conn.cursor()
            cur.execute('BEGIN')
            try:
                cur.execute(f'DELETE FROM "{self.table_name}"')
                if not df.empty:
                    cols = ','.join([f'"{c}"' for c in self.schema])
                    placeholders = ','.join(['?'] * len(self.schema))
                    rows = []
                    for _, row in df.iterrows():
                        rows.append([self._normalize_value(row.get(c)) for c in self.schema])
                    cur.executemany(f'INSERT INTO "{self.table_name}" ({cols}) VALUES ({placeholders})', rows)
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def get_all(self) -> pd.DataFrame:
        return self._read_csv()

    def count(self) -> int:
        if not self._table_exists():
            return 0
        with self.get_conn() as conn:
            cur = conn.execute(f'SELECT COUNT(*) as c FROM "{self.table_name}"')
            return cur.fetchone()['c']

    def backup(self) -> Optional[str]:
        db_path = get_db_path()
        if not db_path.exists():
            return None
        backup_path = str(db_path) + '.backup'
        shutil.copy2(db_path, backup_path)
        return backup_path

    # ------------------ Utilities ------------------
    def _guess_pk_column(self) -> str:
        # Prefer explicit column names
        if 'CODIGO' in self.schema:
            return 'CODIGO'
        for c in self.schema:
            if c.startswith('ID_'):
                return c
        # fallback to first column
        return self.schema[0]

    @staticmethod
    def _normalize_value(v: Any) -> Any:
        # Convert empty strings to None for DB NULL
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == '':
            return None
        return v

    # Generic CRUD alias names for compatibility
    def find_all_as_df(self) -> pd.DataFrame:
        return self.get_all()

    def find_all_as_list(self) -> List[Dict[str, Any]]:
        return self.find_all()