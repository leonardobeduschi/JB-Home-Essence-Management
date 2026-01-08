"""Migration script: import CSV data from data/ into SQLite DB.

- Reads data/products.csv, data/clients.csv, data/sales.csv, data/sales_items.csv
- Uses `src.database.connection.init_db` to ensure schema exists
- Inserts rows handling empty fields, currency strings and dates
- Records migration in `migrations` table to avoid re-running
- Logs progress to console

Usage:
    python migrate_from_csv.py [--db PATH] [--force]

"""
from __future__ import annotations

import argparse
import csv
import datetime
import logging
import re
import sys
from pathlib import Path
from typing import Optional

from src.database.connection import get_connection, init_db

MIGRATION_NAME = 'csv_to_sqlite_v1'
DATA_DIR = Path('data')
DEFAULT_DB = None  # use default from connection module

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger('migrate')


num_re = re.compile(r'-?\d+[\.,]?\d*')


def extract_number(s: Optional[str]) -> Optional[float]:
    """Extract a numeric value from a string, return float or None."""
    if s is None:
        return None
    s = s.strip()
    if s == '':
        return None
    m = num_re.search(s)
    if not m:
        return None
    token = m.group(0).replace('.', '').replace(',', '.') if token_needs_swap(m.group(0)) else m.group(0).replace(',', '.')
    try:
        return float(token)
    except Exception:
        try:
            return float(m.group(0).replace(',', '.'))
        except Exception:
            return None


def token_needs_swap(token: str) -> bool:
    """Heuristic: if token contains both '.' and ',', assume '.' is thousand sep and ',' decimal -> swap.
    Example: '1.234,56' -> become '1234.56'
    """
    return '.' in token and ',' in token and token.index('.') < token.index(',')


def parse_int(s: Optional[str]) -> Optional[int]:
    if s is None:
        return None
    s = s.strip()
    if s == '':
        return None
    try:
        # Sometimes floats are present for integer-looking fields
        return int(float(s.replace(',', '.')))
    except Exception:
        # fallback to extract digits
        m = re.search(r'-?\d+', s)
        if m:
            return int(m.group(0))
        return None


def parse_currency(s: Optional[str]) -> Optional[float]:
    return extract_number(s)


def parse_date(s: Optional[str]) -> Optional[str]:
    """Parse date strings like dd/mm/YYYY and return ISO date YYYY-MM-DD, or original if parsing fails.
    If input empty -> None
    """
    if s is None:
        return None
    s = s.strip()
    if s == '':
        return None
    for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
        try:
            d = datetime.datetime.strptime(s, fmt).date()
            return d.isoformat()
        except Exception:
            continue
    # Could not parse; return original trimmed string to preserve data
    return s


def insert_clients(conn, csv_path: Path) -> int:
    logger.info('Importing clients from %s', csv_path)
    inserted = 0
    with csv_path.open(encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    with conn:
        cur = conn.cursor()
        for r in rows:
            # Keep column names exactly
            values = (
                r.get('ID_CLIENTE') or None,
                r.get('CLIENTE') or None,
                r.get('VENDEDOR') or None,
                r.get('TIPO') or None,
                r.get('IDADE') or None,
                r.get('GENERO') or None,
                r.get('PROFISSAO') or None,
                r.get('CPF_CNPJ') or None,
                r.get('TELEFONE') or None,
                r.get('ENDERECO') or None,
            )
            cur.execute(
                'INSERT OR REPLACE INTO clients (ID_CLIENTE, CLIENTE, VENDEDOR, TIPO, IDADE, GENERO, PROFISSAO, CPF_CNPJ, TELEFONE, ENDERECO) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                values
            )
            inserted += 1
    logger.info('Inserted %d clients', inserted)
    return inserted


def insert_products(conn, csv_path: Path) -> int:
    logger.info('Importing products from %s', csv_path)
    inserted = 0
    with csv_path.open(encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    with conn:
        cur = conn.cursor()
        for r in rows:
            codigo = r.get('CODIGO') or None
            produto = r.get('PRODUTO') or None
            categoria = r.get('CATEGORIA') or None
            custo = parse_currency(r.get('CUSTO'))
            valor = parse_currency(r.get('VALOR'))
            estoque = parse_int(r.get('ESTOQUE'))

            cur.execute(
                'INSERT OR REPLACE INTO products (CODIGO, PRODUTO, CATEGORIA, CUSTO, VALOR, ESTOQUE) VALUES (?, ?, ?, ?, ?, ?)',
                (codigo, produto, categoria, custo, valor, estoque)
            )
            inserted += 1
    logger.info('Inserted %d products', inserted)
    return inserted


def insert_sales(conn, csv_path: Path) -> int:
    logger.info('Importing sales from %s', csv_path)
    inserted = 0
    with csv_path.open(encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    with conn:
        cur = conn.cursor()
        for r in rows:
            id_venda = r.get('ID_VENDA') or None
            id_cliente = r.get('ID_CLIENTE') or None
            cliente = r.get('CLIENTE') or None
            meio = r.get('MEIO') or None
            data = parse_date(r.get('DATA'))
            valor_total = parse_currency(r.get('VALOR_TOTAL_VENDA'))

            cur.execute(
                'INSERT OR REPLACE INTO sales (ID_VENDA, ID_CLIENTE, CLIENTE, MEIO, DATA, VALOR_TOTAL_VENDA) VALUES (?, ?, ?, ?, ?, ?)',
                (id_venda, id_cliente, cliente, meio, data, valor_total)
            )
            inserted += 1
    logger.info('Inserted %d sales', inserted)
    return inserted


def insert_sales_items(conn, csv_path: Path) -> int:
    logger.info('Importing sales_items from %s', csv_path)
    inserted = 0
    with csv_path.open(encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    with conn:
        cur = conn.cursor()
        for r in rows:
            id_venda = r.get('ID_VENDA') or None
            produto = r.get('PRODUTO') or None
            categoria = r.get('CATEGORIA') or None
            codigo = r.get('CODIGO') or None
            quantidade = parse_int(r.get('QUANTIDADE'))
            preco_unit = parse_currency(r.get('PRECO_UNIT'))
            preco_total = parse_currency(r.get('PRECO_TOTAL'))

            cur.execute(
                'INSERT INTO sales_items (ID_VENDA, PRODUTO, CATEGORIA, CODIGO, QUANTIDADE, PRECO_UNIT, PRECO_TOTAL) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (id_venda, produto, categoria, codigo, quantidade, preco_unit, preco_total)
            )
            inserted += 1
    logger.info('Inserted %d sales_items', inserted)
    return inserted


def ensure_migrations_table(conn) -> None:
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS migrations (name TEXT PRIMARY KEY, applied_at TEXT)')
    conn.commit()


def migration_already_applied(conn) -> bool:
    cur = conn.cursor()
    cur.execute('SELECT 1 FROM migrations WHERE name = ?', (MIGRATION_NAME,))
    return cur.fetchone() is not None


def record_migration(conn) -> None:
    cur = conn.cursor()
    cur.execute('INSERT OR REPLACE INTO migrations (name, applied_at) VALUES (?, ?)', (MIGRATION_NAME, datetime.datetime.utcnow().isoformat()))
    conn.commit()


def main(db_path: Optional[Path], force: bool = False) -> int:
    if db_path:
        logger.info('Using DB at %s', db_path)
    else:
        logger.info('Using default DB (connection module)')

    # Ensure schema exists
    init_db(db_path)

    conn = get_connection(db_path)

    try:
        ensure_migrations_table(conn)
        if migration_already_applied(conn) and not force:
            logger.warning('Migration "%s" already applied. Use --force to re-run.', MIGRATION_NAME)
            return 0

        # Import order: clients, products, sales, sales_items
        clients_csv = DATA_DIR / 'clients.csv'
        products_csv = DATA_DIR / 'products.csv'
        sales_csv = DATA_DIR / 'sales.csv'
        sales_items_csv = DATA_DIR / 'sales_items.csv'

        if not (clients_csv.exists() and products_csv.exists() and sales_csv.exists() and sales_items_csv.exists()):
            logger.error('One or more CSV files are missing in data/. Aborting.')
            return 2

        inserted_clients = insert_clients(conn, clients_csv)
        inserted_products = insert_products(conn, products_csv)
        inserted_sales = insert_sales(conn, sales_csv)
        inserted_sales_items = insert_sales_items(conn, sales_items_csv)

        record_migration(conn)

        logger.info('Migration completed: clients=%d products=%d sales=%d sales_items=%d', inserted_clients, inserted_products, inserted_sales, inserted_sales_items)
        return 0
    finally:
        conn.close()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--db', help='Path to sqlite DB file (overrides default)', default=None)
    p.add_argument('--force', help='Force re-run the migration (will overwrite)', action='store_true')
    args = p.parse_args()

    sys.exit(main(Path(args.db) if args.db else None, force=args.force))
