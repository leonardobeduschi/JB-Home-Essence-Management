import csv
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data/database.sqlite3")
BACKUP_DIR = Path("data/backup_migration")

TABLES = [
    "clients",
    "products",
    "sales",
    "sales_items"
]

def backup_table(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    headers = [description[0] for description in cursor.description]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"{table_name}_backup_{timestamp}.csv"

    with backup_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"Backup criado: {backup_file}")

def run_backup():
    BACKUP_DIR.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        for table in TABLES:
            backup_table(conn, table)
    finally:
        conn.close()

if __name__ == "__main__":
    run_backup()
