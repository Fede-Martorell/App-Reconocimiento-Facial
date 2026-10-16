# Reconocimiento facial y control de asistencia - Sprint 1

El proyecto cumple dos consignas principales: comparar los rostros de dos imágenes y registrar asistencia en tiempo real con una cámara web. Como extensión, incluye un panel Flask para administrar personal autorizado y guardar accesos en SQLite.

## Alcance del sprint

- Comparación de dos imágenes con distancia facial y resultado visual.
- Control de asistencia por cámara web y registro en CSV.
- Panel de administrador: alta de personal y activación/desactivación de acceso.
- Enrolamiento con una foto que contenga exactamente un rostro.
- Simulador de molinete desde el navegador usando la cámara.
- Registro persistente de accesos permitidos y denegados.
- Solo las personas activas y con biometría cargada pueden ingresar.

## Cómo ejecutarlo

Requiere Python 3.12 de 64 bits en Windows. En PowerShell, dentro de esta carpeta:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows.ps1
python app.py
```

Abrí `http://127.0.0.1:5000` en el navegador. La primera ejecución crea automáticamente la base de datos SQLite.

## Usarlo desde un teléfono en la misma red Wi-Fi

No hace falta una nube para la demostración. Ejecutá la aplicación permitiendo conexiones de la red local:

```powershell
$env:APP_HOST = "0.0.0.0"
python app.py
```

En la computadora, ejecutá `ipconfig` y buscá la dirección IPv4 de la red Wi-Fi, por ejemplo `192.168.1.25`. Desde el teléfono, conectado al mismo Wi-Fi, abrí `http://192.168.1.25:5000`. Windows puede pedir permiso para el firewall: habilitalo solamente en redes privadas.

En la carga de personal y en el molinete hay una opción para tomar o seleccionar una foto desde el teléfono. Esta alternativa funciona aun cuando el navegador no permite la cámara en vivo por falta de HTTPS.

El instalador de Windows usa el wheel precompilado `dlib-bin` porque `face_recognition` depende de `dlib` y su instalación oficial intenta compilar C++ en Windows.

## Los dos scripts requeridos

### Comparar dos imágenes

```powershell
python comparar_rostros.py ruta\persona_1.jpg ruta\persona_2.jpg
```

El script detecta exactamente un rostro por imagen, calcula sus codificaciones, informa la distancia facial y muestra ambas imágenes con el resultado.

### Control de asistencia

1. Copiá fotos individuales a `empleados/`.
2. Nombrá cada archivo con el nombre del empleado, por ejemplo `Ana_Perez.jpg`.
3. Ejecutá:

```powershell
python control_asistencia.py
```

La cámara marca los rostros reconocidos y escribe una asistencia diaria por persona en `asistencia.csv`. Presioná `Q` para cerrar.

## Decisiones de diseño

SQLite es la mejor opción para la demo: no necesita usuario, contraseña, hosting ni conexión de red. Para una fase posterior con varios molinetes simultáneos, se migraría a PostgreSQL y se protegerían los templates biométricos con cifrado y controles de acceso.

El vector facial se guarda como `face_encoding`, no como hash: `face_recognition`, basado en `dlib`, produce una codificación de 128 valores y compara su distancia euclídea. El proyecto usa una tolerancia de `0.50` para ser más estricto que el valor predeterminado de la librería.

## Datos que no se suben al repositorio

La base SQLite y las imágenes usadas para enrolamiento se generan en `data/` y `uploads/`; ambos directorios están ignorados por Git porque contienen información personal y biométrica de prueba.
