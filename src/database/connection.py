"""SQLite connection helper for JB Home Essence.

Provides a reusable connection factory and an initialization helper
that runs the `schema.sql` file to create the base tables.

This module intentionally uses only the standard library so it does
not introduce new runtime dependencies.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional

# Default DB path (can be overridden with SQLITE_DB env var)
DEFAULT_DB = Path(os.getenv('SQLITE_DB', 'data/database.sqlite3'))
DEFAULT_SCHEMA = Path(__file__).resolve().parent / 'schema.sql'


def get_db_path(path: Optional[str | Path] = None) -> Path:
    """Return the Path to the SQLite database file to use."""
    return Path(path) if path else DEFAULT_DB


def get_connection(path: Optional[str | Path] = None) -> sqlite3.Connection:
    """Return a new sqlite3.Connection with sensible defaults:

    - row_factory set to sqlite3.Row for dict-like access
    - foreign keys enforcement enabled (PRAGMA foreign_keys = ON)

    The caller **must** close the connection when done.
    """
    db_path = get_db_path(path)
    # Ensure parent dir exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path), detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row

    # Enforce foreign keys
    conn.execute('PRAGMA foreign_keys = ON')

    return conn


def init_db(schema_path: Optional[str | Path] = None, db_path: Optional[str | Path] = None) -> None:
    """Initialize (or re-initialize) the database using the schema SQL file.

    If the DB file does not exist it will be created. The schema SQL is executed
    in a single transaction.
    """
    db_path = get_db_path(db_path)
    schema_file = Path(schema_path) if schema_path else DEFAULT_SCHEMA

    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    # Ensure parent dir exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with get_connection(db_path) as conn:
        with open(schema_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        conn.executescript(sql)
        conn.commit()


if __name__ == '__main__':
    # Quick CLI helper for local development
    print(f"Initializing database at: {get_db_path()} using schema {DEFAULT_SCHEMA}")
    init_db()
    print("Done.")