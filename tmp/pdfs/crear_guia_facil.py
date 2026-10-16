from pathlib import Path

# Reutilizar solo las funciones de diseño; no generar la guía anterior.
design = Path(__file__).with_name('crear_guia.py').read_text(encoding='utf-8-sig')
exec(design.split("page('Guía de estudio y defensa')")[0])
OUT = ROOT / 'output/pdf/Guia_facil_Sprint_1.pdf'
styles['body'].fontSize=13
styles['body'].leading=19
styles['body'].spaceAfter=12
styles['quote'].fontSize=13
styles['quote'].leading=19
styles['h2'].fontSize=15
styles['h2'].leading=20
styles['h2'].spaceBefore=12
styles['h2'].spaceAfter=10
styles['small'].fontSize=10
styles['small'].leading=14
styles['cell'].fontSize=11
styles['cell'].leading=16

page('Empezá por esta idea')
add('Una app para decidir quién puede entrar.','title')
add('Pensá en la entrada de una empresa. Hay personas habilitadas para ingresar y otras que no.')
add('Nuestra app permite registrar a esas personas y comparar una nueva foto con sus perfiles faciales.')
box('<b>Registrar → comparar → decidir → guardar el resultado.</b>','LAS CUATRO ACCIONES')
h('Un ejemplo que vamos a usar siempre')
add('<b>Ana</b> trabaja en la empresa. Primero cargamos sus datos y su foto. Cuando intenta entrar, enviamos otra imagen de su rostro.')
add('La app busca una coincidencia entre las personas activas. Si encuentra una suficiente, permite el acceso. Si no, lo deniega.')
h('Tu primera respuesta para la exposición')
box('“Nuestra app es un prototipo de control de acceso. Registra personas, compara rostros y guarda si el acceso fue permitido o denegado”.','PODÉS DECIRLO ASÍ')
add('<b>Practicá:</b> tapá el recuadro y explicá para qué sirve la app con tus palabras.')
add('No necesitás recordar las mismas palabras. Necesitás transmitir la misma idea.','small')
add('<b>Cómo estudiar:</b> leé una página, cerrala y explicala en voz alta. Si te trabás, volvé a leer solo esa parte.','small')

page('Las partes: como una recepción')
add('Imaginá una recepción con una ventanilla, una persona que atiende y un archivo de registros.')
h('1. La pantalla: la ventanilla')
add('Es lo que vemos en el navegador: botones, formularios y resultados. Nos permite enviar los datos.')
add('<b>En el proyecto:</b> las páginas están en templates/ y el diseño en static/style.css.','small')
h('2. Flask: quien coordina')
add('Recibe lo que enviamos. Comprueba los datos y pide ayuda a la base de datos o al motor facial.')
add('<b>En el proyecto:</b> app.py.','small')
h('3. SQLite: el archivo de registros')
add('Guarda las personas, sus perfiles faciales y los intentos de acceso. Los datos permanecen aunque reiniciemos la app.')
add('<b>En el proyecto:</b> database.py.','small')
h('4. El motor facial: quien compara')
add('Procesa la foto y obtiene números que permiten compararla con los rostros registrados.')
add('<b>En el proyecto:</b> recognition_engine.py.','small')
box('“La pantalla recibe los datos. Flask coordina. SQLite guarda. El motor facial compara”.','CUATRO PARTES, CUATRO FUNCIONES')
add('<b>Practicá:</b> ¿qué parte guarda la información? ¿Cuál compara los rostros?')

page('Primero registramos a Ana')
h('Paso 1. Cargamos sus datos')
add('Escribimos su nombre, un correo opcional y su estado: activo o inactivo. La app guarda un registro de Ana.')
h('Paso 2. Cargamos una foto')
add('La imagen debe tener exactamente un rostro. Si no hay ninguno o hay varios, el código la rechaza.')
h('Paso 3. Creamos su perfil facial')
add('El modelo transforma el rostro en una lista de números. Esa lista se llama <b>embedding</b> y se usa para comparar fotos.')
box('<b>Embedding = números que representan un rostro para compararlo.</b><br/><br/>No es un hash ni una foto cifrada.','UNA PALABRA NUEVA')
h('Tres palabras que tenés que distinguir')
bullets(['<b>Registrada:</b> Ana tiene sus datos guardados.','<b>Activa:</b> Ana está habilitada para participar en la búsqueda.','<b>Enrolada:</b> Ana tiene su perfil facial guardado.'])
add('Para que la app la autorice mediante su perfil, debe estar activa, tener biometría y lograr una coincidencia suficiente.')
add('<b>Practicá:</b> Ana está activa, pero todavía no cargó su biometría. ¿Alcanza para reconocerla? <b>No.</b>')

page('Después verificamos el acceso')
add('Ana intenta ingresar. La app recibe una nueva foto, subida como archivo o capturada desde la cámara.')
h('La decisión en cuatro pasos')
bullets(['<b>1.</b> Obtiene los números del rostro de la nueva imagen.','<b>2.</b> Busca los perfiles de personas activas.','<b>3.</b> Compara y elige el perfil más parecido.','<b>4.</b> Si el parecido alcanza el mínimo configurado, permite el acceso; si no, lo deniega.'])
h('¿Qué pasa si desactivan a Ana?')
add('Su perfil deja de participar en la búsqueda autorizada. Sus datos no se borran.')
h('¿Cómo sabemos qué decidió la app?')
add('Guarda el resultado en un registro de acceso. El panel muestra los intentos recientes.')
box('“No alcanza con tener una foto registrada. La persona debe estar activa y la nueva imagen debe coincidir suficientemente con un perfil autorizado”.','LA REGLA PRINCIPAL')
add('<b>Si preguntan por el número 0,40:</b> es el mínimo de similitud configurado en el prototipo. No significa 40 % de certeza. Todavía necesita pruebas con fotos reales.','small')
add('<b>Practicá:</b> explicá qué ocurre si la foto no coincide con ninguna persona autorizada.')

page('Qué decir en la exposición')
add('Podés explicar todo el proyecto con estos cinco bloques. Cada integrante puede presentar uno.')
h('1. Para qué sirve')
add('“Hicimos un prototipo para administrar personas y verificar su acceso mediante imágenes de sus rostros”.','quote')
h('2. Cómo cargamos el personal')
add('“Registramos nombre, correo opcional y estado. También podemos activar o desactivar a una persona”.','quote')
h('3. Qué guardamos')
add('“SQLite guarda las personas, sus perfiles faciales y los accesos. Las fotos quedan como archivos en uploads/”.','quote')
h('4. Cómo comparamos')
add('“Usamos un modelo ya entrenado para obtener números del rostro. Comparamos esos números con los perfiles activos”.','quote')
h('5. Qué logramos y qué falta')
add('“Probamos el panel, los datos y la lógica de acceso con vectores simulados. En el entorno revisado falta probar el reconocimiento con personas reales y la cámara”.','quote')
box('<b>Implementado</b> significa que está en el código.<br/><b>Probado</b> significa que lo ejecutamos y comprobamos.<br/><br/>No son lo mismo.','PARA EXPLICAR EL AVANCE CORRECTAMENTE')
add('Todavía hay errores por corregir y falta proteger la administración con un inicio de sesión. Es un prototipo, no un sistema listo para uso real.','small')

page('Repasá sin mirar')
add('Leé la pregunta, tapá la respuesta y contestá en voz alta. Una respuesta corta está bien.')
for q,a in [
 ('¿Para qué sirve la app?', 'Para registrar personas, comparar rostros y decidir el acceso.'),
 ('¿Quién guarda los datos?', 'SQLite, la base de datos.'),
 ('¿Qué es un embedding?', 'Una lista de números que representa un rostro para compararlo.'),
 ('¿Qué pasa si la persona está inactiva?', 'Su perfil queda fuera de la búsqueda autorizada.'),
 ('¿Qué pasa si no hay coincidencia suficiente?', 'Se deniega el acceso.'),
 ('¿Está todo comprobado con personas reales?', 'No. En la revisión anterior, la lógica facial se probó con simulaciones.')]:
    h(q); add(a)
box('<b>5 minutos:</b> leé las páginas 1 y 2.<br/><b>5 minutos:</b> contá la historia de Ana de las páginas 3 y 4.<br/><b>5 minutos:</b> practicá el guion y estas preguntas.','UNA SESIÓN CORTA DE ESTUDIO')
add('<b>Si te olvidás de todo, empezá por esto:</b> “Primero registramos a la persona. Después comparamos una nueva foto. Finalmente decidimos y guardamos el resultado”.','small')
add('Guía simplificada del 5 de octubre de 2026. Basada en el código del proyecto y en VERIFICACION.md del 2 de octubre. No se hicieron nuevas pruebas de la app para crear este material.','small')

def decorate(c,doc):
    c.saveState()
    c.setFillColor(NAVY); c.rect(0,A4[1]-12,A4[0],12,fill=1,stroke=0)
    c.setFillColor(GRAY); c.setFont('ArialBold',8)
    c.drawString(46,A4[1]-36,'RECONOCIMIENTO FACIAL / GUÍA FÁCIL')
    c.setStrokeColor(colors.HexColor('#D3DFE9')); c.line(46,40,A4[0]-46,40)
    c.setFont('Arial',8); c.drawString(46,26,'Sprint 1 · Estudiá una idea por vez')
    c.drawRightString(A4[0]-46,26,f'{doc.page} / 6')
    if doc.page <= len(titles):
        c.bookmarkPage(f'p{doc.page}'); c.addOutlineEntry(titles[doc.page-1],f'p{doc.page}')
    c.restoreState()
doc=SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=46,rightMargin=46,topMargin=58,bottomMargin=54,title='Guía fácil para estudiar y exponer - Sprint 1',author='Equipo del proyecto')
doc.build(story,onFirstPage=decorate,onLaterPages=decorate)
r=PdfReader(str(OUT))
assert len(r.pages)==6,len(r.pages)
for i,title in enumerate(titles): assert title in r.pages[i].extract_text(),title
print(f'PDF listo: {len(r.pages)} páginas; {OUT.stat().st_size} bytes')

