"""SQLite persistence for the Sprint 1 prototype."""

from __future__ import annotations

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "facial_access.db"


class DatabaseConnection(sqlite3.Connection):
    """Confirmar/revertir la transacción y cerrar al salir del contexto."""

    def __exit__(self, exception_type, exception, traceback):
        try:
            return super().__exit__(exception_type, exception, traceback)
        finally:
            self.close()


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, factory=DatabaseConnection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    with get_connection() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE,
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'inactive')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS biometric_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL UNIQUE,
                face_encoding BLOB,
                source_image_path TEXT,
                enrolled_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER,
                device_name TEXT NOT NULL DEFAULT 'Molinete principal',
                result TEXT NOT NULL CHECK (result IN ('allowed', 'denied', 'blocked')),
                detail TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL
            );
            """
        )


def query_all(sql: str, parameters: tuple = ()) -> list[sqlite3.Row]:
    with get_connection() as db:
        return db.execute(sql, parameters).fetchall()


def query_one(sql: str, parameters: tuple = ()) -> sqlite3.Row | None:
    with get_connection() as db:
        return db.execute(sql, parameters).fetchone()

