# Guía de exposición para 5 integrantes

## Objetivo de la presentación

Presentar el Sprint 1 de un sistema de control de acceso facial para una empresa. El sistema permite registrar empleados, cargar su biometría, activar o revocar permisos y verificar el acceso desde una computadora o teléfono.

La consigna obligatoria se demuestra con dos programas independientes: `comparar_rostros.py`, que compara dos imágenes, y `control_asistencia.py`, que reconoce empleados por cámara y genera `asistencia.csv`. El panel web es una extensión de esos conceptos. También se incluye `asistencia.py`, con integración al padrón del panel y al CSV compartido; consultar README.md para elegir la variante.

**Duración sugerida:** 10 a 12 minutos más preguntas.

## Preparación antes de exponer

1. Inicien la aplicación y comprueben que abre el panel.
2. Tengan una persona activa con biometría cargada.
3. Tengan otra persona que puedan desactivar durante la demo.
4. Abran en el celular la pantalla del molinete usando la IP local de la computadora.
5. Tengan abiertas las pestañas **Panel**, **Personal** y **Molinete**.
6. Prueben antes la cámara, los dos scripts y el acceso desde el teléfono.

---

## Integrante 1: problema, alcance y comparación de imágenes

**Tiempo:** 2 minutos.

### Qué decir

> Nuestro problema es reemplazar las tarjetas físicas de acceso, que pueden perderse o prestarse. Proponemos un prototipo de reconocimiento facial para controlar el ingreso de empleados.

> En este Sprint 1 nos enfocamos en el flujo principal: administrar empleados, enrolar su rostro, permitir o bloquear su acceso y registrar cada intento. Decidimos no incluir todavía visitantes con QR, correos, balanceo de carga ni anti-spoofing real, porque son funcionalidades de los siguientes sprints.

> El criterio central de negocio es que una persona solo puede ingresar si el sistema la reconoce y además su estado está activo.

> El primer script requerido recibe dos rutas de imagen. OpenCV carga cada archivo y convierte BGR a RGB; face_recognition localiza un rostro, genera una codificación de 128 valores y calcula la distancia facial. Con `compare_faces` y tolerancia inicial 0.60 decide si coinciden. El resultado aparece en consola y sobre una ventana con ambas imágenes.

### Qué mostrar

- El panel principal.
- Métricas de personal registrado, activo y biometrías cargadas.
- Ejecutar `python comparar_rostros.py imagen_1.jpg imagen_2.jpg`.

### Si preguntan por qué el alcance es acotado

> Priorizamos una entrega vertical y demostrable: desde el alta hasta el registro de acceso. Eso reduce riesgo técnico y nos deja una base para extender el sistema en los siguientes sprints.

---

## Integrante 2: arquitectura y tecnologías

**Tiempo:** 2 minutos.

### Qué decir

> La arquitectura es local y tiene tres capas. El navegador o teléfono toma o sube una imagen. Flask recibe esa solicitud y aplica las reglas de negocio. Por último, SQLite persiste empleados, biometrías y registros de acceso.

```text
Teléfono o navegador
        |
        v
Flask: interfaz y lógica de negocio
        |
        +--> SQLite: datos y auditoría
        |
        +--> InsightFace + ONNX Runtime: motor del panel
        |
        +--> face_recognition + dlib: scripts académicos
```

> Usamos InsightFace y ONNX Runtime en el panel para conservar las biometrías existentes. En los scripts académicos usamos face_recognition y dlib. Usamos Flask para las rutas web y formularios; SQLite porque no requiere un servidor separado; OpenCV para imágenes y cámara; face_recognition para localizar, codificar y comparar rostros; dlib como motor interno; os para archivos y carpetas; NumPy para operaciones matemáticas; y datetime para registrar fecha y hora.

> Elegimos SQLite para el Sprint 1 porque el proyecto funciona en una sola computadora y no requiere instalar MySQL ni PostgreSQL. Para varios molinetes simultáneos migraríamos a PostgreSQL.

### Qué mostrar

- [app.py](app.py), solo para señalar que Flask conecta la interfaz, base y motor facial.
- [database.py](database.py), solo las tablas, sin leer todo el código.

### Pregunta probable: ¿por qué no una API en la nube?

> Procesamos localmente para reducir dependencia de Internet y evitar enviar datos biométricos a un tercero. La única descarga externa es el modelo la primera vez.

---

## Integrante 3: base de datos y panel administrador

**Tiempo:** 2 minutos.

### Qué decir

> El modelo de datos tiene tres entidades. `employees` guarda los datos básicos y el estado. `biometric_profiles` guarda la representación facial y se relaciona uno a uno con el empleado. `access_logs` audita cada intento de entrada.

```text
employees 1 ─── 0..1 biometric_profiles
employees 1 ─── N access_logs
```

> Un perfil biométrico tiene `employee_id` único, por lo que un empleado posee como máximo un perfil activo. Las claves foráneas mantienen la integridad: no se puede guardar una biometría para un empleado inexistente.

> El panel permite alta, activación y desactivación. La desactivación no depende de borrar al empleado: cambia el estado a `inactive`, y el reconocimiento consulta solo empleados activos. Por eso el bloqueo es inmediato en el prototipo.

### Demostración

1. Entrar a **Personal**.
2. Mostrar una persona activa y biometría cargada.
3. Presionar **Desactivar**.
4. Explicar que ya no se incluirá en la búsqueda facial.

### Pregunta probable: ¿cómo evitan SQL injection?

> Usamos consultas parametrizadas con placeholders `?`, por ejemplo `WHERE id = ?`, en lugar de concatenar texto ingresado por el usuario en la consulta SQL.

---

## Integrante 4: enrolamiento, fotos y biometría

**Tiempo:** 2 a 3 minutos.

### Qué decir

> El enrolamiento empieza al cargar una foto JPG o PNG. El formulario usa `multipart/form-data`, por lo que Flask recibe el archivo como binario. En celular usamos `capture="user"` para sugerir la cámara frontal.

> Validamos que exista un archivo, limitamos el tamaño a 5 MB y aceptamos JPG o PNG. También usamos `secure_filename` para evitar que el nombre de archivo intente escribir fuera de la carpeta de cargas.

> La foto se guarda localmente en `uploads/` y se procesa con OpenCV e InsightFace en el panel. Exigimos exactamente un rostro: si no hay rostros o hay más de uno, se rechaza la imagen para no enrolar datos ambiguos.

> El resultado no es un hash. El panel genera un **embedding normalizado de 512 valores** mediante InsightFace. Los scripts académicos generan codificaciones de **128 valores** con face_recognition; ambos tipos se mantienen separados. Ese vector se serializa con NumPy y se guarda como BLOB en SQLite.

### Demostración

1. Presionar **Cargar personal** o **Cargar biometría**.
2. Tomar una foto desde el teléfono o seleccionar una imagen.
3. Mostrar el estado “Biometría cargada”.

### Frase importante

> No decimos que almacenamos un hash facial: almacenamos un embedding. Un hash criptográfico no permite medir parecido; un embedding sí permite comparar similitud entre rostros.

### Pregunta probable: ¿las fotos se suben a GitHub?

> No. `uploads/`, la base de datos local y el entorno virtual están en `.gitignore`. No se versionan datos biométricos de prueba.

---

## Integrante 5: reconocimiento, asistencia y auditoría

**Tiempo:** 2 a 3 minutos.

### Qué decir

> Para verificar un acceso, el usuario toma una foto desde la cámara o la sube desde el celular. La aplicación obtiene el embedding de ese rostro y consulta solamente embeddings de empleados activos.

> En el panel comparamos embeddings normalizados mediante similitud coseno. Elegimos la mayor similitud y exigimos al menos 0.40. La distancia mostrada es 1 menos la similitud. Los scripts independientes usan distancia euclídea con face_recognition; sus umbrales no son intercambiables.

```text
Foto de acceso
  → embedding candidato
  → comparación con perfiles activos
  → mayor similitud >= umbral 0.40 (panel)
  → acceso permitido o denegado
  → registro en access_logs
```

> Si no hay coincidencia suficiente, si la persona está inactiva o si la imagen no contiene exactamente un rostro, se deniega el acceso. Tanto los permitidos como los denegados quedan registrados con fecha y detalle.

> El segundo script obligatorio carga las fotos de `empleados/`. Usa `os.listdir` para recorrerlas y extrae cada nombre del archivo. Luego OpenCV captura fotogramas de la webcam, face_recognition codifica los rostros y NumPy encuentra la menor distancia. Si reconoce a alguien, datetime aporta fecha y hora y el módulo estándar csv agrega la asistencia a `asistencia.csv`. Se registra una sola vez por persona y por día.

### Demostración

1. Ir al **Molinete** desde el teléfono.
2. Tomar o seleccionar una foto de la persona activa: mostrar “Acceso permitido”.
3. Volver a desactivar a la persona, repetir: mostrar “Acceso denegado”.
4. Abrir el panel y mostrar los dos eventos en el historial.
5. Ejecutar `python control_asistencia.py`, reconocer a una persona y abrir `asistencia.csv`.

### Pregunta probable: ¿0.50 asegura que nunca haya falsos positivos?

> No. Es un umbral inicial para el prototipo. Una versión productiva debe calibrarlo con un conjunto de pruebas representativo y medir falsas aceptaciones, falsos rechazos, precisión y tiempo de respuesta.

---

## Conceptos que todos deben saber

| Concepto | Respuesta breve |
| --- | --- |
| Flask | Framework web de Python que define rutas, recibe formularios y renderiza HTML. |
| SQLite | Base de datos en un archivo local, sin servidor adicional. |
| OpenCV | Librería para leer y procesar imágenes. |
| face_recognition | API que localiza, codifica y compara rostros usando dlib. |
| dlib | Motor de aprendizaje automático usado internamente por face_recognition. |
| os | Manejo portable de carpetas, nombres y rutas de archivos. |
| datetime | Obtención de fecha y hora para asistencias y accesos. |
| Embedding | Vector numérico que representa rasgos faciales para comparar similitud. |
| BLOB | Campo de base de datos para guardar datos binarios; aquí contiene el vector serializado. |
| Distancia euclídea | Distancia entre dos codificaciones; un valor menor indica mayor parecido. |
| Enrolamiento | Proceso de registrar una foto y generar la biometría de una persona. |

## Límites del Sprint 1

No oculten estos límites; mencionarlos demuestra criterio técnico.

- No hay liveness detection: una foto podría intentar engañar al sistema.
- No hay visitantes, QR, correos ni vencimientos temporales.
- No hay autenticación de administrador ni HTTPS para una publicación pública.
- Las codificaciones biométricas no están cifradas aún.
- La desactivación excluye al empleado de la búsqueda; el borrado irreversible del perfil biométrico queda para otro sprint.
- El modo debug está desactivado por defecto y solo se habilita con FLASK_DEBUG=1 para desarrollo.

## Cierre sugerido

> En conclusión, el Sprint 1 entrega un flujo completo de control de acceso: administración de personal, enrolamiento biométrico, validación facial, revocación inmediata por estado y auditoría de eventos. La siguiente etapa incorporaría anti-spoofing, visitantes temporales, QR, seguridad de datos y despliegue con HTTPS.
