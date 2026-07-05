from dao.dao import Dao


SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS materias(
        id_materia SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL UNIQUE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS cuestionarios(
        id_cuestionario SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL UNIQUE,
        id_materia INTEGER NOT NULL REFERENCES materias(id_materia)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        area TEXT NOT NULL,
        estado TEXT NOT NULL,
        fecha_creacion TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS rutas_imagenes(
        id_ruta SERIAL PRIMARY KEY,
        descripcion TEXT NOT NULL UNIQUE,
        ruta TEXT NOT NULL UNIQUE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS preguntas(
        id_pregunta SERIAL PRIMARY KEY,
        id_cuestionario INTEGER NOT NULL REFERENCES cuestionarios(id_cuestionario)
            ON DELETE CASCADE ON UPDATE CASCADE,
        enunciado TEXT NOT NULL,
        id_ruta_imagen INTEGER REFERENCES rutas_imagenes(id_ruta)
            ON DELETE SET NULL ON UPDATE CASCADE,
        nombre_imagen TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS respuestas(
        id_respuesta SERIAL PRIMARY KEY,
        id_pregunta INTEGER NOT NULL REFERENCES preguntas(id_pregunta)
            ON DELETE CASCADE ON UPDATE CASCADE,
        descripcion TEXT NOT NULL,
        id_ruta_imagen INTEGER REFERENCES rutas_imagenes(id_ruta)
            ON DELETE SET NULL ON UPDATE CASCADE,
        nombre_imagen TEXT,
        UNIQUE(id_pregunta)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS partidas(
        id_partida SERIAL PRIMARY KEY,
        codigo_partida TEXT NOT NULL UNIQUE,
        nombre TEXT NOT NULL,
        area TEXT NOT NULL,
        tiempo_por_pregunta INTEGER NOT NULL,
        puntos_correcta INTEGER NOT NULL,
        penalizacion_incorrecta INTEGER NOT NULL,
        estado TEXT NOT NULL,
        pregunta_actual INTEGER NOT NULL DEFAULT 0,
        fecha_creacion TEXT NOT NULL,
        tiempo_restante_actual INTEGER,
        temporizador_activo_desde TEXT,
        tiempo_agotado INTEGER NOT NULL DEFAULT 0
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS partida_cuestionarios(
        id_partida_cuestionario SERIAL PRIMARY KEY,
        id_partida INTEGER NOT NULL REFERENCES partidas(id_partida)
            ON DELETE CASCADE ON UPDATE CASCADE,
        id_cuestionario INTEGER NOT NULL REFERENCES cuestionarios(id_cuestionario)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        UNIQUE(id_partida, id_cuestionario)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS partida_preguntas(
        id_partida_pregunta SERIAL PRIMARY KEY,
        id_partida INTEGER NOT NULL REFERENCES partidas(id_partida)
            ON DELETE CASCADE ON UPDATE CASCADE,
        id_pregunta INTEGER NOT NULL REFERENCES preguntas(id_pregunta)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        numero_orden INTEGER NOT NULL,
        estado TEXT NOT NULL DEFAULT 'PENDIENTE',
        UNIQUE(id_partida, numero_orden)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS participantes(
        id_participante SERIAL PRIMARY KEY,
        id_partida INTEGER NOT NULL REFERENCES partidas(id_partida)
            ON DELETE CASCADE ON UPDATE CASCADE,
        codigo_participante TEXT NOT NULL,
        nombre TEXT NOT NULL,
        sede TEXT NOT NULL,
        integrantes TEXT NOT NULL DEFAULT '',
        puntaje INTEGER NOT NULL DEFAULT 0,
        estado TEXT NOT NULL DEFAULT 'DESCONECTADO',
        conectado INTEGER NOT NULL DEFAULT 0,
        UNIQUE(id_partida, codigo_participante),
        UNIQUE(id_partida, sede)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS solicitudes_palabra(
        id_solicitud SERIAL PRIMARY KEY,
        id_partida INTEGER NOT NULL REFERENCES partidas(id_partida)
            ON DELETE CASCADE ON UPDATE CASCADE,
        id_partida_pregunta INTEGER NOT NULL REFERENCES partida_preguntas(id_partida_pregunta)
            ON DELETE CASCADE ON UPDATE CASCADE,
        id_participante INTEGER NOT NULL REFERENCES participantes(id_participante)
            ON DELETE CASCADE ON UPDATE CASCADE,
        orden_solicitud INTEGER NOT NULL,
        fecha_hora TEXT NOT NULL,
        estado TEXT NOT NULL DEFAULT 'EN_COLA',
        UNIQUE(id_partida_pregunta, id_participante)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS respuestas_partida(
        id_respuesta_partida SERIAL PRIMARY KEY,
        id_partida INTEGER NOT NULL REFERENCES partidas(id_partida)
            ON DELETE CASCADE ON UPDATE CASCADE,
        id_partida_pregunta INTEGER NOT NULL REFERENCES partida_preguntas(id_partida_pregunta)
            ON DELETE CASCADE ON UPDATE CASCADE,
        id_participante INTEGER NOT NULL REFERENCES participantes(id_participante)
            ON DELETE CASCADE ON UPDATE CASCADE,
        resultado TEXT NOT NULL,
        puntos_aplicados INTEGER NOT NULL,
        fecha_hora TEXT NOT NULL
    );
    """,
    """
    ALTER TABLE materias
    ADD COLUMN IF NOT EXISTS created_by TEXT NOT NULL DEFAULT 'global';
    """,
    """
    ALTER TABLE cuestionarios
    ADD COLUMN IF NOT EXISTS created_by TEXT NOT NULL DEFAULT 'global';
    """,
    """
    ALTER TABLE partidas
    ADD COLUMN IF NOT EXISTS created_by TEXT NOT NULL DEFAULT 'global';
    """,
    """
    ALTER TABLE rutas_imagenes
    ADD COLUMN IF NOT EXISTS created_by TEXT NOT NULL DEFAULT 'global';
    """,
    """
    ALTER TABLE materias
    DROP CONSTRAINT IF EXISTS materias_nombre_key;
    """,
    """
    ALTER TABLE cuestionarios
    DROP CONSTRAINT IF EXISTS cuestionarios_nombre_key;
    """,
    """
    ALTER TABLE rutas_imagenes
    DROP CONSTRAINT IF EXISTS rutas_imagenes_descripcion_key;
    """,
    """
    ALTER TABLE rutas_imagenes
    DROP CONSTRAINT IF EXISTS rutas_imagenes_ruta_key;
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS materias_created_by_nombre_idx
    ON materias(created_by, nombre);
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS cuestionarios_created_by_nombre_idx
    ON cuestionarios(created_by, nombre);
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS rutas_imagenes_created_by_descripcion_idx
    ON rutas_imagenes(created_by, descripcion);
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS rutas_imagenes_created_by_ruta_idx
    ON rutas_imagenes(created_by, ruta);
    """,
    """
    CREATE INDEX IF NOT EXISTS partidas_codigo_partida_idx
    ON partidas(codigo_partida);
    """,
    """
    CREATE INDEX IF NOT EXISTS partidas_created_by_estado_idx
    ON partidas(created_by, estado);
    """,
    """
    CREATE INDEX IF NOT EXISTS cuestionarios_materia_area_idx
    ON cuestionarios(id_materia, area);
    """,
    """
    CREATE INDEX IF NOT EXISTS preguntas_cuestionario_idx
    ON preguntas(id_cuestionario);
    """,
    """
    CREATE INDEX IF NOT EXISTS respuestas_pregunta_idx
    ON respuestas(id_pregunta);
    """,
    """
    CREATE INDEX IF NOT EXISTS partida_preguntas_partida_orden_idx
    ON partida_preguntas(id_partida, numero_orden);
    """,
    """
    CREATE INDEX IF NOT EXISTS participantes_partida_puntaje_idx
    ON participantes(id_partida, puntaje DESC, sede, nombre);
    """,
    """
    CREATE INDEX IF NOT EXISTS solicitudes_palabra_partida_pregunta_estado_idx
    ON solicitudes_palabra(id_partida, id_partida_pregunta, estado, orden_solicitud);
    """,
    """
    CREATE INDEX IF NOT EXISTS respuestas_partida_partida_ultima_idx
    ON respuestas_partida(id_partida, id_respuesta_partida DESC);
    """,
    """
    CREATE INDEX IF NOT EXISTS respuestas_partida_pregunta_resultado_idx
    ON respuestas_partida(id_partida_pregunta, resultado);
    """
)


def create_tables():
    dao = Dao()

    if not dao.conectar():
        print("[ERROR] No fue posible conectar a PostgreSQL.")
        return False

    try:
        for statement in SCHEMA_STATEMENTS:
            dao.cursor.execute(statement)

        dao.conexion.commit()
        return True

    except Exception as e:
        dao.conexion.rollback()
        print(f"[ERROR] No fue posible crear/verificar tablas: {e}")
        return False

    finally:
        dao.cerrar()
