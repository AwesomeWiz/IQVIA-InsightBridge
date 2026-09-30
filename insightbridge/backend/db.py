"""Small SQLite access layer for read-only analytics queries."""

from pathlib import Path
import sqlite3


DATABASE_PATH = Path(__file__).resolve().parent / "saas_bi.db"


def execute_read_query(sql: str, parameters: tuple = ()) -> tuple[list[str], list[list]]:
    normalized = " ".join(sql.strip().lower().split())
    forbidden = ("insert ", "update ", "delete ", "drop ", "alter ", "create ", "pragma ", ";")

    if not normalized.startswith("select ") or any(word in normalized for word in forbidden):
        raise ValueError("Only one read-only SELECT statement is allowed.")

    connection = sqlite3.connect(f"file:{DATABASE_PATH.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        cursor = connection.execute(sql, parameters)
        columns = [item[0] for item in cursor.description]
        rows = [list(row) for row in cursor.fetchall()]
        return columns, rows
    finally:
        connection.close()
