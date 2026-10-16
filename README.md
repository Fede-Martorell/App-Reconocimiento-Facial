# Sistema de Asistencias para Empresas

Panel web para administrar empleados y registrar su primer ingreso del día mediante reconocimiento facial. Incluye los dos scripts de la consigna: comparación de imágenes y asistencia en tiempo real por webcam.

## Instalación y ejecución

En Windows, con Python 3.10 o superior, desde PowerShell en esta carpeta:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows.ps1
.\.venv\Scripts\python.exe app.py
```

Abrir **http://127.0.0.1:5000**. El instalador crea `.venv` e instala `requirements.txt`. Si dlib necesita compilarse, se requieren CMake y Visual Studio Build Tools con **Desarrollo de escritorio con C++**.

Instalación manual:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Uso del panel

1. **Personal:** cargar nombre, email opcional y estado del empleado. Se asigna un ID propio; dos empleados pueden tener el mismo nombre.
2. **Cargar foto:** elegir una imagen JPG o PNG con exactamente un rostro. Puede hacerse durante el alta o después. Si la foto falla, el empleado queda creado con su foto pendiente.
3. **Registrar ingreso:** capturar una imagen con la cámara del navegador o seleccionar una foto. El sistema compara solo contra empleados activos y vuelve a comprobar su estado antes de guardar.
4. **Asistencias:** consultar los ingresos, filtrar por fecha y descargar el CSV con el mismo filtro.
5. **Panel:** revisar cantidades de empleados y las últimas verificaciones. Un intento no identificado se guarda como auditoría y no genera asistencia.

Desactivar un empleado mantiene su historial e impide nuevos registros. Actualizar una foto reemplaza su vector facial únicamente cuando la nueva foto se procesó correctamente. Las fotografías nuevas no se almacenan: se guarda su codificación en SQLite.

## Los dos scripts de la consigna

### Comparación de dos imágenes

```powershell
.\.venv\Scripts\python.exe comparar_rostros.py "C:\fotos\control.jpg" "C:\fotos\prueba.jpg"
```

Cada imagen debe contener exactamente un rostro. Se muestran ambas con recuadros, coincidencia y distancia. Presionar cualquier tecla para cerrar. La tolerancia inicial es `0.6`; puede ajustarse con `--tolerancia 0.5`. La distancia no es un porcentaje: un valor menor indica mayor similitud.

### Asistencia por webcam con los empleados del panel

```powershell
.\.venv\Scripts\python.exe asistencia.py
```

El programa usa los empleados de SQLite y el mismo registro CSV que la web. Lee sus perfiles activos en cada fotograma procesado: las altas, fotos y cambios de estado del panel se reflejan sin reiniciar la cámara. **Q** o **Escape** cierran y liberan la cámara; `--camara 1` permite seleccionar otro dispositivo.

### Alternativa de carpeta para la consigna

Colocar una foto individual por empleado en `empleados/`, por ejemplo `Ana_Perez.jpg`. El nombre del archivo se muestra como `Ana Perez`.

```powershell
.\.venv\Scripts\python.exe asistencia.py --fuente carpeta --empleados empleados --csv data/asistencias_carpeta.csv
```

Este modo es independiente del padrón del panel y usa identidades con prefijo `archivo:`. Usar nombres únicos y reiniciar al cambiar las fotos. El CSV separado permite probarlo sin mezclar el padrón de carpeta con el de la empresa.

## Organización del código

| Archivo o carpeta | Responsabilidad |
|---|---|
| `app.py` | Crear la aplicación Flask, recibir formularios y devolver páginas o descargas. |
| `services.py` | Validar empleados, enrolar fotos, identificar personas y aplicar reglas de asistencia. |
| `database.py` | Crear SQLite y concentrar las consultas en `EmployeeRepository`. |
| `face_recognition_engine.py` | Leer imágenes, convertir BGR a RGB, detectar, codificar, comparar y dibujar rostros. |
| `attendance_log.py` | Leer y escribir CSV; impedir duplicados por empleado y día. |
| `asistencia.py` | Capturar fotogramas de webcam, reconocer y dibujar nombres. |
| `comparar_rostros.py` | Comparar dos fotografías y mostrar coincidencia y distancia. |
| `templates/` | Plantillas HTML del panel. |
| `static/` | Estilos y JavaScript de captura de cámara. |
| `tests/` | Pruebas de reglas, persistencia, panel y webcam. |

**Flujo web:** formulario → ruta de `app.py` → `AttendanceService` → motor facial, repositorio y CSV → respuesta HTML.

**Flujo webcam:** captura → detección → perfiles activos → mejor coincidencia → la misma regla de registro → nombre y recuadro en pantalla.

Las rutas no contienen SQL. El servicio no depende de Flask. El motor facial no conoce formularios ni bases de datos. Esto permite modificar cada parte y probarla sin abrir la cámara.

## Datos y reglas

- `data/facial_access.db`: empleados, codificaciones faciales e historial de verificaciones web.
- `data/asistencias.csv`: primer ingreso de cada empleado por día, con fecha y hora local del equipo.
- Se registra por **ID y fecha**, por lo que un nombre repetido no mezcla personas. Un ingreso desde la web y otro desde webcam el mismo día producen una sola fila.
- El CSV está protegido por un bloqueo entre procesos. La web y la webcam pueden utilizarlo simultáneamente.
- Los CSV anteriores con columnas `empleado_id,nombre,fecha,hora,origen` siguen siendo compatibles. Un CSV de tres columnas debe conservarse aparte y se puede elegir un archivo nuevo con `--csv`.
- La carpeta `data/`, las fotos de empleados, las cargas antiguas y `.env` están excluidos de Git.

```csv
empleado_id,nombre,fecha,hora,origen
1,Ana Perez,2026-10-16,09:15:30,web
```

Se usa **un solo motor: face_recognition/dlib**, con vectores de 128 valores, en la web y en ambos scripts. Las codificaciones antiguas de InsightFace se conservan en la base pero aparecen como pendientes: hay que volver a cargar la foto. Sus vectores y umbrales son diferentes y no se convierten automáticamente.

## Verificación

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Las pruebas usan bases y CSV temporales, cámara simulada y respuestas faciales controladas. Cubren registro diario, concurrencia, nombres repetidos, estado activo, carga y actualización de fotos, filtrado, descarga, formularios y errores de escritura. Para validar la detección real, instalar dlib y ejecutar ambos scripts con fotos y webcam.

## Evolución del proyecto

La implementación actual sirve como prototipo local para una empresa. La base para ampliarlo está separada por responsabilidades. Los próximos pasos para un uso empresarial real son cuentas de administrador y roles, configuración de empresa y sucursales, horarios y reportes, y despliegue con HTTPS. Actualmente no hay inicio de sesión ni prueba de vida; el servidor se inicia solo en `127.0.0.1` y no debe exponerse como sistema de producción.

La fábrica `create_app(config)` permite configurar `DATABASE_PATH`, `ATTENDANCE_CSV` y `FACE_TOLERANCE`. `FLASK_SECRET_KEY` permite mantener la clave de sesión entre reinicios. El modo debug permanece desactivado salvo que se configure `FLASK_DEBUG=1`.
