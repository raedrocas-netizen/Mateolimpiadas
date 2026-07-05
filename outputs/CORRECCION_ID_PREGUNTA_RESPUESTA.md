# Correccion ID de pregunta al guardar respuesta

## Problema

La pantalla unificada guardaba correctamente la pregunta en `/api/preguntas`, pero luego enviaba `id_pregunta = None` a `/api/respuestas`.

Esto provocaba un error 500 al intentar ejecutar:

```python
int(data.get("id_pregunta", 0))
```

## Correccion

- `dao/pregunta_dao.py` ahora asigna el ID generado al objeto `Pregunta` usando `obtener_ultimo_id()`.
- `/api/preguntas` devuelve explicitamente la pregunta creada/actualizada con `id_pregunta`.
- `static/js/questionnaire_questions.js` valida que `id_pregunta` exista antes de llamar `/api/respuestas`.
- `/api/respuestas` ahora responde error 400 claro si no recibe `id_pregunta`, evitando el 500.

## Resultado esperado

El flujo queda:

1. Guardar pregunta.
2. Recibir `data.id_pregunta`.
3. Enviar ese ID a `/api/respuestas`.
4. Crear la respuesta asociada a la pregunta recien creada.
