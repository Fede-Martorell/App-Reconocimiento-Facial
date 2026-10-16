"""Script 2: asistencia en tiempo real con webcam, nombres y registro CSV."""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import cv2

from attendance_log import DEFAULT_CSV, record_attendance
from face_recognition_engine import (BASE_DIR, Face, best_match, detect_faces, draw_face,
                                     is_active, load_profiles, read_image, save_image)


def process_frame(frame, profiles, tolerance, csv_path, *, now: datetime | None = None, origin: str = "webcam"):
    """Mismo procesamiento para la cámara y para la prueba con una imagen."""
    annotated = frame.copy()
    observations = []
    # No permitir que un perfil desactivado compita con los perfiles activos.
    profiles = [profile for profile in profiles if is_active(profile)]
    scale = min(1., 640 / max(frame.shape[:2]))
    working = cv2.resize(frame, None, fx=scale, fy=scale) if scale < 1 else frame
    faces = detect_faces(working)
    for detected in faces:
        face = Face(tuple(int(round(value / scale)) for value in detected.location), detected.encoding)
        index, distance = best_match(face.encoding, profiles, tolerance)
        if index is None:
            label = "Desconocido"
            draw_face(annotated, face, label, False)
            observations.append(dict(name=label, allowed=False, registered=False, distance=distance))
            continue
        profile = profiles[index]
        # Verificación adicional inmediatamente antes de guardar el ingreso.
        if not is_active(profile):
            draw_face(annotated, face, "Inactivo", False)
            observations.append(dict(name="Inactivo", allowed=False, registered=False, distance=distance))
            continue
        added = record_attendance(profile.employee_id, profile.name, csv_path, now=now, origin=origin)
        label = profile.name + (" - Registrado" if added else " - Ya registrado hoy")
        draw_face(annotated, face, label, True)
        if added:
            print(f"Asistencia registrada: {profile.name}")
        observations.append(dict(name=profile.name, allowed=True, registered=added, distance=distance))
    return annotated, observations


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fuente", choices=["base", "carpeta"], default="base", help="base reutiliza las fotos del panel; carpeta usa nombres de archivo.")
    parser.add_argument("--empleados", type=Path, default=BASE_DIR / "empleados")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--camara", type=int, default=0)
    parser.add_argument("--tolerancia", type=float, default=0.6)
    parser.add_argument("--cada", type=int, default=3, help="Procesar uno de cada N cuadros para reducir uso de CPU.")
    parser.add_argument("--max-fotogramas", type=int, default=0, help="0: sin límite; otro valor permite una prueba acotada.")
    parser.add_argument("--sin-ventana", action="store_true")
    parser.add_argument("--imagen", type=Path, help="Prueba del mismo flujo sobre una imagen, sin abrir la cámara.")
    parser.add_argument("--salida", type=Path, default=BASE_DIR / "data/asistencia_prueba.jpg")
    args = parser.parse_args(argv)
    capture = None
    try:
        if not 0 < args.tolerancia <= 1 or args.cada < 1 or args.max_fotogramas < 0:
            raise ValueError("Usá tolerancia en (0, 1], --cada >= 1 y --max-fotogramas >= 0.")
        if args.sin_ventana and not args.imagen and not args.max_fotogramas:
            raise ValueError("La prueba de cámara sin ventana necesita --max-fotogramas para poder terminar.")
        profiles, warnings = load_profiles(args.fuente, args.empleados)
        for warning in warnings:
            print(f"Foto omitida: {warning}")
        if not profiles:
            raise ValueError("No hay empleados con fotos válidas. Cargalos en el panel o en la carpeta indicada.")
        print(f"Perfiles cargados: {len(profiles)}. CSV: {args.csv}")
        if args.imagen:
            image, observations = process_frame(read_image(args.imagen), profiles, args.tolerancia, args.csv, origin="imagen")
            save_image(args.salida, image)
            for item in observations:
                print(f"{item['name']} | Reconocido: {item['allowed']} | Distancia: {item['distance']}")
            print(f"Resultado guardado: {args.salida}")
            return 0
        capture = cv2.VideoCapture(args.camara)
        if not capture.isOpened():
            raise ValueError("No se pudo abrir la webcam. Cerrá otras apps que la usen y revisá --camara 0 o 1 y los permisos de Windows.")
        print("Cámara iniciada. Q o Escape para salir. Reiniciá el programa si agregás o actualizás fotos.")
        count = 0
        display = None
        while True:
            ok, frame = capture.read()
            if not ok or frame is None:
                raise ValueError("La cámara dejó de entregar imágenes.")
            if count % args.cada == 0:
                display, _ = process_frame(frame, profiles, args.tolerancia, args.csv)
            # Mostrar el último cuadro procesado para no dibujar cajas sobre otro instante.
            if not args.sin_ventana:
                cv2.imshow("Asistencia - Q o Escape para salir", display)
                if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                    break
            count += 1
            if args.max_fotogramas and count >= args.max_fotogramas:
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
        if not args.sin_ventana:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    raise SystemExit(main())
