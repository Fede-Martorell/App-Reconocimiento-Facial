from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted, Flowable, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/pdf/Guia_de_estudio_y_defensa_Sprint_1.pdf'
pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialBold', 'C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFont(TTFont('ArialItalic', 'C:/Windows/Fonts/ariali.ttf'))
pdfmetrics.registerFontFamily('Arial', normal='Arial', bold='ArialBold', italic='ArialItalic', boldItalic='ArialBold')
NAVY = colors.HexColor('#142D46')
BLUE = colors.HexColor('#215DAD')
TEAL = colors.HexColor('#087F8C')
INK = colors.HexColor('#24364B')
GRAY = colors.HexColor('#526478')
PALE = colors.HexColor('#EFF5FA')
W = A4[0] - 92
styles = {
 'body': ParagraphStyle('body', fontName='Arial', fontSize=10, leading=14, textColor=INK, spaceAfter=7),
 'small': ParagraphStyle('small', fontName='Arial', fontSize=9, leading=12.5, textColor=GRAY, spaceAfter=6),
 'title': ParagraphStyle('title', fontName='ArialBold', fontSize=26, leading=31, textColor=NAVY, spaceAfter=17),
 'h1': ParagraphStyle('h1', fontName='ArialBold', fontSize=21, leading=26, textColor=NAVY, spaceAfter=15),
 'h2': ParagraphStyle('h2', fontName='ArialBold', fontSize=12, leading=16, textColor=BLUE, spaceBefore=7, spaceAfter=6),
 'quote': ParagraphStyle('quote', fontName='ArialItalic', fontSize=10.3, leading=15.3, textColor=NAVY, spaceAfter=3),
 'cell': ParagraphStyle('cell', fontName='Arial', fontSize=9.2, leading=12, textColor=INK),
 'cellhead': ParagraphStyle('cellhead', fontName='ArialBold', fontSize=9.2, leading=12.5, textColor=colors.white),
 'code': ParagraphStyle('code', fontName='Courier', fontSize=8.7, leading=12, textColor=NAVY, backColor=PALE, borderPadding=10, spaceBefore=6, spaceAfter=13),
}
story=[]
titles=[]
def p(text,style='body'):
    return Paragraph(text,styles[style])
def add(text,style='body'):
    story.append(p(text,style))
def h(text): add(text,'h2')
def bullets(items):
    for item in items: add('• '+item)
def code(text): story.append(Preformatted(text,styles['code']))
def box(text,label='IDEA PARA RECORDAR'):
    table=Table([[p(label,'h2')],[p(text)]],colWidths=[W-22])
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('BOX',(0,0),(-1,-1),0.6,colors.HexColor('#D4E2ED')),('LEFTPADDING',(0,0),(-1,-1),11),('RIGHTPADDING',(0,0),(-1,-1),11),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story.extend([table,Spacer(1,10)])
def table(headers,rows,widths):
    data=[[p(escape(x),'cellhead') for x in headers]]+[[p(x,'cell') for x in row] for row in rows]
    t=Table(data,colWidths=[W*x for x in widths],repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),0.6,NAVY)]))
    story.extend([t,Spacer(1,10)])
def page(title):
    if titles: story.append(PageBreak())
    titles.append(title)
    add(f'{len(titles):02d} / SPRINT 1','small')
    add(title,'h1')
class Flow(Flowable):
    def __init__(self,labels): super().__init__(); self.labels=labels; self.width=W; self.height=77
    def draw(self):
        c=self.canv; gap=14; bw=(W-gap*(len(self.labels)-1))/len(self.labels)
        for i,lines in enumerate(self.labels):
            x=i*(bw+gap)
            c.setFillColor(PALE); c.setStrokeColor(colors.HexColor('#BCD0E2')); c.roundRect(x,22,bw,48,5,fill=1,stroke=1)
            c.setFillColor(NAVY); c.setFont('ArialBold',9)
            for j,line in enumerate(lines): c.drawCentredString(x+bw/2,52-j*13,line)
            if i < len(self.labels)-1:
                c.setStrokeColor(TEAL); c.line(x+bw+2,46,x+bw+gap-2,46); c.line(x+bw+gap-5,49,x+bw+gap-2,46); c.line(x+bw+gap-5,43,x+bw+gap-2,46)

page('Guía de estudio y defensa')
add('App de reconocimiento facial','title')
add('Entender el proyecto, recorrer el código y explicar el Sprint 1 con tus propias palabras.','body')
box('El sistema recibe una imagen, obtiene un vector facial, lo compara con los perfiles del personal activo y registra la decisión. El panel administra los datos que hacen posible ese recorrido.','EL PROYECTO EN UNA FRASE')
h('Cómo usar esta guía')
bullets(['<b>Primera lectura:</b> seguí el recorrido completo de las páginas 2 a 7.','<b>Segunda lectura:</b> abrí el código y ubicá las funciones mencionadas.','<b>Antes de exponer:</b> repasá el estado real del sprint, el guion y las preguntas.','<b>Para comprobar que entendiste:</b> resolvé los ejercicios sin mirar las respuestas.'])
table(['Contenido','Página'],[
 ['Arquitectura, archivos y rutas','2'],['Administración y estados del personal','3'],['Enrolamiento y embeddings','4'],['SQLite y relaciones entre tablas','5'],['Comparación y decisión de acceso','6'],['Cámara, formularios y errores','7'],['Qué se probó y qué queda pendiente','8'],['Guion para cinco integrantes','9'],['Preguntas frecuentes de la defensa','10'],['Ejercicios con respuestas','11'],['Repaso rápido y mapa de código','12']], [.86,.14])
add('<b>Versión:</b> 5 de octubre de 2026. Basada en el código local y en la verificación del 2 de octubre. No se ejecutaron nuevas pruebas funcionales al crear esta guía.','small')

page('Arquitectura: quién hace qué')
add('La aplicación separa la presentación, la coordinación del flujo, la persistencia y el procesamiento facial. Una acción en el navegador llega a una ruta de Flask. Esa ruta llama a los módulos necesarios y devuelve una página.')
story.append(Flow([['Navegador','HTML + JS'],['Flask','app.py'],['SQLite / motor','Datos + IA']]))
table(['Archivo o carpeta','Responsabilidad'],[
 ['<b>app.py</b>','Rutas, validaciones, carga de archivos, cambios de estado y registros de acceso.'],
 ['<b>database.py</b>','Conectar con SQLite, crear tablas y ejecutar consultas.'],
 ['<b>recognition_engine.py</b>','Cargar el modelo, extraer embeddings y buscar la mejor coincidencia.'],
 ['<b>templates/</b>','Páginas HTML con Jinja; muestran datos enviados por Flask.'],
 ['<b>static/style.css</b>','Colores, distribución y adaptación de la interfaz a pantallas pequeñas.'],
 ['<b>data/ y uploads/</b>','Base local y fotografías guardadas. Se excluyen de Git.']], [.34,.66])
h('Las rutas principales')
table(['Ruta','Método y operación'],[
 ['<b>/</b>','GET: métricas y últimos ocho accesos.'],['<b>/employees</b>','GET: listado de personal y estado de biometría.'],['<b>/employees/new</b>','GET: formulario. POST: registrar persona.'],['<b>/employees/&lt;id&gt;/enroll</b>','GET: formulario. POST: crear o actualizar biometría.'],['<b>/employees/&lt;id&gt;/toggle-status</b>','POST: alternar activo e inactivo.'],['<b>/access</b>','GET: mostrar molinete. POST: verificar imagen.']], [.48,.52])
box('<b>GET</b> consulta o muestra información. <b>POST</b> envía datos para realizar una operación. Una ruta es la dirección que conecta la solicitud del navegador con una función de Flask.')
add('<b>Para decirlo:</b> “Flask coordina el flujo; el motor facial calcula la coincidencia; SQLite conserva los datos; los templates muestran el resultado”.','quote')

page('Administración y estados del personal')
h('Qué ocurre al guardar una persona')
bullets(['El formulario envía nombre, correo opcional, estado y una foto opcional.','<b>new_employee()</b> lee los datos; <b>.strip()</b> quita espacios exteriores.','Rechaza el nombre vacío y los estados distintos de <b>active</b> e <b>inactive</b>.','Inserta el empleado en SQLite y obtiene su ID con <b>cursor.lastrowid</b>.','Si hay foto, intenta crear la biometría. Si no hay foto, el empleado queda registrado con enrolamiento pendiente.'])
code('full_name = request.form.get("full_name", "").strip()\nemail = request.form.get("email", "").strip() or None\nphoto = request.files.get("photo")')
add('<b>request.form</b> lee texto del formulario. <b>request.files</b> lee archivos. El correo vacío se guarda como NULL; si se informa, la base exige que sea único.')
h('Tres condiciones que no son equivalentes')
table(['Condición','Significado','¿Alcanza para ingresar?'],[
 ['Registrado','Existe el empleado en la base.','No.'],['Activo','Está habilitado para ser considerado en la búsqueda.','No: necesita biometría.'],['Enrolado','Tiene un vector facial guardado.','No: necesita estar activo y coincidir.']], [.20,.52,.28])
h('Activación y desactivación')
add('<b>toggle_status()</b> busca al empleado, alterna su estado y actualiza <b>deactivated_at</b>. Al desactivarlo registra una fecha; al reactivarlo la limpia. No elimina al empleado ni su perfil facial.')
box('Un empleado inactivo queda excluido de la búsqueda de candidatos autorizados. La desactivación impide usar su propio perfil para obtener autorización; no equivale a borrar sus datos.','REGLA DE NEGOCIO')
add('<b>Caso concreto:</b> Ana se registra sin foto. Aparece en Personal, pero todavía no puede ser reconocida. Después carga su biometría. Si la desactivan, deja de ser candidata autorizada.')
add('<b>Matiz:</b> ante un error controlado al cargar la foto, la app conserva el empleado para completar el enrolamiento después. El alta y la biometría no son una única transacción atómica.','small')

page('Enrolamiento: de foto a vector')
add('Enrolar es asociar una representación facial a un empleado. La función <b>save_biometric_profile()</b> valida y guarda el archivo, llama al motor y actualiza el perfil en SQLite.')
story.append(Flow([['Foto','JPG / PNG'],['OpenCV','Lee imagen'],['InsightFace','Embedding'],['NumPy','Bytes']]))
h('El recorrido del código')
bullets(['La app comprueba que haya archivo y que su extensión sea JPG, JPEG o PNG.','Usa el ID, una fecha y <b>secure_filename()</b> para construir el nombre dentro de uploads/.','<b>cv2.imread()</b> intenta leer el contenido. Si no puede, se rechaza la imagen.','<b>_one_embedding()</b> exige exactamente un rostro y obtiene <b>normed_embedding</b>.','<b>np.save(..., allow_pickle=False)</b> serializa el vector; la app lo guarda como BLOB.'])
code('faces = _get_model().get(image)\nif len(faces) != 1:\n    raise ValueError("La imagen debe contener exactamente un rostro.")\nreturn faces[0].normed_embedding.astype(np.float32)')
h('Qué es un embedding')
add('Es un vector numérico producido por un modelo entrenado. Sirve para comparar características faciales. Dos fotos de la misma persona pueden generar vectores diferentes, pero suficientemente parecidos.')
box('<b>Detección:</b> localizar un rostro en la imagen.<br/><b>Reconocimiento:</b> compararlo con perfiles conocidos.<br/><b>Embedding:</b> representación numérica para comparar.<br/><b>Hash:</b> resultado de otra clase de transformación; no es lo que guarda esta app.','CUATRO CONCEPTOS')
h('El modelo y los archivos')
add('La configuración usa <b>FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])</b>. ONNX Runtime ejecuta los modelos en CPU. <b>_model</b> se carga de forma diferida y se reutiliza por proceso una vez preparado.')
add('La foto queda en uploads/ cuando el enrolamiento funciona. Si falla su guardado o la extracción, se intenta borrar el archivo recién usado. Actualizar el perfil reemplaza el vector, pero actualmente conserva la foto anterior.')
add('<b>Para decirlo:</b> “Guardamos un embedding facial serializado; no un hash. El modelo ya está entrenado: nuestra app lo utiliza, no lo entrena desde cero”.','quote')

page('SQLite: datos y relaciones')
add('SQLite guarda la información en <b>data/facial_access.db</b>. Para este prototipo evita configurar un servidor de base de datos. Persistir significa que los datos sobreviven al reinicio de la aplicación.')
table(['Tabla','Datos principales','Relación'],[
 ['<b>employees</b>','id, full_name, email, status, created_at, deactivated_at.','Una persona tiene cero o un perfil.'],
 ['<b>biometric_profiles</b>','employee_id, face_encoding, source_image_path, enrolled_at.','employee_id es único y referencia al empleado.'],
 ['<b>access_logs</b>','employee_id, device_name, result, detail, created_at.','Una persona puede tener muchos accesos; un intento desconocido puede tener employee_id NULL.']], [.25,.47,.28])
h('Cómo se conserva la coherencia')
bullets(['<b>PRIMARY KEY:</b> identifica cada registro mediante un ID.','<b>UNIQUE:</b> evita correos repetidos y varios perfiles para un mismo empleado.','<b>FOREIGN KEY:</b> relaciona el perfil y los accesos con un empleado válido.','<b>CHECK:</b> restringe los estados permitidos en la base.','<b>PRAGMA foreign_keys = ON:</b> activa el control de esas relaciones en cada conexión.'])
h('Consultas parametrizadas')
code('db.execute(\n    "UPDATE employees SET status = ? WHERE id = ?",\n    (new_status, employee_id),\n)')
add('Los valores se vinculan como parámetros y no se concatenan dentro del SQL. Esto evita que esos valores se interpreten como instrucciones SQL.')
h('Actualizar sin duplicar el perfil')
add('El guardado utiliza <b>INSERT ... ON CONFLICT(employee_id) DO UPDATE</b>. Si el empleado ya tiene perfil, actualiza el vector, la ruta y la fecha; si no, crea el perfil.')
box('<b>with connection</b> confirma o revierte la transacción al salir. <b>No cierra automáticamente la conexión.</b> En esta versión falta cerrar las conexiones explícitamente.','CORRECCIÓN IMPORTANTE PARA LA DEFENSA')
add('<b>BLOB</b> es almacenamiento binario. La base contiene los bytes del vector y la ruta de la foto, no el archivo JPG/PNG. <b>allow_pickle=False</b> evita cargar objetos Python mediante pickle; no cifra el vector.','small')

page('Cómo se decide el acceso')
add('<b>access()</b> recibe la imagen, selecciona los perfiles activos con biometría y llama a <b>find_match()</b>. Es una búsqueda de identificación: compara al candidato contra todos los perfiles seleccionados, no contra un único ID declarado.')
code("WHERE employees.status = 'active'\n  AND biometric_profiles.face_encoding IS NOT NULL")
h('La comparación, paso a paso')
bullets(['<b>encoding_from_bytes()</b> decodifica la imagen y genera el vector candidato.','<b>np.load(..., allow_pickle=False)</b> recupera los vectores registrados.','El producto <b>np.asarray(stored) @ candidate</b> calcula las similitudes.','<b>np.argmax()</b> elige la posición con mayor similitud.','Si esa similitud es al menos <b>0,40</b>, devuelve el ID; si no, devuelve None.'])
code('similarities = np.asarray(stored) @ candidate\nposition = int(np.argmax(similarities))\nsimilarity = float(similarities[position])\ndistance = 1.0 - similarity')
add('Los vectores están normalizados: su longitud es uno. En ese caso, su producto punto equivale a la similitud coseno. Mayor similitud implica mayor parecido en el espacio del modelo. La pantalla muestra <b>distancia = 1 - similitud</b>: una distancia menor corresponde a mayor similitud.')
h('Ejemplo ilustrativo, no medición del proyecto')
table(['Perfil activo','Similitud','Resultado de la búsqueda'],[
 ['Ana','0,78','Mayor valor: supera 0,40; devuelve su ID.'],['Bruno','0,22','No es el mejor candidato.'],['Otra imagen: mejor valor','0,31','No supera 0,40; no identifica un autorizado.']], [.33,.18,.49])
box('El umbral 0,40 no significa “40 % de certeza”. Es un corte configurado. Subirlo suele reducir aceptaciones y aumentar rechazos; bajarlo produce el efecto contrario. Su calidad debe medirse con casos reales.')
add('Una coincidencia suficiente genera <b>allowed</b>; si no existe, <b>denied</b>. El resultado se guarda con <b>write_access_log()</b>. Si no hay perfiles, se devuelve (None, None), pero el código procesa primero la imagen: puede fallar antes de llegar a esa devolución.','small')

page('Navegador, cámara y errores')
h('Dos formas de enviar una imagen')
table(['Foto subida','Captura en vivo'],[
 ['El input type="file" permite elegir una foto. capture="user" sugiere usar la cámara frontal en dispositivos compatibles.','JavaScript solicita cámara mediante getUserMedia y muestra el video.'],
 ['multipart/form-data transporta el archivo. Flask lo obtiene desde request.files.','Canvas toma un cuadro del video. toDataURL genera una URL de datos que contiene la imagen en Base64.'],
 ['El servidor lee los bytes con photo.read().','El servidor decodifica el texto con base64.b64decode().']], [.5,.5])
box('<b>Base64</b> representa bytes mediante texto. No cifra la foto, no genera el embedding y no autentica a la persona.','EVITÁ CONFUNDIR ESTOS PASOS')
h('Qué controles existen')
bullets(['El input <b>accept</b> orienta la selección; no garantiza que el archivo tenga contenido válido.','El servidor revisa la extensión y OpenCV intenta decodificar la imagen.','<b>MAX_CONTENT_LENGTH</b> limita la solicitud completa a 5 MiB, incluido el formulario.','Se controla la cantidad de rostros y se informa cuando faltan dependencias o no se prepara el modelo.'])
h('Qué devuelve Flask')
add('<b>render_template()</b> genera HTML con datos; <b>redirect()</b> envía al usuario a otra ruta; <b>url_for()</b> construye direcciones; <b>flash()</b> prepara mensajes de éxito o error. Jinja muestra esos datos dentro de los templates.')
h('Límites de este flujo')
add('La cámara depende de permisos y del contexto de seguridad del navegador. En un teléfono conectado por HTTP a una dirección de red local puede no estar disponible; la carga de archivo es una alternativa. La cámara real y el clic antes de que el video esté listo siguen sin comprobarse en nuestro entorno.')
add('El código maneja <b>ValueError</b> y <b>RecognitionUnavailable</b> en enrolamiento y acceso. Otros fallos pueden terminar en HTTP 500. El rechazo por tamaño devuelve HTTP 413; todavía no hay una página propia para explicarlo.')
add('<b>Para decirlo:</b> “La interfaz ofrece cámara y archivo. La decisión se toma en el servidor, usando la imagen recibida y los perfiles autorizados”.','quote')

page('Estado real del Sprint 1')
add('Diferenciá <b>lo implementado</b>, <b>lo probado</b> y <b>lo pendiente</b>. Tener una función escrita no demuestra que el flujo completo funcione con personas y dispositivos reales.')
h('Resultados de la revisión del 2 de octubre')
table(['Nivel de evidencia','Resultado'],[
 ['Pruebas sin motor facial real','Panel, formularios, altas, rechazo de datos inválidos, cambios de estado, registros e integridad SQLite.'],
 ['Pruebas con partes simuladas','Guardar/actualizar perfil; rechazar cero o dos rostros; permitir vector coincidente y rechazar desconocido o inactivo.'],
 ['No verificado en ese entorno','Modelo buffalo_l, precisión con fotos reales, cámara, teléfono e interfaz mediante inspección visual.']], [.34,.66])
add('Se ejecutaron <b>34 comprobaciones: 28 satisfactorias y 6 fallidas o con controles ausentes</b>. Se usaron datos ficticios y una base temporal. Esa cifra no representa precisión facial ni porcentaje de cobertura.')
h('Hallazgos pendientes')
bullets(['Administración sin login y formularios sin protección CSRF.','En una base nueva, arrancar mediante importación/Flask CLI no crea las tablas. La ejecución documentada con python app.py sí llama a la inicialización.','Conexiones SQLite sin cierre explícito.','Un fallo inesperado del detector puede generar HTTP 500.','Reemplazar la biometría conserva imágenes anteriores.'])
h('Fortalezas que sí pueden explicar')
add('Separación de módulos; SQLite persistente para una demo local; consultas parametrizadas; perfil único por empleado; filtro de estado activo; validación de un solo rostro; registro de decisiones normales; alternativa de carga de foto.')
box('“Tenemos implementado el flujo básico. Probamos la administración y la lógica de autorización con datos simulados. Falta validar el reconocimiento con personas reales y corregir los hallazgos antes de ampliar el sistema”.','FORMA PRECISA DE PRESENTAR EL AVANCE')
add('<b>Antes de un uso real:</b> falta prueba de vida, calibración, autenticación y protección de datos biométricos. La ejecución directa usa debug=True y una clave predeterminada si no se configura otra. No hay integración con un molinete físico.','small')

page('Guion de exposición: cinco áreas')
add('Distribución sugerida para una defensa de 6 a 8 minutos. Cada integrante explica un área del trabajo del equipo. Los bloques sirven como apoyo: conviene entenderlos y expresarlos con palabras propias.')
for title,text in [
 ('1. Objetivo y arquitectura', '“Nuestro Sprint 1 construye un prototipo local de control de acceso. Incluye administración de personal, enrolamiento, verificación y registros. Separamos interfaz, servidor, persistencia y motor facial. Flask coordina el flujo; SQLite guarda la información. Por ahora el molinete es un simulador web”.'),
 ('2. Administración e interfaz', '“El panel muestra métricas y últimos accesos. Podemos registrar una persona con nombre, correo opcional y estado, y completar su biometría después. Validamos nombre y estado; el correo informado es único. Desactivar a alguien conserva sus datos, pero excluye su perfil de la búsqueda autorizada”.'),
 ('3. Base de datos', '“Elegimos SQLite porque el prototipo es local. employees guarda al personal; biometric_profiles, su vector y la ruta de la foto; access_logs, los intentos. Cada empleado puede tener un único perfil biométrico. Las consultas usan parámetros y habilitamos claves foráneas para mantener las relaciones”.'),
 ('4. Enrolamiento y motor', '“OpenCV lee la foto e InsightFace obtiene los rostros. Exigimos exactamente uno y guardamos su embedding normalizado como bytes. No guardamos un hash. Utilizamos un modelo ya entrenado, configurado para CPU, y lo reutilizamos después de cargarlo. La validación con personas reales está pendiente en el entorno revisado”.'),
 ('5. Decisión, pruebas y cierre', '“Comparamos la nueva imagen con los perfiles activos. Seleccionamos la mayor similitud y aplicamos el umbral de 0,40. Registramos la decisión. Probamos el panel, la persistencia y la autorización con vectores simulados. El siguiente paso es validar el modelo y la cámara, y corregir errores y controles ausentes”.')]:
    h(title); add(text,'quote'); story.append(Spacer(1,5))
h('Demostración recomendada')
add('Mostrar panel → registrar persona sin foto → consultar listado → mostrar formulario de enrolamiento → desactivar persona → explicar filtro de activos. Solo demostrar reconocimiento real si antes lo probaron en el equipo de la exposición.')
box('Para explicar cualquier parte, seguí esta secuencia: <b>qué recibe → qué valida → qué función llama → qué guarda → qué devuelve</b>. Si recordás ese recorrido, podés responder sin memorizar líneas.','TU APOYO SI TE QUEDÁS EN BLANCO')

page('Preguntas típicas de la defensa')
qas=[
 ('¿Por qué un embedding y no un hash?', 'Porque necesitamos medir similitud entre fotos distintas. El embedding es la representación que produce el modelo para esa comparación.'),
 ('¿Ustedes entrenaron la inteligencia artificial?', 'No. Integramos un modelo preentrenado y programamos su uso dentro de la app.'),
 ('¿Dónde están las fotos?', 'En uploads/. SQLite guarda la ruta y el vector como BLOB. La foto no está dentro de la tabla.'),
 ('¿Qué pasa si hay dos rostros?', 'El código rechaza la imagen porque exige exactamente uno, tanto al enrolar como al verificar.'),
 ('¿Puede entrar alguien activo sin foto?', 'No mediante su propio perfil: necesita biometría registrada y una coincidencia suficiente.'),
 ('¿Qué significa 0,40?', 'Es el umbral de similitud. No es una probabilidad. Todavía debe calibrarse con fotos representativas.'),
 ('¿La distancia y la similitud son lo mismo?', 'No. La app calcula distancia como 1 menos similitud: menor distancia significa mayor parecido.'),
 ('¿Por qué SQLite?', 'Simplifica el prototipo local y conserva los datos sin un servidor independiente. Una migración futura dependería de la concurrencia y del uso esperado.'),
 ('¿Cada intento queda registrado?', 'Las decisiones normales y los errores controlados del flujo sí. Algunos fallos inesperados o rechazos previos todavía no generan un registro.'),
 ('¿El sistema detecta una foto usada para engañarlo?', 'No implementa prueba de vida. Acepta imágenes; no demuestra presencia física.'),
 ('¿Qué sucede si no hay perfiles activos?', 'Se deniega si se procesa la imagen correctamente. El código obtiene primero su embedding, por lo que un error de imagen o modelo puede ocurrir antes.'),
 ('¿Está listo para producción?', 'No. Es un prototipo. Faltan validación real, calibración, autenticación, controles de formularios y mejoras en errores y protección de datos.')]
for question,answer in qas:
    story.append(KeepTogether([p(question,'h2'),p(answer)]))

page('Práctica: comprobá que entendiste')
add('Respondé primero sin mirar. No busques repetir una definición: explicá qué pasa dentro de esta app.')
h('Seis situaciones')
for i,text in enumerate([
 'Ana está activa, pero todavía no tiene perfil biométrico. ¿Su registro alcanza para autorizarla?',
 'Bruno tiene perfil, pero está inactivo. ¿El motor lo incluye entre los candidatos?',
 'Las similitudes contra dos perfiles activos son 0,35 y 0,62. ¿Cuál elige? ¿Qué distancia devuelve?',
 'El mejor valor es 0,39. ¿Se permite el acceso con el umbral actual?',
 'Una persona vuelve a cargar su foto. ¿Se crean dos perfiles? ¿Qué pasa hoy con la foto anterior?',
 'Se muestra un mensaje de “faltan librerías”. ¿Es equivalente a haber probado el reconocimiento real?'],1):
    add(f'<b>{i}.</b> {text}')
h('Respuestas para autocorregirte')
answers=[
 'No. No tiene un vector con el que pueda identificarse como perfil autorizado.',
 'No. La consulta filtra por status = active antes de comparar los perfiles.',
 'El perfil con 0,62. Supera 0,40 y la distancia es 1 - 0,62 = 0,38.',
 'No. 0,39 es menor que 0,40; devuelve que no hubo coincidencia autorizada.',
 'No crea dos perfiles: actualiza el existente. Actualmente conserva la foto anterior en disco.',
 'No. Solo demuestra que se maneja la ausencia de dependencias. Hay que ejecutar el modelo y probar imágenes reales.']
for i,text in enumerate(answers,1): add(f'<b>{i}.</b> {text}','small')
h('Plan breve de estudio: 60 minutos')
table(['Tiempo','Actividad'],[
 ['10 min','Leer arquitectura y dibujar el recorrido completo.'],['15 min','Recorrer alta y enrolamiento en app.py.'],['15 min','Leer tablas y find_match(); explicar un ejemplo numérico.'],['10 min','Resolver los seis casos sin mirar respuestas.'],['10 min','Ensayar en voz alta el guion y responder tres preguntas.']], [.18,.82])
box('Podés dar por comprendido un tema cuando lo explicás con un ejemplo, encontrás la función correspondiente y distinguís qué está probado de qué está pendiente.','CRITERIO DE ESTUDIO')

page('Repaso final y mapa del código')
h('El recorrido que tenés que poder contar')
box('<b>Alta:</b> formulario → Flask valida → employees.<br/><b>Enrolamiento:</b> foto → un rostro → embedding → biometric_profiles.<br/><b>Acceso:</b> nueva imagen → embedding → perfiles activos → mayor similitud → umbral → access_logs.')
table(['Concepto','Recordatorio de una línea'],[
 ['Embedding','Vector para comparar rostros; no es hash ni cifrado.'],['Normalización','Vector de longitud uno; habilita similitud coseno por producto punto.'],['BLOB','Datos binarios guardados en SQLite.'],['Base64','Bytes representados como texto para transportar la captura.'],['Enrolamiento','Registrar la representación facial de una persona.'],['Falso positivo / negativo','Autorizar por error / rechazar por error; deben medirse con pruebas reales.'],['Transacción','Grupo de cambios que se confirma o revierte. No implica cierre de conexión.']], [.28,.72])
h('Dónde buscar al estudiar')
table(['Archivo','Funciones o elementos clave'],[
 ['app.py','dashboard, new_employee, save_biometric_profile, toggle_status, enroll_employee, access, write_access_log.'],['database.py','get_connection, initialize_database, query_all, query_one; esquema de las tres tablas.'],['recognition_engine.py','_get_model, _one_embedding, encoding_from_image, encoding_from_bytes, find_match.'],['templates/access.html','getUserMedia, canvas, snapshot, formulario y carga alternativa.']], [.34,.66])
h('Frases que conviene evitar')
add('“Hasheamos caras”; “0,40 es 40 % de certeza”; “entrenamos el modelo”; “Base64 cifra la imagen”; “with cierra SQLite”; “ya funciona todo”. Reemplazalas por las explicaciones precisas de esta guía.')
add('<b>Fuentes de esta guía:</b> app.py, database.py, recognition_engine.py, templates/, README.md y VERIFICACION.md del proyecto local. Comportamiento del contexto SQLite: <link href="https://docs.python.org/3/library/sqlite3.html#how-to-use-the-connection-context-manager" color="#215DAD">documentación oficial de Python</link>.','small')
add('<b>Alcance:</b> material de estudio del Sprint 1, preparado el 5 de octubre de 2026. Refleja la implementación leída y la auditoría previa; no certifica precisión biométrica ni aptitud para un control de acceso real.','small')

def decorate(c,doc):
    c.saveState()
    n=doc.page
    c.setFillColor(NAVY); c.rect(0,A4[1]-12,A4[0],12,fill=1,stroke=0)
    c.setFont('ArialBold',8); c.setFillColor(GRAY)
    c.drawString(46,A4[1]-36,'CONTROL DE ACCESO FACIAL / GUÍA DE ESTUDIO')
    c.setStrokeColor(colors.HexColor('#D3DFE9')); c.line(46,40,A4[0]-46,40)
    c.setFont('Arial',8); c.drawString(46,26,'Sprint 1 · 5 de octubre de 2026')
    c.drawRightString(A4[0]-46,26,f'{n} / 12')
    if n <= len(titles):
        c.bookmarkPage(f'page{n}')
        c.addOutlineEntry(titles[n-1],f'page{n}',level=0,closed=False)
    c.restoreState()
doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=46,leftMargin=46,topMargin=58,bottomMargin=54,title='Guía de estudio y defensa - App de reconocimiento facial - Sprint 1',author='Equipo del proyecto',subject='Funcionamiento, código, pruebas y preparación de exposición',pageCompression=1)
doc.build(story,onFirstPage=decorate,onLaterPages=decorate)
reader=PdfReader(str(OUT))
texts=[page.extract_text() for page in reader.pages]
assert len(reader.pages)==12, f'Paginación inesperada: {len(reader.pages)}'
for i,title in enumerate(titles):
    assert title in texts[i], f'Título fuera de página: {title}'
assert all(len(t)>600 for t in texts)
assert '0,40' in ''.join(texts) and 'No cierra automáticamente' in ''.join(texts)
print(f'PDF generado: {OUT}\nPáginas: {len(reader.pages)}\nTamaño: {OUT.stat().st_size} bytes')
print('Caracteres por página:',[len(t) for t in texts])

