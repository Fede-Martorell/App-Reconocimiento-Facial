"""Script 2: reconocer empleados con la webcam y registrar su asistencia."""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from attendance_log import DEFAULT_CSV, record_attendance
from face_recognition_engine import BASE_DIR, Face, best_match, detect_faces, draw_face, load_profiles
from database import DATABASE_PATH, EmployeeRepository
from services import AttendanceService, InactiveEmployeeError


def process_frame(frame, profiles, tolerance, csv_path, service=None):
    """Reconocer y dibujar todos los rostros; registrar solo los conocidos."""
    annotated = frame.copy()
    # Reducir la imagen para agilizar la detección y restaurar las coordenadas.
    scale = min(1., 640 / max(frame.shape[:2]))
    working = cv2.resize(frame, None, fx=scale, fy=scale) if scale < 1 else frame
    if service is not None:
        profiles = service.profiles()
    for detected in detect_faces(working):
        face = Face(tuple(int(round(value / scale)) for value in detected.location), detected.encoding)
        index, _ = best_match(face.encoding, profiles, tolerance)
        if index is None:
            draw_face(annotated, face, "Desconocido", False)
            continue
        profile = profiles[index]
        if service is not None:
            try:
                registered = service.register(profile, origin="webcam")
            except InactiveEmployeeError:
                draw_face(annotated, face, "Empleado inactivo", False)
                continue
        else:
            identity = profile.employee_id or "archivo:" + profile.name.casefold()
            registered = record_attendance(identity, profile.name, csv_path, origin="carpeta")
        if registered:
            print(f"Asistencia registrada: {profile.name}")
        draw_face(annotated, face, profile.name, True)
    return annotated


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fuente", choices=["base", "carpeta"], default="base", help="base: empleados del panel; carpeta: fotos por nombre.")
    parser.add_argument("--base", type=Path, default=DATABASE_PATH)
    parser.add_argument("--empleados", type=Path, default=BASE_DIR / "empleados")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--camara", type=int, default=0)
    parser.add_argument("--tolerancia", type=float, default=0.6)
    args = parser.parse_args(argv)
    capture = None
    try:
        if not 0 < args.tolerancia <= 1:
            raise ValueError("La tolerancia debe ser mayor que 0 y menor o igual a 1.")
        service = None
        if args.fuente == "base":
            service = AttendanceService(EmployeeRepository(args.base), args.csv, args.tolerancia)
            profiles, warnings = service.profiles(), []
        else:
            profiles, warnings = load_profiles(args.empleados)
        for warning in warnings:
            print(f"Foto omitida: {warning}")
        if not profiles:
            raise ValueError("No hay empleados con fotos válidas. Cargá sus fotos en el panel o usá --fuente carpeta.")
        print(f"Empleados cargados: {len(profiles)}. CSV: {args.csv}")
        capture = cv2.VideoCapture(args.camara)
        if not capture.isOpened():
            raise ValueError("No se pudo abrir la webcam. Revisá los permisos o probá --camara 1.")
        print("Cámara iniciada. Q o Escape para salir. Los empleados del panel se actualizan en cada captura.")
        while True:
            ok, frame = capture.read()
            if not ok or frame is None:
                raise ValueError("La cámara dejó de entregar imágenes.")
            display = process_frame(frame, profiles, args.tolerancia, args.csv, service)
            cv2.imshow("Asistencia - Q o Escape para salir", display)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break
        return 0
    except (ValueError, RuntimeError, OSError, cv2.error) as error:
        print(f"Error: {error}")
        return 1
    except KeyboardInterrupt:
        return 0
    finally:
        if capture is not None:
            capture.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    raise SystemExit(main())
