"""Script 1: comparar dos imágenes y visualizar coincidencia y distancia."""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from face_recognition_engine import Face, Profile, best_match, draw_face, read_image, save_image, single_face


def compare_images(control_path, test_path, tolerance=0.6):
    control, test = read_image(control_path), read_image(test_path)
    control_face, test_face = single_face(control), single_face(test)
    index, distance = best_match(test_face.encoding, [Profile("control", "Control", control_face.encoding)], tolerance)
    match = index is not None
    panels = []
    for image, face, label, allowed in ((control, control_face, "Control", True),
                                         (test, test_face, "Coincide" if match else "No coincide", match)):
        scale = min(600 / image.shape[1], 520 / image.shape[0])
        resized = cv2.resize(image, (max(1, int(image.shape[1] * scale)), max(1, int(image.shape[0] * scale))))
        scaled_face = Face(tuple(int(round(value * scale)) for value in face.location), face.encoding)
        draw_face(resized, scaled_face, label, allowed)
        panels.append(resized)
    height = max(panel.shape[0] for panel in panels)
    panels = [cv2.copyMakeBorder(panel, 0, height - panel.shape[0], 0, 0, cv2.BORDER_CONSTANT) for panel in panels]
    result = cv2.hconcat(panels)
    result = cv2.copyMakeBorder(result, 100, 0, 0, 0, cv2.BORDER_CONSTANT, value=(245, 245, 245))
    color = (30, 140, 30) if match else (30, 30, 200)
    cv2.putText(result, "COINCIDE" if match else "NO COINCIDE", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, .8, color, 2)
    cv2.putText(result, f"Distancia: {distance:.3f} / Tolerancia: {tolerance:.2f}", (15, 59), cv2.FONT_HERSHEY_SIMPLEX, .6, (30, 30, 30), 1)
    cv2.putText(result, "Control (izquierda) | Prueba (derecha)", (15, 84), cv2.FONT_HERSHEY_SIMPLEX, .55, (30, 30, 30), 1)
    return match, distance, result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("control", type=Path, help="Foto de control con un rostro.")
    parser.add_argument("prueba", type=Path, help="Foto de prueba con un rostro.")
    parser.add_argument("--tolerancia", type=float, default=0.6, help="Distancia máxima; no es un porcentaje.")
    parser.add_argument("--salida", type=Path, default=Path(__file__).resolve().parent / "data/comparacion.jpg")
    parser.add_argument("--sin-ventana", action="store_true", help="Guardar el resultado sin abrir una ventana.")
    args = parser.parse_args(argv)
    try:
        match, distance, image = compare_images(args.control, args.prueba, args.tolerancia)
        save_image(args.salida, image)
        print(f"{'COINCIDE' if match else 'NO COINCIDE'} | Distancia: {distance:.4f} | Tolerancia: {args.tolerancia:.2f}")
        print(f"Imagen de resultado: {args.salida}")
        if not args.sin_ventana:
            cv2.imshow("Comparacion de rostros - pulse una tecla para salir", image)
            cv2.waitKey(0)
        return 0
    except (ValueError, RuntimeError, OSError, cv2.error) as error:
        print(f"Error: {error}")
        return 1
    finally:
        if not args.sin_ventana:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    raise SystemExit(main())
