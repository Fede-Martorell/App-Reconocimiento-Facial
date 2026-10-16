# Verificación del prototipo — 2 de octubre de 2026

El panel administrativo y la persistencia básica funcionan en las pruebas ejecutadas. No se puede afirmar que toda la aplicación funcione: hay defectos reproducibles y el reconocimiento con personas reales sigue sin verificar.

## Método y alcance

Se ejecutaron 34 comprobaciones: 28 satisfactorias y 6 con fallos o controles ausentes. Se usaron el cliente HTTP de Flask, SQLite en un directorio temporal y datos ficticios. No se modificó el código de la aplicación ni se cargaron empleados en su base habitual.

Se descargó Flask 3.1.3 con sus dependencias en `.venv/audit-packages`, una carpeta ignorada por Git. El script de comprobación quedó en `.venv/audit_checks.py`; esa carpeta no es un entorno virtual completo. Se utilizó el Python 3.12 incluido en Codex porque `python` y `py` no están disponibles en el PATH de esta sesión.

Las pruebas de decisiones faciales emplearon vectores sintéticos, las de enrolamiento exitoso simularon la extracción y las de cantidad de rostros simularon el detector. Esto verifica la lógica que rodea al reconocimiento, pero no la detección real, la precisión del modelo ni la cámara. No se ejecutó una inspección visual del navegador.

## Funciones verificadas

- Sintaxis de los tres módulos Python e inicialización repetible de SQLite.
- Respuestas HTTP 200 del panel, listado de personal, formulario de alta, molinete y hoja de estilos, después de inicializar la base.
- Alta persistente de personal, eliminación de espacios exteriores del nombre y rechazo de nombre vacío, estado inválido y correo duplicado.
- Desactivación y reactivación, incluida la fecha de desactivación.
- Manejo de empleado inexistente, enrolamiento sin foto, extensión incorrecta y ausencia de dependencias de visión.
- Guardado y reemplazo del vector biométrico sin duplicar perfiles, con extracción simulada.
- Registro de acceso denegado sin captura y ante un Base64 malformado.
- Acceso permitido para un empleado activo con coincidencia; denegado para desconocidos e inactivos, con vectores simulados.
- Rechazo de solicitudes que superan el límite de carga mediante HTTP 413.
- Rechazo de cero o dos rostros con detector simulado.
- Integridad de la base SQLite de prueba.

La prueba de una imagen vacía solo confirmó la respuesta cuando faltan las dependencias de visión. No demuestra el comportamiento de OpenCV ante ese archivo.

## Hallazgos reproducidos

| Prioridad | Hallazgo | Evidencia e impacto |
|---|---|---|
| Alta al compartir la app | Administración sin autenticación | `GET /employees` anónimo devuelve 200 y un POST puede cambiar el estado de un empleado. Cualquier persona con acceso a la app puede administrar el personal. |
| Alta al compartir la app | Formularios sin protección CSRF | `POST /employees/1/toggle-status` sin token cambia el estado. Falta un control que impida acciones inducidas desde otra página. |
| Media | Arranque por importación no inicializa la base | En una base nueva, importar la app y pedir `/` produce `OperationalError: no such table: employees`. La inicialización solo está dentro de `if __name__ == '__main__'` en `app.py`. El procedimiento documentado con `python app.py` sí contempla esa inicialización; Flask CLI y servidores que importan la app no. |
| Media | Fallos inesperados del detector generan HTTP 500 | Al simular un `RuntimeError` durante el enrolamiento, `/employees/1/enroll` devuelve 500. Solo se manejan `ValueError` y `RecognitionUnavailable` en esa ruta. |
| Media | Conexiones SQLite sin cierre explícito | La conexión sigue utilizable después de `query_all`. El contexto de SQLite finaliza la transacción, pero no cierra la conexión. La limpieza inicial de la base temporal falló en Windows por un archivo abierto; la prueba pudo limpiar después de forzar la recolección de objetos. |
| Baja | Fotos anteriores acumuladas | Tras dos enrolamientos hay un solo perfil y dos imágenes en disco. Actualizar el perfil no elimina su foto anterior. |

## Observaciones del código

- La ejecución directa habilita `debug=True`, incluso cuando `APP_HOST` permite conexiones desde la red local. Debe configurarse antes de compartir la aplicación.
- La clave de sesión tiene un valor predeterminado fijo; configurar `FLASK_SECRET_KEY` para cualquier uso compartido.
- El botón de captura no espera a que el video tenga dimensiones válidas. Queda pendiente probar el clic antes de que la cámara esté lista.
- No se implementa prueba de vida: el flujo acepta fotografías. El prototipo no verifica que una persona esté físicamente frente al dispositivo.
- No hay una suite de pruebas versionada en el repositorio original.

## Verificaciones pendientes

1. Instalar y comprobar `requirements-vision.txt` en un entorno de desarrollo. En esta sesión no estaban instalados OpenCV, InsightFace ni ONNX Runtime. El requisito `insightface>=2.0` existe actualmente; su documentación declara instalación base de ONNX Runtime y descarga inicial de modelos: [paquete oficial en PyPI](https://pypi.org/project/insightface/).
2. Descargar y cargar el modelo `buffalo_l`, y enrolar una fotografía real con un solo rostro.
3. Probar con fotografías distintas de la misma persona y de otras personas, además de imágenes sin rostros o con varios rostros. Evaluar el umbral de similitud de 0,40; estas pruebas no validaron su precisión.
4. Verificar permisos de cámara, captura y carga alternativa en computadora y teléfono, y revisar visualmente la interfaz.
5. Corregir los hallazgos y repetir los casos afectados antes de ampliar funcionalidades.

La base del prototipo permite seguir trabajando, pero todavía no está validado el flujo completo de reconocimiento facial ni el uso como control de acceso real.
