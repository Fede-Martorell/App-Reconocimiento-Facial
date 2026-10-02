# Control de acceso con reconocimiento facial - Sprint 1

Prototipo local para administrar personal autorizado, registrar biometrías faciales y verificar el acceso desde una cámara web. Los datos quedan guardados en SQLite (`data/facial_access.db`), por lo que no hace falta instalar ni conectar un servidor de base de datos.

## Alcance del sprint

- Panel de administrador: alta de personal y activación/desactivación de acceso.
- Enrolamiento con una foto que contenga exactamente un rostro.
- Simulador de molinete desde el navegador usando la cámara.
- Registro persistente de accesos permitidos y denegados.
- Solo las personas activas y con biometría cargada pueden ingresar.

## Cómo ejecutarlo

Requiere Python 3.10 o superior. En PowerShell, dentro de esta carpeta:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
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

El comando anterior instala el panel y SQLite, que es todo lo necesario para administrar personal desde el navegador.

### Reconocimiento facial real (segundo paso)

Para evitar problemas de compilación de `dlib` en Windows, el proyecto usa InsightFace y ONNX Runtime. Instalá las dependencias de visión por separado:

```powershell
pip install -r requirements-vision.txt
```

La primera carga de biometría descarga el modelo de reconocimiento; mantené la conexión a Internet durante ese paso. Hasta completar la instalación, el panel, SQLite, altas, bajas y registro de accesos funcionan.

## Decisiones de diseño

SQLite es la mejor opción para la demo: no necesita usuario, contraseña, hosting ni conexión de red. Para una fase posterior con varios molinetes simultáneos, se migraría a PostgreSQL y se protegerían los templates biométricos con cifrado y controles de acceso.

El vector facial se guarda como `face_encoding`, no como hash: un encoding de reconocimiento facial es un vector numérico y no un hash criptográfico.

## Datos que no se suben al repositorio

La base SQLite y las imágenes usadas para enrolamiento se generan en `data/` y `uploads/`; ambos directorios están ignorados por Git porque contienen información personal y biométrica de prueba.
