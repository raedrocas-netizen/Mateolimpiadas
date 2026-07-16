# AGENTS.md — MateOlimpiadas Web

## Contexto del proyecto

MateOlimpiadas Web es la fase final web de una aplicación de competencias académicas en tiempo real para el Colegio IMB-PC, sede Petapa.

Autores principales:
- Matthew Carranza
- Rafael Rosado

Colaboración en pruebas y validación:
- Alejandro Rousselin
- Brandon Figueroa
- Kevin Dávila

La aplicación tiene tres roles sincronizados mediante Flask-SocketIO:
- Juez
- Participante
- Pantalla pública

Tecnologías principales:
- Python
- Flask
- Flask-SocketIO
- PostgreSQL
- HTML
- CSS
- Bootstrap
- JavaScript
- Gunicorn
- Render

## Objetivo de la fase final

La versión web ya es funcional. El trabajo actual consiste en mejorarla sin perder su estabilidad.

Las prioridades, en este orden, son:

1. Mantener intacta la sincronización y el funcionamiento estable de las partidas.
2. Lograr una estética equivalente o superior a la aplicación de escritorio.
3. Alcanzar una funcionalidad igual o mejor que la versión de escritorio.
4. Mejorar la practicidad y reducir pasos, clics y pantallas innecesarias.
5. Mejorar responsive, accesibilidad, claridad y consistencia visual.

## Principio de practicidad

Cada flujo debe requerir la menor cantidad razonable de acciones.

Ejemplos:
- Al crear una partida correctamente, abrir directamente su sala de espera.
- No pedir confirmaciones innecesarias para acciones reversibles.
- No obligar al usuario a regresar manualmente a una pantalla cuando el siguiente paso es evidente.
- Mostrar las acciones principales de forma visible.
- Ocultar opciones avanzadas hasta que sean necesarias.
- Evitar botones duplicados o pasos que no aporten seguridad.
- Mantener mensajes claros de éxito, error, conexión y estado.

Antes de modificar un flujo, documentar:
- flujo actual;
- problema práctico;
- flujo propuesto;
- riesgo de regresión;
- forma de probarlo.

## Referencia de la aplicación de escritorio

La versión web debe conservar o mejorar las siguientes cualidades de la aplicación de escritorio:

- Identidad visual institucional azul, celeste, blanco y tonos neutros.
- Ventanas y paneles con jerarquía visual clara.
- Botones semánticos y acciones principales fáciles de reconocer.
- Creación de partida sencilla.
- Entrada directa a sala de espera después de crear una partida.
- Selección de uno o varios cuestionarios cuando corresponda.
- Sala de espera clara y actualizada.
- Participantes identificados por nombre y sede.
- Estados de partida visibles.
- Cronómetro y progreso fáciles de leer.
- Solicitudes de palabra ordenadas.
- Dar palabra, correcto, incorrecto y sin respuesta.
- Ranking y puntuaciones.
- Preguntas e imágenes con buen tamaño.
- Posibilidad de ampliar imágenes cuando sea necesario.
- Reconexión.
- Pantalla pública sin respuestas correctas.
- Pantalla final y podio.
- Colores o identificación visual por sede.
- Mensajes claros y reducción de pasos innecesarios.

No copiar limitaciones propias de Tkinter. Aprovechar las ventajas de la web para lograr una experiencia mejor.

## Arquitectura que debe respetarse

- `routes/`: rutas Flask.
- `socket_events/`: eventos y sincronización en tiempo real.
- `dao/`: acceso a PostgreSQL.
- `logical_business/`: reglas de negocio.
- `data_representation/`: entidades y representación.
- `templates/`: plantillas HTML/Jinja.
- `static/css/`: estilos.
- `static/js/`: comportamiento frontend.
- `static/audio/`: sonidos.
- `static/img/`: imágenes e identidad visual.

Las consultas SQL deben mantenerse en `dao/`.

## Restricciones obligatorias

No realizar estas acciones sin autorización explícita:

- No trabajar directamente sobre `main`.
- No reescribir la arquitectura.
- No sustituir Socket.IO por polling.
- No agregar recargas automáticas como reemplazo de eventos.
- No cambiar contratos, nombres o payloads de eventos Socket.IO.
- No cambiar reglas de puntuación, penalización o competencia.
- No cambiar el cronómetro sin una tarea específica.
- No cambiar el esquema de PostgreSQL.
- No mover consultas SQL fuera de `dao/`.
- No revelar respuestas correctas al participante o a la pantalla pública.
- No mezclar una refactorización amplia con un cambio visual.
- No agregar dependencias sin justificarlo.
- No guardar credenciales, secretos o tokens en el repositorio.
- No sustituir el logo principal hasta recibir el recurso definitivo.

## Forma obligatoria de trabajar

Para cada tarea:

1. Leer este archivo.
2. Inspeccionar los archivos relacionados.
3. Explicar el flujo actual.
4. Proponer un plan corto.
5. Enumerar los archivos que se modificarán.
6. Realizar cambios pequeños y enfocados.
7. Revisar el diff.
8. Ejecutar las comprobaciones disponibles.
9. Informar qué se probó y qué falta probar.
10. Dejar el cambio listo para revisión mediante pull request.

Cuando la tarea sea grande, primero crear una auditoría o plan sin modificar código.

## Reglas visuales

- Mantener identidad institucional.
- Usar variables CSS para colores, espacios, radios, sombras y tipografía.
- Mantener consistencia entre juez, participante y display.
- Priorizar legibilidad en laptop, teléfono, tableta y proyector.
- Evitar pantallas vacías, planas o saturadas.
- Usar iconos solo cuando ayuden a entender la acción.
- Mantener foco visible y navegación con teclado.
- No depender únicamente del color para comunicar estados.
- Diseñar estados vacíos, cargando, desconectado y error.
- Evitar CSS global que pueda romper otras pantallas.

## Identidad visual aprobada

Logo principal:
- Usar `static/img/logos/logo_olimpiadas_matematica.png`.
- Es el logo principal aprobado para la fase final web.
- Mantener sus proporciones, colores y transparencia.
- No deformarlo, recolorearlo ni recortarlo sin autorización.
- Usar `object-fit: contain` y tamaños responsivos.
- Evitar mostrarlo tan pequeño que el texto interno sea ilegible.
- El archivo fuente editable puede conservarse en
  `docs/branding/logoOlimpiadasMatematica.ai`, pero no debe utilizarse
  directamente desde HTML o CSS.

Favicon:
- Crear o utilizar una versión simplificada y cuadrada del logo.
- No depender del texto completo del logo en tamaños de 16x16 o 32x32.
- Mantener provisionalmente los recursos existentes hasta aprobar el favicon definitivo.

Footer:
- Usar `static/img/logo_petapa.png`.
- Mostrar autores:
  - Matthew Carranza
  - Rafael Rosado
- Mostrar colaboración en pruebas y validación:
  - Alejandro Rousselin
  - Brandon Figueroa
  - Kevin Dávila
- Debe ser compacto, responsive y coherente con el sitio.

## Pruebas mínimas

Para cambios visuales:
- escritorio;
- laptop;
- tableta;
- teléfono;
- texto largo;
- estados vacíos;
- estados de error;
- navegación con teclado;
- contraste;
- foco visible.

Para cambios en flujos o partidas, probar manualmente:

1. Inicio de sesión del juez.
2. Creación de partida.
3. Entrada automática a sala de espera.
4. Ingreso de participante.
5. Inicio de competencia.
6. Pregunta y cronómetro.
7. Solicitud de palabra.
8. Dar palabra.
9. Correcta, incorrecta y sin respuesta cuando aplique.
10. Siguiente pregunta.
11. Finalización.
12. Ranking y podio.
13. Sincronización simultánea en juez, participante y pantalla pública.

## Criterio de finalización

Una tarea está terminada cuando:

- cumple el alcance solicitado;
- mantiene la lógica estable;
- reduce pasos o mejora claramente la experiencia;
- conserva o mejora la funcionalidad de escritorio;
- fue revisada mediante diff;
- fue probada;
- no contiene secretos;
- no rompe responsive;
- queda lista para una pull request y revisión humana.
