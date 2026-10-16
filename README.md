# Proyecto 2 - Sistema de Asistencias por reconocimiento facial

El proyecto incluye los **dos scripts de la consigna** y el panel web que ya tenía el equipo.

- `comparar_rostros.py`: compara una imagen de control con una de prueba. Muestra ambos rostros con recuadros, coincidencia y distancia.
- `asistencia.py`: reconoce empleados con la webcam, dibuja nombres y recuadros, y registra el primer ingreso del día en CSV.
- `app.py`: panel web de personal, enrolamiento, molinete y consulta/descarga de asistencias.

## Instalar en Windows

Desde PowerShell en esta carpeta, ejecutar una línea a la vez:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows.ps1
```

El instalador usa `.venv` directamente; no necesita activación. Para compilar `dlib` puede hacer falta CMake y Visual Studio Build Tools con **Desarrollo de escritorio con C++**. En el equipo revisado se comprobó su presencia. No alcanza con instalar solo CMake si faltan las herramientas de C++. Los scripts usan rutas cortas de Windows para los modelos de dlib cuando la carpeta contiene tildes. Si el equipo no dispone de esas rutas, generan una caché temporal sin tildes; puede indicarse con FACE_MODELS_CACHE.

Instalación manual:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-vision.txt -r requirements-asistencia.txt
.\.venv\Scripts\python.exe -m pip check
```

`requirements.txt` instala el panel y NumPy. `requirements-vision.txt` instala InsightFace para el panel. `requirements-asistencia.txt` instala `face_recognition`, OpenCV y las dependencias de los dos scripts académicos. `os`, `csv`, `datetime`, `pathlib` y `sqlite3` forman parte de Python.

## 1. Comparar dos imágenes

```powershell
.\.venv\Scripts\python.exe comparar_rostros.py "C:\ruta\control.jpg" "C:\ruta\prueba.jpg"
```

Cada imagen debe contener exactamente un rostro. Se abre una ventana con las imágenes, sus recuadros, el resultado y la distancia. Pulsar una tecla para cerrar. También guarda `data/comparacion.jpg`.

Para ejecutar sin ventana:

```powershell
.\.venv\Scripts\python.exe comparar_rostros.py "C:\ruta\control.jpg" "C:\ruta\prueba.jpg" --sin-ventana --salida "data/comparacion.jpg"
```

La distancia de `face_recognition` es euclídea entre vectores de 128 componentes: **menor es más parecido**. La tolerancia inicial es `0.6`; puede cambiarse con `--tolerancia`. No es un porcentaje ni garantiza precisión: debe evaluarse con fotografías distintas de la misma persona y de otras personas.

## 2. Preparar empleados

Hay dos fuentes, elegidas explícitamente:

### Usar las fotos registradas en el panel

```powershell
.\.venv\Scripts\python.exe app.py
```

Abrir http://127.0.0.1:5000, cargar personal y enrolar sus fotos. Luego ejecutar `asistencia.py` desde otra terminal. El script usa las **fotos** de los empleados activos para calcular sus propios vectores con `face_recognition`. No modifica ni reutiliza como propios los vectores de InsightFace.

### Usar una carpeta, como en la consigna

Colocar JPG o PNG dentro de `empleados/`, por ejemplo:

```text
empleados/
  Ana_Perez.jpg
  Bruno_Gomez.png
```

El programa lista la carpeta con `os.listdir` y obtiene el nombre del archivo: `Ana_Perez.jpg` se muestra como `Ana Perez`. Cada foto de referencia debe tener un rostro. En este modo no existe el estado activo/inactivo del panel: las fotos de esa carpeta forman el padrón. Usar nombres de archivo distintos para personas distintas.

## 3. Iniciar asistencia en tiempo real

Con empleados del panel:

```powershell
.\.venv\Scripts\python.exe asistencia.py
```

Con la carpeta de la consigna:

```powershell
.\.venv\Scripts\python.exe asistencia.py --fuente carpeta --empleados empleados
```

La cámara muestra recuadros y nombres. Los desconocidos aparecen en rojo y no generan asistencia. Se procesa uno de cada tres cuadros por defecto para reducir CPU; `--cada 1` procesa todos. La ventana muestra el último cuadro procesado con sus anotaciones. **Q** o **Escape** cierran y liberan la cámara. Si la webcam está ocupada, cerrar la cámara del navegador y otras apps; usar `--camara 1` si corresponde a otro dispositivo.

El modo del panel vuelve a consultar el estado activo al reconocer y antes de registrar. Para incorporar fotos nuevas o reemplazadas hay que reiniciar el script, porque las referencias se cargan al iniciar.

## CSV de asistencias

Web y webcam comparten `data/asistencias.csv` con columnas:

```csv
empleado_id,nombre,fecha,hora,origen
1,Ana Perez,2026-10-16,09:15:30,webcam
```

La fecha y hora son locales del equipo. Se guarda **un primer ingreso por persona y día**, incluso al reiniciar el programa, para no repetir una fila por cada fotograma. Al día siguiente se admite un nuevo ingreso. Personas distintas con el mismo nombre se distinguen por su ID en el modo base. En modo carpeta el ID deriva del nombre del archivo.

La web muestra **Asistencias** y permite descargar el CSV. Los accesos denegados permanecen en el historial de accesos de SQLite, pero no se agregan al CSV de presentes. El archivo usa UTF-8 con BOM para conservar tildes al abrirlo en Excel. `--csv otra/ruta.csv` permite elegir un archivo distinto para una demostración o prueba.

## Prueba con una foto sin abrir la webcam

```powershell
.\.venv\Scripts\python.exe asistencia.py --imagen "C:\ruta\foto.jpg" --csv "data/prueba_asistencias.csv"
```

Usa el mismo flujo de detección y registro, guarda `data/asistencia_prueba.jpg` y no abre la cámara. Es una prueba de diagnóstico; no sustituye probar la webcam física. El CSV separado evita registrar una asistencia real durante el ensayo.

## Pruebas automatizadas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Consultar `CONSIGNA.md` para el mapa de requisitos y `VERIFICACION_CONSIGNA.md` para los resultados y límites de la verificación. Los PDF anteriores son material del Sprint 1 previo a estos cambios.

## Motores y límites

Los dos scripts usan **face_recognition/dlib**, como pide la consigna. El panel conserva **InsightFace/ONNX Runtime** para mantener sus perfiles existentes. Son motores y espacios de vectores diferentes: no se mezclan sus distancias ni sus umbrales. El umbral coseno de `0.40` del panel no equivale a la tolerancia euclídea de `0.6` de los scripts.

Se trata de un prototipo educativo, sin prueba de vida, autenticación administrativa ni evaluación formal de precisión. La ejecución web tiene debug desactivado por defecto; `FLASK_DEBUG=1` lo habilita para desarrollo. Para compartir o usar datos reales hacen falta controles adicionales. La primera preparación del motor del panel puede descargar modelos.

`data/`, `uploads/` y las fotos dentro de `empleados/` están ignorados por Git porque contienen datos personales. SQLite es local; no hace falta configurar un servidor.

## Archivos integrados del grupo

Se conserva `control_asistencia.py`, la variante simple de cámara del grupo: usa las fotos de `empleados/`, tolerancia 0.50 y genera `asistencia.csv` con nombre, fecha y hora. El programa `asistencia.py` agrega la integración con el panel y el CSV compartido `data/asistencias.csv`, con tolerancia inicial 0.60.

`GUIA_EXPOSICION_5_PERSONAS.md` distribuye la defensa entre los integrantes. El panel conserva InsightFace de 512 componentes y los scripts académicos utilizan face_recognition de 128. La columna `encoding_model` incorporada por el grupo identifica el motor; las biometrías anteriores sin esa marca siguen siendo compatibles por dimensión. No se mezclan los vectores de motores diferentes.
