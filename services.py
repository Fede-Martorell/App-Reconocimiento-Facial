"""Reglas del sistema, compartidas por el panel web y la webcam."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO

import numpy as np

from database import EmployeeRepository
from attendance_log import read_attendance, record_attendance
from face_recognition_engine import Profile, best_match, decode_image, single_face


class InactiveEmployeeError(ValueError):
    """El empleado dejó de estar habilitado durante el reconocimiento."""


@dataclass
class AttendanceDecision:
    result: str
    message: str
    distance: float | None = None
    attendance: str | None = None


class AttendanceService:
    def __init__(self, repository: EmployeeRepository, csv_path, tolerance: float = 0.6):
        self.repository = repository
        self.csv_path = csv_path
        self.tolerance = tolerance

    def create_employee(self, full_name: str, email: str, status: str) -> int:
        full_name = full_name.strip()
        email = email.strip() or None
        if not full_name or len(full_name) > 120:
            raise ValueError("El nombre debe tener entre 1 y 120 caracteres.")
        if email and (len(email) > 160 or "@" not in email):
            raise ValueError("Ingresá un email válido de hasta 160 caracteres.")
        if status not in {"active", "inactive"}:
            raise ValueError("Estado de empleado inválido.")
        try:
            return self.repository.create_employee(full_name, email, status)
        except sqlite3.IntegrityError as error:
            raise ValueError("Ya existe un empleado con ese email.") from error

    def enroll(self, employee_id: int, image_bytes: bytes) -> None:
        if self.repository.get_employee(employee_id) is None:
            raise ValueError("Empleado inexistente.")
        face = single_face(decode_image(image_bytes))
        buffer = BytesIO()
        np.save(buffer, face.encoding, allow_pickle=False)
        self.repository.save_encoding(employee_id, buffer.getvalue())

    def profiles(self) -> list[Profile]:
        profiles = []
        for employee in self.repository.active_profiles():
            encoding = np.load(BytesIO(employee["face_encoding"]), allow_pickle=False)
            if encoding.shape != (128,) or not np.isfinite(encoding).all():
                raise ValueError(f"Actualizá la foto del empleado {employee['id']}: su biometría es inválida.")
            profiles.append(Profile(employee["full_name"], encoding, str(employee["id"])))
        return profiles

    def register(self, profile: Profile, *, origin: str) -> bool:
        """Consultar el estado actual antes de registrar, también desde la webcam."""
        employee = self.repository.get_employee(profile.employee_id)
        if employee is None or employee["status"] != "active":
            raise InactiveEmployeeError("El empleado no está activo.")
        return record_attendance(employee["id"], employee["full_name"], self.csv_path, origin=origin)

    def verify(self, image_bytes: bytes) -> AttendanceDecision:
        """Identificar una captura, registrar el ingreso y dejar auditoría."""
        face = single_face(decode_image(image_bytes))
        profiles = self.profiles()
        index, distance = best_match(face.encoding, profiles, self.tolerance)
        if index is None:
            self.repository.log_access(None, "denied", "Rostro no identificado entre el personal activo")
            return AttendanceDecision("denied", "Persona no identificada", distance)
        profile = profiles[index]
        registered = self.register(profile, origin="web")
        self.repository.log_access(profile.employee_id, "allowed", "Reconocimiento facial validado")
        return AttendanceDecision(
            "allowed", f"Ingreso verificado: {profile.name}", distance,
            "Asistencia registrada." if registered else "Ya registraste asistencia hoy.",
        )

    def attendance(self, date: str | None = None) -> list[dict]:
        rows = read_attendance(self.csv_path)
        if date:
            datetime.strptime(date, "%Y-%m-%d")
            rows = [row for row in rows if row["fecha"] == date]
        return rows
