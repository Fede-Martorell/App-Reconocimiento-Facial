"""Compara dos imágenes y muestra si contienen a la misma persona."""

from __future__ import annotations

import argparse
import os
import warnings

import cv2

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
import face_recognition as fr
import numpy as np


TOLERANCIA = 0.50


def cargar_rostro(ruta: str) -> tuple[np.ndarray, np.ndarray, tuple[int, int, int, int]]:
    if not os.path.isfile(ruta):
        raise FileNotFoundError(f"No existe la imagen: {ruta}")

    imagen_bgr = cv2.imread(ruta)
    if imagen_bgr is None:
        raise ValueError(f"OpenCV no pudo leer la imagen: {ruta}")

    imagen_rgb = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)
    ubicaciones = fr.face_locations(imagen_rgb)
    codificaciones = fr.face_encodings(imagen_rgb, ubicaciones)
    if len(codificaciones) != 1:
        raise ValueError(f"{ruta} debe contener exactamente un rostro; se detectaron {len(codificaciones)}.")

    return imagen_bgr, codificaciones[0], ubicaciones[0]


def dibujar_rostro(imagen: np.ndarray, ubicacion, etiqueta: str) -> np.ndarray:
    superior, derecha, inferior, izquierda = ubicacion
    salida = imagen.copy()
    cv2.rectangle(salida, (izquierda, superior), (derecha, inferior), (0, 200, 0), 2)
    cv2.putText(salida, etiqueta, (izquierda, max(superior - 10, 25)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 0), 2)
    return salida


def unir_imagenes(izquierda: np.ndarray, derecha: np.ndarray) -> np.ndarray:
    altura = min(izquierda.shape[0], derecha.shape[0], 650)

    def redimensionar(imagen):
        escala = altura / imagen.shape[0]
        return cv2.resize(imagen, (int(imagen.shape[1] * escala), altura))

    return np.hstack((redimensionar(izquierda), redimensionar(derecha)))


def comparar(ruta_1: str, ruta_2: str, mostrar: bool = True) -> tuple[bool, float]:
    imagen_1, encoding_1, ubicacion_1 = cargar_rostro(ruta_1)
    imagen_2, encoding_2, ubicacion_2 = cargar_rostro(ruta_2)

    distancia = float(fr.face_distance([encoding_1], encoding_2)[0])
    coinciden = bool(fr.compare_faces([encoding_1], encoding_2, tolerance=TOLERANCIA)[0])
    resultado = "COINCIDEN" if coinciden else "NO COINCIDEN"
    print(f"Resultado: {resultado} | Distancia facial: {distancia:.4f} | Tolerancia: {TOLERANCIA:.2f}")

    if mostrar:
        vista_1 = dibujar_rostro(imagen_1, ubicacion_1, "Imagen 1")
        vista_2 = dibujar_rostro(imagen_2, ubicacion_2, "Imagen 2")
        vista = unir_imagenes(vista_1, vista_2)
        color = (0, 180, 0) if coinciden else (0, 0, 220)
        cv2.rectangle(vista, (0, 0), (vista.shape[1], 45), (25, 25, 25), -1)
        cv2.putText(vista, f"{resultado} - distancia: {distancia:.4f}", (15, 31), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.imshow("Comparacion facial", vista)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return coinciden, distancia


def main() -> None:
    parser = argparse.ArgumentParser(description="Compara los rostros presentes en dos imágenes.")
    parser.add_argument("imagen_1")
    parser.add_argument("imagen_2")
    parser.add_argument("--sin-ventana", action="store_true", help="Solo imprime el resultado.")
    argumentos = parser.parse_args()
    comparar(argumentos.imagen_1, argumentos.imagen_2, mostrar=not argumentos.sin_ventana)


if __name__ == "__main__":
    main()
