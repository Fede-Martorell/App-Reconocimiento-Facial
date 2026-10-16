"""Registra asistencia mediante reconocimiento facial en tiempo real."""

from __future__ import annotations

import csv
import os
from datetime import datetime
import warnings

import cv2

warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
import face_recognition as fr
import numpy as np


CARPETA_EMPLEADOS = "empleados"
ARCHIVO_ASISTENCIA = "asistencia.csv"
TOLERANCIA = 0.50
ESCALA = 0.25


def cargar_empleados(carpeta: str) -> tuple[list[np.ndarray], list[str]]:
    os.makedirs(carpeta, exist_ok=True)
    encodings_conocidos: list[np.ndarray] = []
    nombres: list[str] = []

    for archivo in sorted(os.listdir(carpeta)):
        if os.path.splitext(archivo)[1].lower() not in {".jpg", ".jpeg", ".png"}:
            continue

        ruta = os.path.join(carpeta, archivo)
        imagen_bgr = cv2.imread(ruta)
        if imagen_bgr is None:
            print(f"Se omite {archivo}: OpenCV no pudo leerlo.")
            continue

        imagen_rgb = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)
        encodings = fr.face_encodings(imagen_rgb)
        if len(encodings) != 1:
            print(f"Se omite {archivo}: debe contener exactamente un rostro.")
            continue

        encodings_conocidos.append(encodings[0])
        nombres.append(os.path.splitext(archivo)[0])

    return encodings_conocidos, nombres


def asistencias_de_hoy(ruta_csv: str) -> set[str]:
    hoy = datetime.now().strftime("%Y-%m-%d")
    registrados: set[str] = set()
    if not os.path.isfile(ruta_csv):
        return registrados

    with open(ruta_csv, newline="", encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            if fila.get("fecha") == hoy:
                registrados.add(fila.get("nombre", ""))
    return registrados


def registrar_asistencia(nombre: str, ruta_csv: str, registrados: set[str]) -> None:
    if nombre in registrados:
        return

    ahora = datetime.now()
    nuevo_archivo = not os.path.isfile(ruta_csv)
    with open(ruta_csv, "a", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=["nombre", "fecha", "hora"])
        if nuevo_archivo:
            escritor.writeheader()
        escritor.writerow({
            "nombre": nombre,
            "fecha": ahora.strftime("%Y-%m-%d"),
            "hora": ahora.strftime("%H:%M:%S"),
        })
    registrados.add(nombre)
    print(f"Asistencia registrada: {nombre} - {ahora:%H:%M:%S}")


def ejecutar() -> None:
    conocidos, nombres = cargar_empleados(CARPETA_EMPLEADOS)
    if not conocidos:
        raise RuntimeError(f"Agregá fotos individuales en la carpeta '{CARPETA_EMPLEADOS}'.")

    registrados = asistencias_de_hoy(ARCHIVO_ASISTENCIA)
    camara = cv2.VideoCapture(0)
    if not camara.isOpened():
        raise RuntimeError("No se pudo abrir la cámara web.")

    procesar = True
    ubicaciones_actuales = []
    nombres_actuales = []
    try:
        while True:
            correcto, fotograma = camara.read()
            if not correcto:
                print("No se pudo leer un fotograma de la cámara.")
                break

            if procesar:
                reducido = cv2.resize(fotograma, (0, 0), fx=ESCALA, fy=ESCALA)
                rgb = cv2.cvtColor(reducido, cv2.COLOR_BGR2RGB)
                ubicaciones_actuales = fr.face_locations(rgb)
                encodings_actuales = fr.face_encodings(rgb, ubicaciones_actuales)
                nombres_actuales = []

                for encoding in encodings_actuales:
                    distancias = fr.face_distance(conocidos, encoding)
                    mejor_indice = int(np.argmin(distancias))
                    coincidencias = fr.compare_faces(conocidos, encoding, tolerance=TOLERANCIA)
                    nombre = nombres[mejor_indice] if coincidencias[mejor_indice] else "Desconocido"
                    nombres_actuales.append(nombre)
                    if nombre != "Desconocido":
                        registrar_asistencia(nombre, ARCHIVO_ASISTENCIA, registrados)

            procesar = not procesar

            for (superior, derecha, inferior, izquierda), nombre in zip(ubicaciones_actuales, nombres_actuales):
                superior, derecha, inferior, izquierda = [int(valor / ESCALA) for valor in (superior, derecha, inferior, izquierda)]
                color = (0, 180, 0) if nombre != "Desconocido" else (0, 0, 220)
                cv2.rectangle(fotograma, (izquierda, superior), (derecha, inferior), color, 2)
                cv2.rectangle(fotograma, (izquierda, inferior - 30), (derecha, inferior), color, -1)
                cv2.putText(fotograma, nombre, (izquierda + 6, inferior - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

            cv2.imshow("Control de asistencia - presione Q para salir", fotograma)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camara.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    ejecutar()
