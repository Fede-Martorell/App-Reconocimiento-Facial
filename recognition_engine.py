"""Face-recognition adapter backed by InsightFace and ONNX Runtime."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import numpy as np

_model = None


class RecognitionUnavailable(RuntimeError):
    pass


def _get_model():
    global _model
    try:
        from insightface.app import FaceAnalysis
    except ImportError as error:
        raise RecognitionUnavailable(
            "Faltan las librerías de reconocimiento. Instalá requirements-vision.txt."
        ) from error
    if _model is None:
        try:
            # InsightFace downloads its public model pack the first time it is used.
            _model = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
            _model.prepare(ctx_id=0, det_size=(640, 640))
        except Exception as error:
            _model = None
            raise RecognitionUnavailable(
                "No se pudo preparar el modelo facial. Verificá Internet e intentá nuevamente."
            ) from error
    return _model


def _one_embedding(image: np.ndarray) -> np.ndarray:
    faces = _get_model().get(image)
    if len(faces) != 1:
        raise ValueError("La imagen debe contener exactamente un rostro.")
    return faces[0].normed_embedding.astype(np.float32)


def encoding_from_image(path: str) -> bytes:
    try:
        import cv2
    except ImportError as error:
        raise RecognitionUnavailable("Faltan las librerías de reconocimiento. Instalá requirements-vision.txt.") from error
    # Read bytes with Python so Windows paths containing accents work.
    try:
        image_bytes = Path(path).read_bytes()
    except OSError as error:
        raise ValueError("No se pudo leer la imagen subida.") from error
    if not image_bytes:
        raise ValueError("No se pudo leer la imagen subida.")
    image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("No se pudo leer la imagen subida.")
    buffer = BytesIO()
    np.save(buffer, _one_embedding(image), allow_pickle=False)
    return buffer.getvalue()


def encoding_from_bytes(image_bytes: bytes) -> np.ndarray:
    try:
        import cv2
    except ImportError as error:
        raise RecognitionUnavailable("Faltan las librerías de reconocimiento. Instalá requirements-vision.txt.") from error
    if not image_bytes:
        raise ValueError("No se pudo leer la imagen capturada.")
    image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("No se pudo leer la imagen capturada.")
    return _one_embedding(image)


def find_match(image_bytes: bytes, profiles, minimum_similarity: float = 0.40):
    """Return (employee_id, cosine distance), or (None, distance)."""
    candidate = encoding_from_bytes(image_bytes)
    stored = [np.load(BytesIO(profile["face_encoding"]), allow_pickle=False) for profile in profiles]
    if not stored:
        return None, None
    similarities = np.asarray(stored) @ candidate
    position = int(np.argmax(similarities))
    similarity = float(similarities[position])
    distance = 1.0 - similarity
    return (profiles[position]["employee_id"], distance) if similarity >= minimum_similarity else (None, distance)
