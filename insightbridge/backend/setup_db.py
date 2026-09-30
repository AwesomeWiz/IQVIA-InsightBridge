"""Create the SQLite database from the supplied MySQL SQL files."""

from pathlib import Path
import re
import sqlite3


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = Path(__file__).resolve().parent / "saas_bi.db"
SCHEMA_PATH = PROJECT_DIR / "schema.sql"
SEED_PATH = PROJECT_DIR / "seed_data.sql"


def make_sqlite_compatible(sql: str) -> str:
    """Apply only the syntax changes needed for SQLite."""
    sql = re.sub(r"^CREATE DATABASE.*?;\s*$", "", sql, flags=re.MULTILINE | re.IGNORECASE)
    sql = re.sub(r"^USE\s+\w+\s*;\s*$", "", sql, flags=re.MULTILINE | re.IGNORECASE)
    sql = re.sub(r"ENUM\([^)]*\)", "TEXT", sql, flags=re.IGNORECASE)
    sql = re.sub(
        r"\s+ON UPDATE CURRENT_TIMESTAMP",
        "",
        sql,
        flags=re.IGNORECASE,
    )
    return sql


def setup_database(database_path: Path = DATABASE_PATH) -> None:
    schema_sql = make_sqlite_compatible(SCHEMA_PATH.read_text(encoding="utf-8"))
    seed_sql = make_sqlite_compatible(SEED_PATH.read_text(encoding="utf-8"))

    database_path.parent.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        database_path.unlink()

    connection = sqlite3.connect(database_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(schema_sql)
        connection.executescript(seed_sql)
        connection.commit()

        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Foreign-key violations found: {violations}")
    finally:
        connection.close()

    print(f"Created and seeded {database_path}")


if __name__ == "__main__":
    setup_database()
