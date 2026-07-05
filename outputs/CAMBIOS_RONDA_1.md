# Cambios ronda 1

## Creacion de salas

- La API `/api/partidas` ahora genera automaticamente el codigo de sala si el formulario lo envia vacio.
- El formulario muestra mensajes de exito o error al crear una sala.
- Despues de crear una sala se refresca inmediatamente el panel de partidas.
- El backend convierte valores numericos antes de enviarlos a la logica de negocio.

## Panel de partidas

- Se agrego `get_all_with_summary` en DAO y Business de partidas.
- El panel muestra codigo, nombre, cuestionarios, materias, nivel, estado y participantes conectados.

## Formulario de sala

- Los tres campos numericos ahora tienen etiquetas claras:
  - Tiempo por pregunta (segundos)
  - Puntaje por respuesta correcta
  - Penalizacion por respuesta incorrecta

## Imagenes

- Se reemplazo la captura manual de rutas por carga de archivo.
- La API `/api/imagenes` guarda archivos en `static/uploads`.
- El sistema crea/reutiliza automaticamente la ruta `static/uploads` en el modelo existente `rutas_imagenes`.
- Preguntas y respuestas conservan los campos existentes `id_ruta_imagen` y `nombre_imagen`.

## Verificacion

- Busqueda estatica limpia de referencias al formulario viejo de rutas manuales.
- Busqueda estatica limpia de Tkinter, SQLite y sockets TCP tradicionales en las carpetas activas.
- No fue posible ejecutar `compileall` porque este entorno no tiene Python disponible.
- No fue posible ejecutar validacion automatica de JavaScript porque este entorno no tiene Node.js disponible.
