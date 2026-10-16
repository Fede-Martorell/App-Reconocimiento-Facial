"""Facial-recognition adapter backed by face_recognition and dlib."""

from __future__ import annotations

from io import BytesIO
import warnings

import numpy as np

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)


class RecognitionUnavailable(RuntimeError):
    pass


def _libraries():
    try:
        import cv2
        import face_recognition as fr
    except ImportError as error:
        raise RecognitionUnavailable(
            "Faltan OpenCV o face_recognition. Ejecutá install_windows.ps1."
        ) from error
    return cv2, fr


def _one_encoding(image_rgb: np.ndarray) -> np.ndarray:
    _, fr = _libraries()
    locations = fr.face_locations(image_rgb)
    encodings = fr.face_encodings(image_rgb, locations)
    if len(encodings) != 1:
        raise ValueError("La imagen debe contener exactamente un rostro.")
    return encodings[0].astype(np.float64)


def encoding_from_image(path: str) -> bytes:
    cv2, _ = _libraries()
    image = cv2.imread(path)
    if image is None:
        raise ValueError("No se pudo leer la imagen subida.")
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    buffer = BytesIO()
    np.save(buffer, _one_encoding(image_rgb), allow_pickle=False)
    return buffer.getvalue()


def encoding_from_bytes(image_bytes: bytes) -> np.ndarray:
    cv2, _ = _libraries()
    image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("No se pudo leer la imagen capturada.")
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return _one_encoding(image_rgb)


def find_match(image_bytes: bytes, profiles, tolerance: float = 0.50):
    """Return (employee_id, Euclidean distance), or (None, distance)."""
    _, fr = _libraries()
    candidate = encoding_from_bytes(image_bytes)
    compatible_profiles = []
    stored = []
    for profile in profiles:
        encoding = np.load(BytesIO(profile["face_encoding"]), allow_pickle=False)
        if encoding.shape == candidate.shape:
            compatible_profiles.append(profile)
            stored.append(encoding)
    if not compatible_profiles:
        return None, None
    distances = fr.face_distance(stored, candidate)
    position = int(np.argmin(distances))
    distance = float(distances[position])
    matches = fr.compare_faces(stored, candidate, tolerance=tolerance)
    return (compatible_profiles[position]["employee_id"], distance) if matches[position] else (None, distance)
