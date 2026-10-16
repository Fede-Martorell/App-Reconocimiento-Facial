"""Asistencia diaria en CSV, compartida por la web y el programa de cámara."""
from __future__ import annotations

import csv
import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from threading import RLock

DEFAULT_CSV = Path(__file__).resolve().parent / "data" / "asistencias.csv"
FIELDS = ["empleado_id", "nombre", "fecha", "hora", "origen"]
_thread_lock = RLock()


@contextmanager
def _locked(path: Path):
    """Bloquear entre hilos y procesos para no duplicar el ingreso diario."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with _thread_lock, path.with_suffix(path.suffix + ".lock").open("a+b") as lock:
        if lock.seek(0, 2) == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == "nt":
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _read(path: Path) -> list[dict]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != FIELDS:
            raise ValueError("El CSV de asistencias tiene columnas incompatibles. Usá otro archivo.")
        rows = list(reader)
        if any(None in row or any(value is None for value in row.values()) for row in rows):
            raise ValueError("El CSV contiene filas incompletas o inválidas.")
        return rows


def read_attendance(csv_path: str | Path = DEFAULT_CSV) -> list[dict]:
    path = Path(csv_path)
    with _locked(path):
        return _read(path)


def record_attendance(employee_id, name: str, csv_path: str | Path = DEFAULT_CSV,
                      *, now: datetime | None = None, origin: str = "webcam") -> bool:
    """True si registró el primer ingreso del día; False si ya estaba registrado."""
    employee_id, name = str(employee_id).strip(), name.strip()
    if not employee_id or not name:
        raise ValueError("La asistencia necesita un identificador y un nombre.")
    moment = now if now is not None else datetime.now().astimezone()
    date = moment.strftime("%Y-%m-%d")
    path = Path(csv_path)
    with _locked(path):
        rows = _read(path)
        if any(row["empleado_id"] == employee_id and row["fecha"] == date for row in rows):
            return False
        needs_header = not path.exists() or path.stat().st_size == 0
        with path.open("a", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            if needs_header:
                writer.writeheader()
            writer.writerow(dict(empleado_id=employee_id, nombre=name, fecha=date,
                                 hora=moment.strftime("%H:%M:%S"), origen=origin))
            stream.flush()
            os.fsync(stream.fileno())
    return True
