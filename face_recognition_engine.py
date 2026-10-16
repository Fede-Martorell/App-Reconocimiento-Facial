"""Motor de los dos scripts de la consigna: face_recognition + OpenCV.

Sus vectores de 128 valores NO se mezclan con los de InsightFace del panel.
"""
from __future__ import annotations

import os
import unicodedata
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
_library = None


@dataclass
class Face:
    location: tuple[int, int, int, int]  # top, right, bottom, left
    encoding: np.ndarray


@dataclass
class Profile:
    employee_id: str
    name: str
    encoding: np.ndarray
    from_database: bool = False


def _compatible_model_path(path: str) -> str:
    if os.name != "nt" or path.isascii():
        return path
    # dlib abre sus modelos con una API que puede fallar con rutas Unicode.
    import ctypes
    buffer = ctypes.create_unicode_buffer(32768)
    if ctypes.windll.kernel32.GetShortPathNameW(path, buffer, len(buffer)) and buffer.value.isascii():
        return buffer.value
    # Equipos con nombres 8.3 desactivados: copiar a una caché ASCII temporal.
    import shutil
    import tempfile
    source = Path(path)
    cache_root = Path(os.environ.get("FACE_MODELS_CACHE", str(Path(tempfile.gettempdir()) / "face-recognition-models")))
    if not str(cache_root).isascii():
        raise RuntimeError("Configurá FACE_MODELS_CACHE con una carpeta sin tildes para los modelos de dlib.")
    stat = source.stat()
    target = cache_root / f"{stat.st_size}-{stat.st_mtime_ns}" / source.name
    if not target.exists() or target.stat().st_size != stat.st_size:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
                temporary = Path(stream.name)
                with source.open("rb") as original:
                    shutil.copyfileobj(original, stream)
            os.replace(temporary, target)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
    return str(target)


def face_library():
    global _library
    if _library is not None:
        return _library
    try:
        import face_recognition_models as models
        if os.name == "nt":
            for name in ("pose_predictor_model_location", "pose_predictor_five_point_model_location",
                         "face_recognition_model_location", "cnn_face_detector_model_location"):
                original = getattr(models, name)
                setattr(models, name, lambda original=original: _compatible_model_path(original()))
        import face_recognition as fr
    except ImportError as error:
        raise RuntimeError(
            "Falta face_recognition o alguna dependencia. Ejecutá install_windows.ps1 "
            "o instalá requirements-asistencia.txt con el Python de .venv."
        ) from error
    _library = fr
    return fr


def read_image(path: str | Path) -> np.ndarray:
    """Leer por bytes: admite carpetas con tildes en Windows."""
    try:
        content = Path(path).read_bytes()
    except OSError as error:
        raise ValueError(f"No se pudo abrir la imagen: {path}") from error
    image = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR) if content else None
    if image is None:
        raise ValueError(f"El archivo no contiene una imagen válida: {path}")
    return image


def detect_faces(bgr: np.ndarray) -> list[Face]:
    fr = face_library()
    # OpenCV trabaja en BGR; face_recognition recibe RGB.
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    locations = fr.face_locations(rgb, model="hog")
    encodings = fr.face_encodings(rgb, known_face_locations=locations, model="small")
    return [Face(location, encoding) for location, encoding in zip(locations, encodings)]


def single_face(bgr: np.ndarray) -> Face:
    faces = detect_faces(bgr)
    if len(faces) != 1:
        raise ValueError(f"Cada foto de referencia o comparación debe contener un rostro; se detectaron {len(faces)}.")
    return faces[0]


def best_match(encoding: np.ndarray, profiles: list[Profile], tolerance: float = 0.6):
    if not 0 < tolerance <= 1:
        raise ValueError("La tolerancia debe ser mayor que 0 y menor o igual a 1.")
    if not profiles:
        return None, None
    fr = face_library()
    distances = fr.face_distance([profile.encoding for profile in profiles], encoding)
    index = int(np.argmin(distances))
    distance = float(distances[index])
    matches = fr.compare_faces([profiles[index].encoding], encoding, tolerance=tolerance)
    return (index if matches[0] else None), distance


def load_profiles(source: str, folder: str | Path) -> tuple[list[Profile], list[str]]:
    profiles, warnings = [], []
    if source == "base":
        from database import DATABASE_PATH
        import sqlite3
        if not DATABASE_PATH.exists():
            raise ValueError("Primero abrí el panel y cargá empleados con sus fotos, o usá --fuente carpeta.")
        with closing(sqlite3.connect(DATABASE_PATH)) as db:
            entries = [(str(row[0]), row[1], BASE_DIR / row[2], True) for row in db.execute(
                """SELECT employees.id, full_name, source_image_path FROM employees
                   JOIN biometric_profiles ON employee_id = employees.id
                   WHERE status = 'active' AND source_image_path IS NOT NULL"""
            )]
    elif source == "carpeta":
        folder = Path(folder)
        if not folder.is_dir():
            raise ValueError(f"No existe la carpeta de empleados: {folder}")
        entries = [("archivo:" + Path(name).stem.casefold(), Path(name).stem.replace("_", " "),
                    folder / name, False) for name in sorted(os.listdir(folder))
                   if Path(name).suffix.lower() in {".jpg", ".jpeg", ".png"} and (folder / name).is_file()]
    else:
        raise ValueError("La fuente debe ser base o carpeta.")
    for employee_id, name, path, from_database in entries:
        try:
            face = single_face(read_image(path))
            profiles.append(Profile(employee_id, name, face.encoding, from_database))
        except (ValueError, OSError) as error:
            warnings.append(f"{name}: {error}")
    return profiles, warnings


def is_active(profile: Profile) -> bool:
    if not profile.from_database:
        return True
    from database import DATABASE_PATH
    import sqlite3
    with closing(sqlite3.connect(DATABASE_PATH)) as db:
        row = db.execute("SELECT status FROM employees WHERE id = ?", (profile.employee_id,)).fetchone()
    return row is not None and row[0] == "active"


def ascii_text(text: str) -> str:
    # Las tipografías de OpenCV no incluyen todos los caracteres españoles.
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


def draw_face(image: np.ndarray, face: Face, label: str, allowed: bool) -> None:
    top, right, bottom, left = face.location
    height, width = image.shape[:2]
    top, bottom = max(0, top), min(height - 1, bottom)
    left, right = max(0, left), min(width - 1, right)
    color = (40, 170, 40) if allowed else (40, 40, 220)
    thickness = max(2, int(width / 400))
    font_scale = max(0.55, width / 1400)
    cv2.rectangle(image, (left, top), (right, bottom), color, thickness)
    label = ascii_text(label)
    (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
    x = max(0, min(left, width - text_width - 5))
    y = max(text_height + 8, min(top - 10, height - 8))
    cv2.putText(image, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                (0, 0, 0), thickness + 3, cv2.LINE_AA)
    cv2.putText(image, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                color, thickness, cv2.LINE_AA)


def save_image(path: str | Path, image: np.ndarray) -> None:
    path = Path(path)
    if path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        raise ValueError("La salida debe terminar en .jpg, .jpeg o .png.")
    success, encoded = cv2.imencode(path.suffix, image)
    if not success:
        raise ValueError("No se pudo generar la imagen de resultado.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded.tobytes())
