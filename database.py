"""Acceso a SQLite: este módulo concentra las consultas del panel."""

from __future__ import annotations

import sqlite3
from datetime import datetime
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


def get_connection(path: str | Path = DATABASE_PATH) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, factory=DatabaseConnection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(path: str | Path = DATABASE_PATH) -> None:
    with get_connection(path) as db:
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
                encoding_model TEXT,
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
        columns = {row[1] for row in db.execute("PRAGMA table_info(biometric_profiles)")}
        if "encoding_model" not in columns:
            db.execute("ALTER TABLE biometric_profiles ADD COLUMN encoding_model TEXT")


ENCODING_MODEL = "face_recognition_128"


class EmployeeRepository:
    """Operaciones de empleados y auditoría; cada conexión se cierra al terminar."""

    def __init__(self, path: str | Path = DATABASE_PATH):
        self.path = Path(path)
        initialize_database(self.path)

    def get_employee(self, employee_id):
        with get_connection(self.path) as db:
            return db.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()

    def list_employees(self):
        with get_connection(self.path) as db:
            return db.execute(
                """SELECT employees.*,
                          CASE WHEN encoding_model = ? THEN biometric_profiles.id END AS biometric_id
                   FROM employees LEFT JOIN biometric_profiles ON employee_id = employees.id
                   ORDER BY full_name, employees.id""", (ENCODING_MODEL,)
            ).fetchall()

    def create_employee(self, full_name, email, status):
        with get_connection(self.path) as db:
            return db.execute(
                "INSERT INTO employees (full_name, email, status) VALUES (?, ?, ?)",
                (full_name, email, status),
            ).lastrowid

    def toggle_status(self, employee_id):
        with get_connection(self.path) as db:
            db.execute(
                """UPDATE employees
                   SET status = CASE status WHEN 'active' THEN 'inactive' ELSE 'active' END,
                       deactivated_at = CASE status WHEN 'active' THEN ? ELSE NULL END
                   WHERE id = ?""",
                (datetime.now().isoformat(timespec="seconds"), employee_id),
            )

    def save_encoding(self, employee_id, encoding):
        with get_connection(self.path) as db:
            db.execute(
                """INSERT INTO biometric_profiles (employee_id, face_encoding, encoding_model)
                   VALUES (?, ?, ?)
                   ON CONFLICT(employee_id) DO UPDATE SET
                       face_encoding = excluded.face_encoding,
                       encoding_model = excluded.encoding_model,
                       source_image_path = NULL,
                       enrolled_at = CURRENT_TIMESTAMP""",
                (employee_id, encoding, ENCODING_MODEL),
            )

    def active_profiles(self):
        with get_connection(self.path) as db:
            return db.execute(
                """SELECT employees.id, full_name, face_encoding FROM employees
                   JOIN biometric_profiles ON employee_id = employees.id
                   WHERE status = 'active' AND encoding_model = ? AND face_encoding IS NOT NULL
                   ORDER BY employees.id""", (ENCODING_MODEL,)
            ).fetchall()

    def metrics(self):
        with get_connection(self.path) as db:
            employees = db.execute(
                "SELECT COUNT(*) AS total, COALESCE(SUM(status = 'active'), 0) AS active FROM employees"
            ).fetchone()
            enrolled = db.execute(
                "SELECT COUNT(*) FROM biometric_profiles WHERE encoding_model = ? AND face_encoding IS NOT NULL",
                (ENCODING_MODEL,),
            ).fetchone()[0]
        return dict(employees=employees["total"], active=employees["active"], enrolled=enrolled)

    def log_access(self, employee_id, result, detail):
        with get_connection(self.path) as db:
            db.execute(
                "INSERT INTO access_logs (employee_id, result, detail, created_at) VALUES (?, ?, ?, ?)",
                (employee_id, result, detail, datetime.now().isoformat(sep=" ", timespec="seconds")),
            )

    def recent_accesses(self):
        with get_connection(self.path) as db:
            return db.execute(
                """SELECT access_logs.*, employees.full_name FROM access_logs
                   LEFT JOIN employees ON employees.id = access_logs.employee_id
                   ORDER BY access_logs.id DESC LIMIT 10"""
            ).fetchall()
