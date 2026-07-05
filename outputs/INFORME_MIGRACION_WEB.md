# Migracion a plataforma web

## Analisis del proyecto original

El proyecto original ya estaba organizado por capas:

- `data_representation`: entidades de dominio.
- `dao`: persistencia SQLite.
- `logical_business`: validaciones, reglas y flujo de competencia.
- `services`: servicios de contenido remoto.
- `network`: sockets TCP y protocolo JSON.
- `gui`: pantallas Tkinter.
- `helper`: constantes, estilos y creacion de tablas.

La logica mas valiosa estaba en `logical_business` y `dao.partida_dao`: creacion de partidas, validacion de cuestionarios, sala de espera, cola de palabra, correccion, puntajes, ranking, avance de preguntas y cierre de partida.

## Componentes reutilizados

Se reutilizaron las capas:

- `dao`
- `data_representation`
- `logical_business`
- `services`
- `helper`
- `img`

La capa `gui` no se reutilizo porque estaba acoplada a Tkinter. La capa `network` tampoco se reutilizo porque el requisito elimina sockets TCP tradicionales y los reemplaza con Flask-SocketIO.

## Cambios principales

- `dao/dao.py` fue adaptado de SQLite a PostgreSQL usando `psycopg2` y `DATABASE_URL`.
- `helper/database_implements.py` ahora crea automaticamente el esquema en PostgreSQL.
- `logical_business/partida_business.py` conserva el flujo original, pero ahora genera codigos alfanumericos de sala.
- `dao/partida_dao.py` conserva las transacciones de competencia y cola de palabra, ajustadas para PostgreSQL.
- Se agregaron rutas Flask, templates Bootstrap y eventos Flask-SocketIO.

## Nueva estructura web

- `app.py`: fabrica y arranque de Flask.
- `config.py`: configuracion y credenciales globales del juez.
- `extensions.py`: instancia SocketIO.
- `routes/`: pantallas y API HTTP.
- `socket_events/`: eventos en tiempo real.
- `templates/`: interfaz Bootstrap.
- `static/`: CSS, JavaScript e imagenes.
- `helpers/serializers.py`: conversion de entidades existentes a JSON.

## Flujo en tiempo real

Los eventos SocketIO implementados cubren:

- unirse a sala
- participante conectado
- iniciar competencia
- mostrar pregunta
- actualizar cronometro
- pedir palabra
- dar palabra
- respuesta correcta
- respuesta incorrecta
- actualizar puntajes
- mostrar siguiente pregunta
- finalizar competencia
- mostrar podio

El orden de pedir palabra se registra en el servidor y en base de datos, conservando la regla original.

## Despliegue

La aplicacion queda preparada para Render mediante:

- `requirements.txt`
- `Procfile`
- uso exclusivo de `DATABASE_URL`
- Gunicorn
- Flask-SocketIO
- PostgreSQL

## Verificacion pendiente

En este entorno no hay Python instalado, por lo que no fue posible ejecutar `compileall`, iniciar Flask ni correr pruebas automatizadas. La revision realizada fue estatica sobre archivos y dependencias.
