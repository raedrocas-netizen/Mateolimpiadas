# Auditoria de rendimiento y latencia para Render

Fecha: 2026-07-19

Rama auditada: `perf/render-latencia`

## Alcance y limitaciones

La auditoria se realizo sobre el codigo actual, que ya incluye los cambios
recientes del participante y las dependencias frontend locales. No se asumio
que esos cambios fueran la causa de la latencia observada antes de su despliegue.

El entorno local no tiene `DATABASE_URL` ni acceso a CPU, RAM, red o metricas del
servicio de Render. Por eso los tiempos reales de PostgreSQL y Render quedan como
prueba pendiente. Los recuentos SQL se obtuvieron trazando los caminos exitosos
del codigo; incluyen `BEGIN` porque la instrumentacion existente lo registra como
sentencia.

No se modificaron esquema, datos, reglas de competencia, puntuacion, precuenta,
pausa/reanudacion, correcta/incorrecta, contratos Socket.IO ni reconexion.

## Configuracion real de produccion

No existen `render.yaml` ni `Dockerfile`.

El `Procfile` contiene:

```text
web: gunicorn --worker-class gthread --threads 50 --bind 0.0.0.0:$PORT app:app
```

Configuracion efectiva inferible:

- Gunicorn: 1 worker por defecto, porque no se especifica `--workers`.
- Worker class: `gthread`.
- Threads: 50.
- Timeout: 30 segundos por defecto, porque no se especifica `--timeout`.
- Bind: `0.0.0.0:$PORT`.
- Flask-SocketIO: `async_mode="threading"` hardcodeado en `extensions.py`.
- `SOCKETIO_ASYNC_MODE` existe en `Config`, pero actualmente no controla la
  instancia de Socket.IO.
- PostgreSQL: `psycopg2.pool.ThreadedConnectionPool`, minimo 1 y maximo 12 por
  proceso salvo `DB_POOL_MIN` y `DB_POOL_MAX`.
- El pool es compatible con los threads de este proceso. Con mas de 12 prestamos
  simultaneos, `ThreadedConnectionPool.getconn()` puede agotar el pool; hacen falta
  metricas de concurrencia para decidir otro limite.
- Al importar `app.py`, `create_tables()` obtiene una conexion y ejecuta 33
  sentencias DDL de verificacion antes de que el proceso quede listo.

`README_WEB.md` todavia documenta 8 threads, pero el valor ejecutado por el
`Procfile` es 50.

## Flujos auditados

### Pagina principal

`GET /` solo renderiza Jinja y no consulta PostgreSQL. La mediana local de 40
peticiones fue 0.961 ms antes y 0.883 ms despues. La carga fria referenciada por
el HTML era 1,475,610 bytes y quedo en 1,344,896 bytes. La mayor parte restante
es el logo de 1,080,348 bytes; no se cambio por ser identidad visual fuera del
alcance.

### Login del juez

`GET /juez/login` y el `POST` de credenciales no consultan PostgreSQL. Las
credenciales se comparan con configuracion. Un login correcto redirige una vez a
`/juez/nombre`; el `POST /juez/nombre` guarda el nombre en sesion y redirige al
dashboard.

El HTML de `/juez/dashboard` tampoco consulta PostgreSQL. Por tanto, una demora
antes de ver el formulario o despues de una redireccion puede provenir del
arranque del servicio o de recursos estaticos, no de validacion SQL.

Se agrego medicion desactivable a GET/POST de paginas para separar esos tiempos.
En login y nombre se dejaron de referenciar Bootstrap JS y Socket.IO, que no se
usan alli: 395,262 -> 264,548 bytes (-33.1%) en archivos estaticos referenciados.

### Carga inicial del dashboard

El navegador abre Socket.IO, carga `/api/catalogos` y, al terminar, solicita en
paralelo:

- `/api/materias`: 1 consulta y 1 prestamo del pool.
- `/api/cuestionarios`: 1 consulta y 1 prestamo.
- `/api/partidas`: 1 consulta agregada y 1 prestamo.
- `/api/catalogos`: 0 consultas.

La carga inicial normal usa 3 consultas SQL en tres peticiones concurrentes. No
hay SELECT N+1 en esos listados. El dashboard conserva ambos vendors porque usa
Socket.IO, tabs y modal de Bootstrap.

### Participante

`GET /participante/` y `GET /participante/sala` no consultan PostgreSQL. El
catalogo de sedes tampoco.

Un ingreso Socket.IO nuevo usa aproximadamente 12 sentencias: 8 para validar y
crear el participante y 4 para reconstruir ranking. Una reconexion en el mismo
evento usa aproximadamente 11.

La navegacion posterior de ingreso a sala cierra un socket y abre otro. Segun el
orden entre desconexion y reconexion, el proceso completo puede usar
aproximadamente 22 a 39 sentencias. Es el candidato SQL pendiente mas costoso,
pero optimizarlo exige tocar reconexion/transacciones; no se cambio sin una base
PostgreSQL real y smoke test simultaneo.

En el formulario de ingreso ya no se activa la precarga de todos los audios al
primer clic. Esa precarga queda limitada a vistas de competencia que si usan
sonidos.

### Display

`GET /display` no consulta PostgreSQL. `display_unirse` reconstruia el estado con
9 consultas y ahora usa 8. La carga estatica referenciada bajo de 416,652 a
335,931 bytes (-19.4%) al no cargar Bootstrap JS, que esta vista no usa.

## PostgreSQL y conexiones

Cada instancia DAO contiene un `Dao`. Cada metodo obtiene una conexion del pool,
ejecuta su trabajo y la devuelve con `cerrar()`. Ya no se abre una conexion TCP
nueva por operacion en condiciones normales.

Antes de devolverla, `cerrar()` cierra el cursor y hace rollback si la conexion
no esta idle. Las transacciones explicitas hacen commit o rollback. Los SELECT no
hacen commits innecesarios; las escrituras que usan `ejecutar_sql()` si hacen el
commit esperado.

No se encontro N+1 en dashboard ni en `emit_state`. El problema de estado es el
numero de consultas secuenciales y una lectura duplicada de partida, no un N+1
dependiente de cantidad de filas.

No hay configuracion de regiones de Render/PostgreSQL en el repositorio, asi que
no se puede afirmar si estan en ubicaciones distintas.

## Consultas aproximadas por operacion exitosa

| Operacion | Antes | Despues | Nota |
| --- | ---: | ---: | --- |
| Dashboard inicial | 3 | 3 | Tres endpoints concurrentes |
| `juez_unirse` / `display_unirse` | 9 | 8 | Reutiliza partida en ranking |
| `emit_state` | 9 | 8 | Sin cache persistente |
| `pedir_palabra` | 18 | 9 | Elimina reconstruccion redundante |
| `dar_palabra` | 10 | 10 | Transaccion y timer |
| `respuesta_correcta` | ~19 | ~19 | Conservado por riesgo funcional |
| `respuesta_incorrecta` | ~15 | ~15 | Conservado por riesgo funcional |
| `pausar_competencia` | ~18 | ~17 | Solo ahorro de `emit_state` |
| `reanudar_competencia` | ~19 | ~18 | Solo ahorro de `emit_state` |
| Inicio y publicacion de primera pregunta | ~17 | ~16 | Incluye estado diferido |
| Siguiente pregunta normal | ~23 | ~22 | Validaciones duplicadas documentadas |
| Finalizar competencia | ~8 | ~8 | Eventos puntuales, sin estado completo |
| Tick normal | 0 | 0 | Solo memoria y tres emisiones |
| Expiracion natural del timer | ~14 | ~13 | Escritura final mas estado completo |
| `GET /api/partidas/<id>/estado` | 9 | 8 | Reutiliza partida en ranking |

## `emit_state`, serializacion y payloads

Una reconstruccion carga partida, participantes, pregunta, solicitudes, total de
preguntas, ranking, ultimo evento y timer. Antes, ranking volvia a buscar la
partida por codigo. Ahora recibe la instancia ya cargada durante esa ejecucion.

No se agrego cache global. El ahorro es local a la reconstruccion y mantiene el
mismo payload para juez, participante y display.

`pedir_palabra` ya entregaba:

- `resultado_accion` al participante solicitante, con su solicitud;
- `solicitud_palabra` al juez, con la cola;
- `solicitud_palabra_publica` al display, con la cola.

El `emit_state` inmediato no aportaba cambios adicionales y se elimino solo de
esa accion. Una fixture representativa con tres solicitudes midio:

- `estado_sala`: 3 emisiones, 4,507 bytes totales, maximo 1,625 bytes.
- Tick del timer: 3 emisiones, 285 bytes totales, maximo 95 bytes.

Los tamanos son JSON aproximado sin overhead del protocolo y escalan con filas;
las imagenes viajan como URL, no como binario.

La instrumentacion ahora registra bytes y conteo por nombre de evento, nunca el
contenido. Esto evita revelar datos o respuestas correctas.

## Timer

Cada inicio/reanudacion con timer activo crea una tarea mediante
`start_background_task`. Un token unico invalida tareas anteriores.

Por tick:

- duerme 1 segundo;
- verifica el token en memoria;
- decrementa localmente;
- emite `actualizar_cronometro` a participante, juez y display;
- no consulta PostgreSQL;
- no reconstruye ranking, listas, estado ni imagenes.

Al llegar a cero, materializa el agotamiento en PostgreSQL y emite un estado
completo una vez.

Antes, detener o terminar guardaba `codigo -> None` indefinidamente. Ahora la
clave se elimina con `pop()` bajo lock. La expiracion elimina solo si el token
sigue siendo el actual, de modo que un timer viejo no puede borrar uno nuevo.

## Estructuras globales de memoria

| Nombre | Tipo | Contenido | Crece | Limpieza | Riesgo restante |
| --- | --- | --- | --- | --- | --- |
| `_pool` | `ThreadedConnectionPool` | Conexiones PostgreSQL | Hasta max 12 por defecto | Fin del proceso | Acotado |
| `active_timer_tokens` | `dict` | Codigo -> token activo | Inicio/reanudacion | Stop, expiracion o proceso | Corregido; no deja `None` |
| `connected_participants` | `dict` | SID -> partida/participante | Join/reconexion | `disconnect` o proceso | Si no llega disconnect, vive hasta reinicio |
| `connected_judges` | `dict` | SID -> partida | Abrir sala | Cambio de sala, disconnect o proceso | Acotado por sockets vivos normales |
| `active_game_actions` | `dict` | Codigo -> accion atomica | Inicio de transicion | `finally` o proceso | No crece en flujo normal |
| `active_participant_deletions` | `set` | Partida/participante en borrado | Inicio de borrado | `finally` o proceso | No crece en flujo normal |
| Rooms Socket.IO | Interno | SIDs por room | `join_room` | Disconnect; juez deja room previa | Gestion de la libreria |
| Cache de audio frontend | Objeto por pagina | Maximo 9 audios | Primer gesto en vista live | Descarga de pagina | Acotado |

No queda una estructura propia demostrada que crezca indefinidamente durante el
flujo normal. Un reinicio de proceso limpia todas las estructuras en memoria.

## Frontend, listeners y DOM

`judge_dashboard.js`, `participant_room.js` y `display.js` registran sus
listeners Socket.IO una sola vez a nivel superior. No los registran dentro de
`estado_sala`.

No hay `setInterval`. El unico `setTimeout` relevante muestra un aviso temporal
del participante y se limpia al salir de la sala.

Un tick solo actualiza texto del timer, ancho/clases de progreso, sonido y estado
de botones. Ranking, listas e imagenes se reconstruyen al recibir estado completo
o eventos especificos, no cada segundo. Reasignar la misma URL de imagen puede
causar trabajo de DOM en un estado completo, pero el navegador puede reutilizar
cache; no se cambio sin perfil de navegador.

## Recursos estaticos

Bootstrap 5.3.3 y Socket.IO Client 4.7.5 se sirven localmente y sus hashes estan
fijados por pruebas.

Comparacion de bytes referenciados por HTML, basada en tamanos de archivo locales
y sin asumir gzip/Brotli del proxy:

| Pagina | Antes | Despues | Cambio |
| --- | ---: | ---: | ---: |
| Home | 1,475,610 | 1,344,896 | -130,714 (-8.9%) |
| Login juez | 395,262 | 264,548 | -130,714 (-33.1%) |
| Nombre juez | 395,262 | 264,548 | -130,714 (-33.1%) |
| Dashboard | 473,878 | 473,878 | Sin cambio; usa ambos |
| Ingreso participante | 407,317 | 326,596 | -80,721 (-19.8%) |
| Sala participante | 432,556 | 432,556 | Sin cambio; usa ambos |
| Display | 416,652 | 335,931 | -80,721 (-19.4%) |

Los archivos grandes restantes incluyen logo principal historico de 1,080,348
bytes y audios. No se recomprimieron ni sustituyeron recursos visuales/sonoros.

## Instrumentacion

`PERFORMANCE_LOGS` ahora esta apagado por defecto. Para una ventana controlada en
Render:

```text
PERFORMANCE_LOGS=1
```

Para apagar:

```text
PERFORMANCE_LOGS=0
```

Con la variable apagada, `begin_operation()` ya no crea contextos. Benchmark
local de 50,000 operaciones, mediana de 5 rondas:

- Antes: 315.506 ms.
- Despues: 80.189 ms.
- Reduccion local: 74.6%.

Con logs activos se miden:

- GET/POST de paginas, incluidos inicio, login, nombre y dashboard;
- endpoints `/api/*`;
- eventos Socket.IO decorados;
- cada `emit_state`, aunque nazca en una tarea de fondo;
- una muestra del primer tick de cada tarea y la expiracion del timer, sin crear
  un log por cada segundo;
- prestamos del pool;
- SQL y consultas de al menos 50 ms;
- tiempo de emisiones;
- serializacion;
- bytes aproximados de payload por evento.

No se imprimen cuerpos de payload ni credenciales.

## Cuellos de botella priorizados

### CRITICO

Ninguno demostrado con la informacion local disponible.

### ALTO

1. Reconexion/navegacion del participante: ~22-39 sentencias. Frecuente al
   ingresar; alto impacto si DB tiene latencia. Riesgo alto de corregir por
   concurrencia y multiples sockets. No implementado.
2. `pedir_palabra` hacia 9 consultas redundantes y tres estados completos.
   Frecuente; riesgo bajo/moderado. Corregido y probado.
3. `emit_state` hacia 9 viajes secuenciales. Frecuente en uniones/transiciones;
   riesgo bajo para la lectura duplicada. Reducido a 8.
4. Arranque ejecuta 33 DDL. Impacto potencial alto solo en cold start; riesgo
   operativo alto de moverlo. No implementado.

### MEDIO

1. Correcta, incorrecta, pausa, reanudacion y siguiente pregunta hacen varias
   validaciones/lecturas. Riesgo funcional moderado/alto; documentado.
2. 50 threads frente a pool maximo 12. Requiere concurrencia real para saber si
   hay agotamiento; no se cambiaron valores.
3. Recursos JS innecesarios en paginas simples y precarga de audio en paginas no
   live. Corregido localmente.
4. Instrumentacion activa por defecto generaba logs y overhead. Corregido.

### BAJO

1. Imagen principal grande en home. No se cambio para no mezclar identidad
   visual con rendimiento.
2. Reasignacion de imagen durante estados completos. Requiere perfil del browser.
3. Diferencia entre `README_WEB.md` (8 threads) y `Procfile` (50). Documental.

## Optimizaciones no implementadas

- Pool nuevo: ya existe uno seguro para threads.
- Aumento de pool/menos threads: sin metricas de concurrencia puede empeorar DB o
  sockets.
- Consolidacion SQL grande de `emit_state`: mayor riesgo y necesita PostgreSQL
  real.
- Reconexion abreviada: puede romper multiples sockets o estado conectado.
- Mover `create_tables()` fuera del arranque: requiere definir proceso de
  despliegue/migracion, fuera del alcance.
- Indices/migraciones/esquema: prohibidos en esta rama.
- Redis, Celery, async rewrite, otro servidor/proveedor: fuera del alcance.
- Compresion/sustitucion de imagenes o audios: mezcla cambio de recursos visuales.

## Limitaciones potenciales de Render pendientes

Para distinguir codigo de infraestructura hace falta correlacionar logs con:

- cold start vs instancia caliente;
- CPU y RAM durante login/dashboard/competencia;
- latencia app -> PostgreSQL y regiones de ambos servicios;
- conexiones activas, espera/errores del pool y limite de PostgreSQL;
- tiempos de respuesta y transferencia de estaticos;
- compresion y cache headers efectivos;
- concurrencia real de sockets.

No se afirma que Render sea la causa sin esas metricas.

## Pruebas ejecutadas

- `python -m unittest discover -s tests -v`: 82/82 OK.
- Pruebas JavaScript con Node: 34/34 OK.
- `node --check` para `static/js/*.js` y `tests/*.js`: OK.
- Parseo de todas las plantillas Jinja: OK dentro de la suite Python.
- `python -m compileall`: OK.
- `git diff --check`: OK.
- Seguridad de payload publico y respuestas correctas: OK.
- Limpieza natural, stop idempotente y token viejo del timer: OK.
- Solicitud de palabra sin reconstruccion completa: OK.
- Vendors locales y carga solo donde se usan: OK.
- Activacion de audio solo en vistas live: OK.

No se ejecuto una competencia manual con PostgreSQL porque no existe
`DATABASE_URL` en este entorno. Los tiempos Jinja locales no representan Render.

## Smoke test manual recomendado en Render

Activar temporalmente `PERFORMANCE_LOGS=1`, abrir logs y usar juez, dos
participantes y display:

1. Medir `GET /`, `GET/POST /juez/login`, `GET/POST /juez/nombre` y
   `GET /juez/dashboard` por separado.
2. Confirmar que dashboard carga catalogos, materias, cuestionarios y partidas.
3. Crear sala y verificar entrada automatica a espera.
4. Ingresar dos participantes y observar join, disconnect/reconnect y ranking.
5. Conectar display y confirmar que no recibe respuesta correcta.
6. Iniciar y confirmar precuenta exacta de 5 segundos.
7. Solicitar palabra; confirmar un solo evento de cola por juez/display y que el
   participante queda en cola sin `estado_sala` adicional.
8. Dar palabra y confirmar que el timer se detiene una sola vez.
9. Probar Correcta e Incorrecta, incluida cola con timer 0.
10. Pausar/Reanudar y confirmar mismo tiempo/pregunta.
11. Siguiente pregunta y confirmar una sola precuenta/tarea.
12. Finalizar y revisar ranking/podio.
13. Reconectar un participante con dos sockets y cerrar uno; el otro debe seguir
    conectado.
14. Repetir varias salas y confirmar que `active_timer_tokens` queda sin claves
    terminadas.
15. Apagar `PERFORMANCE_LOGS` al terminar la ventana de medicion.

Buscar retrasos progresivos, eventos duplicados, timer acelerado, errores de pool
y crecimiento de mappings por sockets cerrados.

## Archivos modificados

- `app.py`
- `helpers/performance.py`
- `logical_business/partida_business.py`
- `routes/api.py`
- `socket_events/competition_events.py`
- `static/js/live_common.js`
- `templates/base.html`
- `templates/display.html`
- `templates/judge/dashboard.html`
- `templates/judge/questionnaire_questions.html`
- `templates/participant/join.html`
- `templates/participant/room.html`
- `tests/test_frontend_vendor_assets.py`
- `tests/test_live_common.js`
- `tests/test_participant_competition.py`
- `tests/test_pause_resume_competition.py`
- `tests/test_performance_instrumentation.py`
- `tests/test_question_payload_security.py`
- `outputs/INFORME_RENDIMIENTO_RENDER.md`

No se hizo commit ni push.
