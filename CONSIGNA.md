# Correspondencia con la consigna - Proyecto 2

La aplicación original era un panel de control de acceso. Se agregaron los dos programas académicos y un registro de asistencias diario sin eliminar empleados ni biometrías existentes.

| Requisito | Implementación |
|---|---|
| Primer script: comparar dos imágenes | `comparar_rostros.py`, función `compare_images`. |
| Cargar, localizar y codificar rostros | `read_image`, `detect_faces` y `single_face` en `face_recognition_engine.py`. |
| Convertir BGR a RGB | `cv2.cvtColor(..., cv2.COLOR_BGR2RGB)` antes de llamar a `face_recognition`. |
| Comparar coincidencia y distancia | `face_distance`, `compare_faces` y `numpy.argmin` en `best_match`. |
| Mostrar control y prueba | Ventana de OpenCV e imagen de resultado con ambos paneles. |
| Mostrar coincidencia y distancia | Cabecera de la comparación, consola y recuadros. |
| Segundo script: webcam en tiempo real | `asistencia.py`, bucle de `cv2.VideoCapture`. |
| Base de empleados a partir de carpeta | `--fuente carpeta`; `os.listdir`, lectura de JPG/PNG y nombre desde el archivo. |
| Reutilizar personal existente | `--fuente base` toma fotos de SQLite y vuelve a codificarlas con el motor académico. |
| Comparar cada rostro visible | `process_frame` procesa todos los rostros detectados del cuadro. |
| Rectángulos y nombres sobre la captura | `draw_face`, `cv2.rectangle`, `cv2.putText` y `cv2.imshow`. |
| Nombre y hora de ingreso en CSV | `attendance_log.py`, `csv.DictWriter` y `datetime`. Se incluye también fecha e ID. |
| Evitar registros repetidos del mismo día | Control persistente de ID y fecha, protegido por bloqueo entre procesos. |
| Librerías pedidas | OpenCV, face_recognition, os, NumPy y datetime se usan en el flujo real de los scripts. |

## Decisiones agregadas

- Una asistencia diaria significa el **primer ingreso por empleado y día**. No se implementan egresos ni cálculo de horas trabajadas porque la consigna no los pide.
- El modo de carpeta usa como padrón las fotos de esa carpeta. El modo de base respeta activos/inactivos del panel.
- El panel también registra sus reconocimientos permitidos en el mismo CSV y agrega consulta/descarga de asistencias.
- Los vectores de `face_recognition` (128) y de InsightFace (512) se mantienen separados. Se reutilizan las imágenes, no vectores incompatibles.
- Para las rutas con tildes se leen bytes con Python y se decodifican con OpenCV.
- Las comparaciones de referencia requieren un rostro por foto; la cámara puede procesar varios rostros.
- Una no coincidencia es un resultado válido del primer script; un archivo inválido o una cámara inaccesible generan un mensaje de error y un código de salida distinto de cero.

## Referencias técnicas

- [Biblioteca face_recognition y ejemplos oficiales](https://github.com/ageitgey/face_recognition).
- [API: ubicaciones, codificación, comparación y distancias](https://face-recognition.readthedocs.io/en/latest/face_recognition.html).

La validación de requisitos funcionales no representa una garantía de precisión biométrica ni habilita el prototipo para producción.
