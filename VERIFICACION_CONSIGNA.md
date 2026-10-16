# Verificación de adecuación a la consigna - 16 de octubre de 2026

## Resultado

Se implementaron los dos scripts pedidos y se integró el registro CSV con el panel existente. Se conservaron los empleados, las fotografías y los perfiles biométricos que ya estaban cargados.

## Comprobaciones ejecutadas

- **29 pruebas automatizadas aprobadas** con `python -B -m unittest discover -s tests -v`.
- CSV: columnas, nombre, fecha y hora; tildes y comas; primer ingreso por día; nuevo ingreso al día siguiente; personas con nombres iguales e IDs distintos; rechazo de formato incompatible; exclusión de identificadores vacíos.
- Concurrencia: varios hilos y cuatro procesos escribiendo el mismo empleado/día generan una sola asistencia.
- Motor académico: conversión BGR a RGB; API real de distancias y selección del mínimo; tolerancia inclusiva; imágenes inválidas; rutas con tildes; rechazo de cero o dos rostros en fotos de referencia.
- Reconocimiento por cuadro: varios empleados, desconocido, inactivo, cuadro sin rostros y ausencia de registros duplicados.
- Cámara simulada: finalización acotada, frecuencia de procesamiento y liberación del dispositivo al terminar o fallar.
- Base: recodificación de fotos del panel a vectores de face_recognition, exclusión de inactivos, cierre de conexiones y rollback de transacciones fallidas.
- Web: asistencia permitida, denegada y duplicada; consulta; descarga UTF-8; ausencia de CSV; fallos de escritura sin confirmar asistencia.
- Dependencias: `pip check` sin incompatibilidades. Se instaló `face_recognition 1.3.0` y se compiló `dlib 20.0.1` para Python 3.14 en el entorno existente. Se fijó `setuptools<81` porque los modelos de face_recognition todavía usan pkg_resources.
- Sintaxis PowerShell del instalador validada y ayuda CLI de ambos programas comprobada.

## Pruebas con imágenes reales

Se usó el JPG aportado por el usuario y una imagen de otra persona incluida como muestra en una dependencia instalada.

1. Comparación del JPG consigo mismo: coincidencia, distancia **0,0000**. Esto comprueba el flujo positivo, pero no mide reconocimiento entre tomas distintas.
2. Comparación con la otra persona: no coincidencia, distancia **0,7207**, mayor que la tolerancia **0,60**.
3. Foto del usuario frente al padrón cargado en el panel: reconocido y registrado en un CSV temporal. Repetirla no agregó otra fila ese día.
4. La otra persona no generó asistencia en ese padrón.
5. Carga real desde una carpeta de empleados y obtención de nombres de archivo: correcta.
6. Ejecución CLI sin ventana de los dos scripts: correcta. En el segundo se utilizó `--imagen` como diagnóstico.
7. **Webcam física:** apertura y procesamiento de seis cuadros en modo sin ventana; reconoció al empleado, guardó una asistencia en CSV temporal, terminó con código 0 y liberó la cámara. No se guardó video.
8. Ventanas de OpenCV: apertura de la comparación y una segunda prueba de seis cuadros de webcam con ventana; cierre y liberación del dispositivo correctos.
9. Flujo web completo con el motor real de InsightFace en base temporal: alta con foto, generación de perfil, acceso permitido, asistencia única, descarga CSV y acceso denegado después de desactivar al empleado.

Las pruebas de imágenes y webcam no modificaron el CSV habitual del usuario. El flujo web completo se comprobó con otra base temporal; no se alteraron sus empleados ni sus biometrías.

## Inspección visual

Se generaron y revisaron imágenes de diagnóstico con recuadros, etiquetas y resultado/distancia de la comparación en `data/pruebas_consigna/`. Están excluidas de Git. Se comprobó la cámara tanto sin ventana como con ventana, con seis cuadros en cada prueba. También se verificó la apertura de la ventana de comparación. Queda pendiente una demostración interactiva prolongada en el equipo de exposición.

## Compatibilidad y límites

- Se corrigió el acceso a modelos de dlib en carpetas acentuadas mediante rutas cortas de Windows y una alternativa de caché ASCII cuando no existen nombres cortos.
- El panel mantiene InsightFace, y los dos scripts académicos usan face_recognition. Sus vectores y umbrales no se mezclan.
- Las referencias de la cámara se cargan al iniciar: para incorporar una foto nueva o actualizada, reiniciar el script. En modo base se consulta el estado de habilitación durante el reconocimiento.
- Las anotaciones de OpenCV usan una versión sin tildes del texto por limitaciones de su fuente. El nombre original con tildes se conserva en CSV y en la web.
- Permanecen advertencias de deprecación de dependencias externas; no impidieron las pruebas.
- No se evaluaron FAR/FRR, cambios de iluminación sistemáticos, oclusiones, cámaras de otros equipos ni prevención de suplantación con fotografías. Las pruebas no garantizan precisión biométrica ni aptitud para producción.
- La verificación anterior de `VERIFICACION.md` y los PDF de estudio describen el Sprint 1 previo a estas incorporaciones. Este documento registra las comprobaciones actuales.
