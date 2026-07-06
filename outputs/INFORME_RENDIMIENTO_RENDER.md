# Auditoria de rendimiento para Render

Fecha: 2026-07-06

## Objetivo

Encontrar cuellos de botella reales sin cambiar la arquitectura ni la logica funcional de la plataforma.

## Instrumentacion agregada

Se agrego medicion con `time.perf_counter()` para:

- Endpoints `/api/*`
- Eventos principales de Socket.IO
- Tiempo de SQL
- Tiempo de obtencion de conexion PostgreSQL
- Tiempo de emisiones Socket.IO
- Tiempo de serializacion JSON

Los logs en Render quedan con este formato:

```text
[PERFORMANCE]
POST /api/partidas
Estado: 200
Tiempo total: 0.190 s
DB connection: 0.004 s (8)
SQL: 0.072 s (14)
SocketIO: 0.000 s (0)
Serializacion: 0.003 s (1)
Negocio/otros: 0.111 s
```

Tambien se registran hasta 3 consultas SQL lentas cuando superan 50 ms.

Variable disponible:

```text
PERFORMANCE_LOGS=1
```

Para apagar los logs:

```text
PERFORMANCE_LOGS=0
```

## Cuellos de botella encontrados

### 1. Conexion nueva a PostgreSQL por operacion DAO

Antes, cada llamada a `Dao.conectar()` ejecutaba `psycopg2.connect(...)`.

En Render esto puede costar mucho mas que la consulta misma porque implica crear conexiones repetidamente contra PostgreSQL.

Optimizacion:

- Se implemento `ThreadedConnectionPool`.
- Los DAOs conservan la misma interfaz.
- `Dao.cerrar()` ahora devuelve la conexion al pool.

Archivos:

- `dao/dao.py`

### 2. `SELECT LASTVAL()` despues de INSERT

Varios inserts hacian:

1. INSERT
2. SELECT LASTVAL()

Optimizacion:

- Se cambio a `INSERT ... RETURNING id`.
- Se eliminaron viajes extra a PostgreSQL en operaciones frecuentes.

Archivos:

- `dao/materia_dao.py`
- `dao/cuestionario_dao.py`
- `dao/pregunta_dao.py`
- `dao/respuesta_dao.py`
- `dao/ruta_imagen_dao.py`
- `dao/partida_dao.py`

### 3. Creacion de partida con inserts uno por uno

Antes, crear una partida insertaba cada pregunta con una consulta separada.

Ejemplo con 60 preguntas:

- Antes: 60 inserts individuales para `partida_preguntas`.
- Despues: 1 insert masivo con `execute_values`.

Optimizacion:

- `partida_cuestionarios` se inserta por lote.
- `partida_preguntas` se inserta por lote.
- La partida se crea con `RETURNING id_partida`.

Archivo:

- `dao/partida_dao.py`

### 4. Filtro multiusuario aplicado despues de traer datos

Antes, algunos listados cargaban datos completos y luego filtraban por juez en Python con una consulta adicional.

Optimizacion:

- Materias, cuestionarios, rutas de imagen y partidas ahora se filtran por `created_by` directamente en SQL.
- Se reducen consultas y volumen de datos serializado.

Archivos:

- `dao/materia_dao.py`
- `dao/cuestionario_dao.py`
- `dao/ruta_imagen_dao.py`
- `dao/partida_dao.py`
- `routes/api.py`

### 5. Consulta doble para pregunta actual

Antes, `get_current_question()` cargaba primero la partida y despues la pregunta.

Optimizacion:

- Se redujo a una sola consulta SQL con joins.

Archivo:

- `dao/partida_dao.py`

### 6. Socket.IO

Se confirmo que los eventos criticos ya emiten cambios puntuales en:

- `pedir_palabra`
- `dar_palabra`
- `respuesta_correcta`
- `respuesta_incorrecta`
- `finalizar_competencia`

No se cambio la logica de competencia.

Se agrego medicion a:

- `iniciar_competencia`
- `siguiente_pregunta`
- `respuesta_correcta`
- `respuesta_incorrecta`
- `finalizar_competencia`
- `pedir_palabra`
- `dar_palabra`
- conexion/reconexion/desconexion

Archivo:

- `socket_events/competition_events.py`

### 7. Frontend

Se reviso el dashboard.

Las operaciones de guardado ya actualizan componentes locales:

- Materias
- Cuestionarios
- Partidas
- Preguntas

No se encontro recarga completa en esos guardados principales.

## Como medir en Render

Despues de desplegar, ejecutar cada accion y revisar los logs de Render:

- Crear materia: buscar `POST /api/materias`
- Guardar cuestionario: buscar `POST /api/cuestionarios`
- Guardar pregunta: buscar `POST /api/preguntas` y `POST /api/respuestas`
- Crear partida: buscar `POST /api/partidas`
- Generar codigo: buscar `GET /api/partidas/generar-codigo`
- Abrir partida: buscar `SocketIO juez_unirse`
- Iniciar competencia: buscar `SocketIO iniciar_competencia` y `SocketIO iniciar_competencia publicar_pregunta`
- Siguiente pregunta: buscar `SocketIO siguiente_pregunta` y `SocketIO siguiente_pregunta publicar_pregunta`
- Correcta: buscar `SocketIO respuesta_correcta`
- Incorrecta: buscar `SocketIO respuesta_incorrecta`
- Finalizar: buscar `SocketIO finalizar_competencia`

## Validacion local

Se compilaron todos los archivos Python del proyecto.

La app inicia en local; como no existe `DATABASE_URL` en este entorno, solo muestra el aviso esperado de conexion faltante.

Se verifico que `/api/catalogos` genera logs de rendimiento correctamente.

