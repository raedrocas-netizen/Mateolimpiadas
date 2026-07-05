# Cambios ronda 3

## Organizacion de contenido

- El dashboard principal queda compacto y solo administra materias y cuestionarios en la pestaña de contenido.
- Se removio la gestion acumulada de preguntas y respuestas del dashboard.
- Cada cuestionario ahora tiene acceso a una pantalla exclusiva de administracion de preguntas.

## Administrador de preguntas por cuestionario

- Nueva vista: `/juez/cuestionario/<id>/preguntas`.
- Permite listar, agregar, editar y eliminar preguntas de un cuestionario especifico.
- La pantalla esta preparada para cuestionarios grandes con listado desplazable.

## Pregunta + respuesta integrada

- La respuesta esperada se administra desde el mismo formulario de la pregunta.
- Al crear o editar una pregunta se guarda tambien su respuesta esperada.
- Se conserva la relacion existente entre `preguntas` y `respuestas`.

## Multiusuario

- Se agrego columna `created_by` a materias, cuestionarios, partidas y rutas de imagen.
- Las APIs filtran materias, cuestionarios, preguntas, respuestas, partidas e imagenes por el juez autenticado.
- La unicidad de materias/cuestionarios/rutas pasa a ser por juez mediante indices compuestos.

## Competencia finalizada

- Al finalizar, el participante ve el podio final, su puntaje y acciones para volver al inicio o ingresar a otra sala.
- El boton `Pedir palabra` se oculta al finalizar.

## Validaciones

- Se mejoro el mensaje cuando una sala ya finalizo o no esta disponible para participantes.

## Verificacion

- Revision estatica de referencias nuevas y rutas principales.
- No fue posible ejecutar Python/Node en este entorno porque no estan instalados/disponibles.
