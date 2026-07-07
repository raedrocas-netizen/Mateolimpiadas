from dao.dao import Dao

from data_representation.partida import Partida

import helper.super_global as sg
from helpers.ownership import current_owner

from datetime import datetime


class PartidaDao:

    BASE_SELECT = """
    SELECT
        id_partida,
        codigo_partida,
        nombre,
        area,
        tiempo_por_pregunta,
        puntos_correcta,
        penalizacion_incorrecta,
        estado,
        pregunta_actual,
        fecha_creacion,
        tiempo_restante_actual,
        temporizador_activo_desde,
        tiempo_agotado
    FROM partidas
    """

    def __init__(self):
        self.dao = Dao(sg.FULL_PATH)

    def _row_to_partida(self, row):

        partida = Partida()

        partida.set_id_partida(
            row["id_partida"]
        )

        partida.set_codigo_partida(
            row["codigo_partida"]
        )

        partida.set_nombre(
            row["nombre"]
        )

        partida.set_area(
            row["area"]
        )

        partida.set_tiempo_por_pregunta(
            row["tiempo_por_pregunta"]
        )

        partida.set_puntos_correcta(
            row["puntos_correcta"]
        )

        partida.set_penalizacion_incorrecta(
            row["penalizacion_incorrecta"]
        )

        partida.set_estado(
            row["estado"]
        )

        partida.set_pregunta_actual(
            row["pregunta_actual"]
        )

        partida.set_fecha_creacion(
            row["fecha_creacion"]
        )

        partida.set_tiempo_restante_actual(
            row["tiempo_restante_actual"]
            if row["tiempo_restante_actual"] is not None
            else row["tiempo_por_pregunta"]
        )

        partida.set_temporizador_activo_desde(
            row["temporizador_activo_desde"]
        )

        partida.set_tiempo_agotado(
            row["tiempo_agotado"]
            if row["tiempo_agotado"] is not None
            else 0
        )

        return partida

    def _now_text(self):

        return datetime.now().strftime(
            sg.DATETIME_FORMAT
        )

    def _parse_datetime(self, value):

        if value in (None, ""):
            return None

        try:
            return datetime.strptime(
                value,
                sg.DATETIME_FORMAT
            )
        except ValueError:
            return None

    def _calculate_remaining(
            self,
            tiempo_restante_actual,
            temporizador_activo_desde
    ):

        remaining = tiempo_restante_actual

        if remaining is None:
            remaining = 0

        started_at = self._parse_datetime(
            temporizador_activo_desde
        )

        if started_at is not None:
            elapsed = int(
                (
                    datetime.now()
                    -
                    started_at
                ).total_seconds()
            )
            remaining -= elapsed

        return max(
            0,
            remaining
        )

    def _pause_question_timer(
            self,
            id_partida
    ):

        partida = self.dao.cursor.execute(
            """
            SELECT
                tiempo_por_pregunta,
                tiempo_restante_actual,
                temporizador_activo_desde
            FROM partidas
            WHERE id_partida = ?;
            """,
            (id_partida,)
        ).fetchone()

        if partida is None:
            return False

        remaining_source = partida["tiempo_restante_actual"]

        if remaining_source is None:
            remaining_source = partida["tiempo_por_pregunta"]

        remaining = self._calculate_remaining(
            remaining_source,
            partida["temporizador_activo_desde"]
        )

        self.dao.cursor.execute(
            """
            UPDATE partidas
            SET
                tiempo_restante_actual = ?,
                temporizador_activo_desde = NULL,
                tiempo_agotado = CASE
                    WHEN ? <= 0 THEN 1
                    ELSE tiempo_agotado
                END
            WHERE id_partida = ?;
            """,
            (
                remaining,
                remaining,
                id_partida
            )
        )

        return True

    def _resume_question_timer(
            self,
            id_partida
    ):

        partida = self.dao.cursor.execute(
            """
            SELECT
                tiempo_por_pregunta,
                tiempo_restante_actual,
                estado
            FROM partidas
            WHERE id_partida = ?;
            """,
            (id_partida,)
        ).fetchone()

        if partida is None:
            return None

        remaining = partida["tiempo_restante_actual"]

        if remaining is None:
            remaining = partida["tiempo_por_pregunta"]

        if remaining <= 0:
            return self._timer_payload_from_values(
                partida["tiempo_por_pregunta"],
                0,
                None,
                1,
                partida["estado"]
            )

        active_since = self._now_text()

        self.dao.cursor.execute(
            """
            UPDATE partidas
            SET
                tiempo_restante_actual = ?,
                temporizador_activo_desde = ?,
                tiempo_agotado = 0
            WHERE id_partida = ?;
            """,
            (
                remaining,
                active_since,
                id_partida
            )
        )

        return self._timer_payload_from_values(
            partida["tiempo_por_pregunta"],
            remaining,
            active_since,
            0,
            partida["estado"]
        )

    def _rows_to_partidas(self, rows):

        partidas = []

        for row in rows:
            partidas.append(
                self._row_to_partida(row)
            )

        return partidas

    def insert(self, partida):

        if not self.dao.conectar():
            return False

        sql = """
        INSERT INTO partidas(
            codigo_partida,
            nombre,
            area,
            tiempo_por_pregunta,
            puntos_correcta,
            penalizacion_incorrecta,
            estado,
            pregunta_actual,
            fecha_creacion,
            tiempo_restante_actual,
            temporizador_activo_desde,
            tiempo_agotado
        )
        VALUES(
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        );
        """

        result = self.dao.ejecutar_sql(
            sql,
            (
                partida.get_codigo_partida(),
                partida.get_nombre(),
                partida.get_area(),
                partida.get_tiempo_por_pregunta(),
                partida.get_puntos_correcta(),
                partida.get_penalizacion_incorrecta(),
                partida.get_estado(),
                partida.get_pregunta_actual(),
                partida.get_fecha_creacion(),
                partida.get_tiempo_restante_actual(),
                partida.get_temporizador_activo_desde(),
                partida.get_tiempo_agotado()
            )
        )

        if result:
            partida.set_id_partida(
                self.dao.obtener_ultimo_id()
            )

        self.dao.cerrar()

        return result

    def update(self, partida):

        if not self.dao.conectar():
            return False

        sql = """
        UPDATE partidas
        SET
            codigo_partida = ?,
            nombre = ?,
            area = ?,
            tiempo_por_pregunta = ?,
            puntos_correcta = ?,
            penalizacion_incorrecta = ?,
            estado = ?,
            pregunta_actual = ?,
            fecha_creacion = ?,
            tiempo_restante_actual = ?,
            temporizador_activo_desde = ?,
            tiempo_agotado = ?
        WHERE id_partida = ?;
        """

        result = self.dao.ejecutar_sql(
            sql,
            (
                partida.get_codigo_partida(),
                partida.get_nombre(),
                partida.get_area(),
                partida.get_tiempo_por_pregunta(),
                partida.get_puntos_correcta(),
                partida.get_penalizacion_incorrecta(),
                partida.get_estado(),
                partida.get_pregunta_actual(),
                partida.get_fecha_creacion(),
                partida.get_tiempo_restante_actual(),
                partida.get_temporizador_activo_desde(),
                partida.get_tiempo_agotado(),
                partida.get_id_partida()
            )
        )

        self.dao.cerrar()

        return result

    def get_by_id(self, id_partida):

        if not self.dao.conectar():
            return None

        sql = f"""
        {self.BASE_SELECT}
        WHERE id_partida = ?;
        """

        row = self.dao.obtener_uno(
            sql,
            (id_partida,)
        )

        self.dao.cerrar()

        if row is None:
            return None

        return self._row_to_partida(row)

    def get_by_code(self, codigo_partida):

        if not self.dao.conectar():
            return None

        sql = f"""
        {self.BASE_SELECT}
        WHERE codigo_partida = ?;
        """

        row = self.dao.obtener_uno(
            sql,
            (codigo_partida,)
        )

        self.dao.cerrar()

        if row is None:
            return None

        return self._row_to_partida(row)

    def get_all(self):

        if not self.dao.conectar():
            return []

        sql = f"""
        {self.BASE_SELECT}
        ORDER BY id_partida DESC;
        """

        rows = self.dao.obtener_todos(sql)

        self.dao.cerrar()

        return self._rows_to_partidas(rows)

    def get_all_with_summary(self, owner=None):

        if not self.dao.conectar():
            return []

        where_owner = ""
        parametros = ()

        if owner:
            where_owner = "WHERE p.created_by = ?"
            parametros = (owner,)

        rows = self.dao.obtener_todos(
            f"""
            SELECT
                p.id_partida,
                p.codigo_partida,
                p.nombre,
                p.area,
                p.estado,
                p.fecha_creacion,
                p.tiempo_por_pregunta,
                p.puntos_correcta,
                p.penalizacion_incorrecta,
                p.pregunta_actual,
                COALESCE(
                    STRING_AGG(DISTINCT c.nombre, ', '),
                    ''
                ) AS cuestionarios,
                COALESCE(
                    STRING_AGG(DISTINCT m.nombre, ', '),
                    ''
                ) AS materias,
                COUNT(DISTINCT pp.id_partida_pregunta) AS total_preguntas,
                COUNT(DISTINCT pa.id_participante) AS total_participantes,
                COUNT(DISTINCT pa.id_participante)
                    FILTER (WHERE pa.conectado = 1) AS participantes_conectados
            FROM partidas p
            LEFT JOIN partida_cuestionarios pc
                ON pc.id_partida = p.id_partida
            LEFT JOIN cuestionarios c
                ON c.id_cuestionario = pc.id_cuestionario
            LEFT JOIN materias m
                ON m.id_materia = c.id_materia
            LEFT JOIN partida_preguntas pp
                ON pp.id_partida = p.id_partida
            LEFT JOIN participantes pa
                ON pa.id_partida = p.id_partida
            {where_owner}
            GROUP BY
                p.id_partida,
                p.codigo_partida,
                p.nombre,
                p.area,
                p.estado,
                p.fecha_creacion,
                p.tiempo_por_pregunta,
                p.puntos_correcta,
                p.penalizacion_incorrecta,
                p.pregunta_actual
            ORDER BY p.id_partida DESC;
            """,
            parametros
        )

        games = [
            dict(row)
            for row in rows
        ]

        self.dao.cerrar()

        return games

    def get_by_estado(self, estado):

        if not self.dao.conectar():
            return []

        sql = f"""
        {self.BASE_SELECT}
        WHERE estado = ?
        ORDER BY id_partida DESC;
        """

        rows = self.dao.obtener_todos(
            sql,
            (estado,)
        )

        self.dao.cerrar()

        return self._rows_to_partidas(rows)

    def get_by_estados(self, estados):

        if not estados:
            return []

        if not self.dao.conectar():
            return []

        placeholders = ",".join(
            "?"
            for _ in estados
        )

        sql = f"""
        {self.BASE_SELECT}
        WHERE estado IN ({placeholders})
        ORDER BY id_partida DESC;
        """

        rows = self.dao.obtener_todos(
            sql,
            tuple(estados)
        )

        self.dao.cerrar()

        return self._rows_to_partidas(rows)

    def get_statistics_games(
            self,
            estados
    ):

        if not estados:
            return []

        if not self.dao.conectar():
            return []

        placeholders = ",".join(
            "?"
            for _ in estados
        )

        rows = self.dao.obtener_todos(
            f"""
            SELECT
                p.id_partida,
                p.codigo_partida AS game_code,
                p.nombre AS game_name,
                p.estado AS game_state,
                p.pregunta_actual AS current_question,
                COUNT(
                    pp.id_partida_pregunta
                ) AS total_questions
            FROM partidas p
            LEFT JOIN partida_preguntas pp
                ON p.id_partida = pp.id_partida
            WHERE p.estado IN ({placeholders})
            GROUP BY
                p.id_partida,
                p.codigo_partida,
                p.nombre,
                p.estado,
                p.pregunta_actual,
                p.fecha_creacion
            ORDER BY
                (
                    SUBSTR(p.fecha_creacion, 7, 4)
                    || SUBSTR(p.fecha_creacion, 4, 2)
                    || SUBSTR(p.fecha_creacion, 1, 2)
                    || SUBSTR(p.fecha_creacion, 11)
                ) DESC,
                p.id_partida DESC;
            """,
            tuple(estados)
        )

        games = [
            dict(row)
            for row in rows
        ]

        self.dao.cerrar()

        return games

    def get_live_ranking(
            self,
            id_partida
    ):

        if not self.dao.conectar():
            return []

        rows = self.dao.obtener_todos(
            """
            SELECT
                id_participante,
                codigo_participante AS participant_code,
                sede,
                nombre,
                puntaje,
                conectado,
                estado
            FROM participantes
            WHERE id_partida = ?
            ORDER BY
                puntaje DESC,
                LOWER(sede) ASC,
                LOWER(nombre) ASC,
                id_participante ASC;
            """,
            (id_partida,)
        )

        ranking = [
            dict(row)
            for row in rows
        ]

        self.dao.cerrar()

        return ranking

    def get_last_game_event(
            self,
            id_partida
    ):

        if not self.dao.conectar():
            return None

        row = self.dao.obtener_uno(
            """
            SELECT
                p.sede,
                p.nombre,
                rp.resultado,
                rp.puntos_aplicados,
                rp.fecha_hora
            FROM respuestas_partida rp
            INNER JOIN participantes p
                ON rp.id_participante = p.id_participante
            WHERE rp.id_partida = ?
            ORDER BY rp.id_respuesta_partida DESC
            LIMIT 1;
            """,
            (id_partida,)
        )

        self.dao.cerrar()

        if row is None:
            return None

        return dict(row)

    def update_estado(
            self,
            id_partida,
            estado
    ):

        if not self.dao.conectar():
            return False

        sql = """
        UPDATE partidas
        SET
            estado = ?,
            temporizador_activo_desde = CASE
                WHEN ? IN (?, ?) THEN NULL
                ELSE temporizador_activo_desde
            END
        WHERE id_partida = ?;
        """

        result = self.dao.ejecutar_sql(
            sql,
            (
                estado,
                estado,
                sg.GAME_STATUS_FINISHED,
                sg.GAME_STATUS_CANCELLED,
                id_partida
            )
        )

        self.dao.cerrar()

        return result

    def update_pregunta_actual(
            self,
            id_partida,
            pregunta_actual
    ):

        if not self.dao.conectar():
            return False

        sql = """
        UPDATE partidas
        SET pregunta_actual = ?
        WHERE id_partida = ?;
        """

        result = self.dao.ejecutar_sql(
            sql,
            (
                pregunta_actual,
                id_partida
            )
        )

        self.dao.cerrar()

        return result

    def get_timer_status(
            self,
            id_partida
    ):

        if not self.dao.conectar():
            return None

        row = self.dao.obtener_uno(
            """
            SELECT
                tiempo_por_pregunta,
                tiempo_restante_actual,
                temporizador_activo_desde,
                tiempo_agotado,
                estado
            FROM partidas
            WHERE id_partida = ?;
            """,
            (id_partida,)
        )

        self.dao.cerrar()

        if row is None:
            return None

        remaining_source = row["tiempo_restante_actual"]

        if remaining_source is None:
            remaining_source = row["tiempo_por_pregunta"]

        remaining = remaining_source

        if (
                row["estado"] == sg.GAME_STATUS_IN_PROGRESS
                and row["temporizador_activo_desde"] is not None
        ):
            remaining = self._calculate_remaining(
                remaining_source,
                row["temporizador_activo_desde"]
            )

        exhausted = (
            row["tiempo_agotado"] == 1
            or remaining <= 0
        )

        return {
            "remaining": max(0, remaining),
            "exhausted": exhausted,
            "active_since": row["temporizador_activo_desde"],
            "game_state": row["estado"]
        }

    def _timer_payload_from_values(
            self,
            tiempo_por_pregunta,
            tiempo_restante_actual,
            temporizador_activo_desde,
            tiempo_agotado,
            estado
    ):

        remaining_source = tiempo_restante_actual

        if remaining_source is None:
            remaining_source = tiempo_por_pregunta

        remaining = remaining_source

        if (
                estado == sg.GAME_STATUS_IN_PROGRESS
                and temporizador_activo_desde is not None
        ):
            remaining = self._calculate_remaining(
                remaining_source,
                temporizador_activo_desde
            )

        return {
            "remaining": max(0, remaining),
            "exhausted": tiempo_agotado == 1 or remaining <= 0,
            "active_since": temporizador_activo_desde,
            "game_state": estado
        }

    def _question_payload_by_order(
            self,
            id_partida,
            numero_orden
    ):

        row = self.dao.cursor.execute(
            """
            SELECT
                pp.id_partida_pregunta,
                pp.id_partida,
                pp.id_pregunta,
                pp.numero_orden,
                pp.estado AS estado,
                pp.estado AS estado_partida_pregunta,

                p.enunciado,
                p.nombre_imagen AS nombre_imagen_pregunta,

                c.nombre AS nombre_cuestionario,

                ri.ruta AS ruta_pregunta,
                ri.descripcion AS descripcion_ruta_pregunta,

                r.descripcion AS respuesta_correcta,
                r.nombre_imagen AS nombre_imagen_respuesta,

                rir.ruta AS ruta_respuesta,
                rir.descripcion AS descripcion_ruta_respuesta

            FROM partida_preguntas pp

            INNER JOIN preguntas p
                ON pp.id_pregunta = p.id_pregunta

            INNER JOIN cuestionarios c
                ON p.id_cuestionario = c.id_cuestionario

            LEFT JOIN rutas_imagenes ri
                ON p.id_ruta_imagen = ri.id_ruta

            LEFT JOIN respuestas r
                ON p.id_pregunta = r.id_pregunta

            LEFT JOIN rutas_imagenes rir
                ON r.id_ruta_imagen = rir.id_ruta

            WHERE pp.id_partida = ?
            AND pp.numero_orden = ?
            LIMIT 1;
            """,
            (
                id_partida,
                numero_orden
            )
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    def _request_payload(
            self,
            id_solicitud
    ):

        row = self.dao.cursor.execute(
            """
            SELECT
                sp.id_solicitud,
                sp.id_partida,
                sp.id_partida_pregunta,
                sp.id_participante,
                sp.orden_solicitud,
                sp.fecha_hora,
                sp.estado,
                p.codigo_participante,
                p.nombre,
                p.sede,
                p.puntaje
            FROM solicitudes_palabra sp
            INNER JOIN participantes p
                ON sp.id_participante = p.id_participante
            WHERE sp.id_solicitud = ?;
            """,
            (id_solicitud,)
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    def _ranking_payload(
            self,
            id_partida
    ):

        rows = self.dao.cursor.execute(
            """
            SELECT
                id_participante,
                codigo_participante AS participant_code,
                sede,
                nombre,
                puntaje,
                conectado,
                estado
            FROM participantes
            WHERE id_partida = ?
            ORDER BY
                puntaje DESC,
                LOWER(sede) ASC,
                LOWER(nombre) ASC,
                id_participante ASC;
            """,
            (id_partida,)
        ).fetchall()

        return {
            "ranking": [
                dict(row)
                for row in rows
            ]
        }

    def start_game_transaction(
            self,
            id_partida
    ):

        if not self.dao.conectar():
            return False

        try:
            self.dao.cursor.execute(
                "BEGIN"
            )

            partida = self.dao.cursor.execute(
                """
                SELECT
                    estado,
                    pregunta_actual,
                    tiempo_por_pregunta,
                    tiempo_restante_actual,
                    temporizador_activo_desde,
                    tiempo_agotado
                FROM partidas
                WHERE id_partida = ?;
                """,
                (id_partida,)
            ).fetchone()

            if partida is None:
                self.dao.conexion.rollback()
                self.dao.cerrar()
                return False

            if partida["estado"] == sg.GAME_STATUS_IN_PROGRESS:
                question = self._question_payload_by_order(
                    id_partida,
                    partida["pregunta_actual"]
                )
                timer = self._timer_payload_from_values(
                    partida["tiempo_por_pregunta"],
                    partida["tiempo_restante_actual"],
                    partida["temporizador_activo_desde"],
                    partida["tiempo_agotado"],
                    partida["estado"]
                )
                self.dao.conexion.commit()
                self.dao.cerrar()
                return {
                    "question": question,
                    "timer": timer
                }

            current_question = partida["pregunta_actual"]

            if current_question <= 0:
                first_question = self.dao.cursor.execute(
                    """
                    SELECT numero_orden
                    FROM partida_preguntas
                    WHERE id_partida = ?
                    ORDER BY numero_orden
                    LIMIT 1;
                    """,
                    (id_partida,)
                ).fetchone()

                if first_question is None:
                    self.dao.conexion.rollback()
                    self.dao.cerrar()
                    return False

                current_question = first_question["numero_orden"]

                self.dao.cursor.execute(
                    """
                    UPDATE partida_preguntas
                    SET estado = ?
                    WHERE id_partida = ?
                    AND numero_orden = ?;
                    """,
                    (
                        sg.GAME_QUESTION_STATUS_CURRENT,
                        id_partida,
                        current_question
                    )
                )

            active_since = self._now_text()

            self.dao.cursor.execute(
                """
                UPDATE partidas
                SET
                    estado = ?,
                    pregunta_actual = ?,
                    tiempo_restante_actual = ?,
                    temporizador_activo_desde = ?,
                    tiempo_agotado = 0
                WHERE id_partida = ?;
                """,
                (
                    sg.GAME_STATUS_IN_PROGRESS,
                    current_question,
                    partida["tiempo_por_pregunta"],
                    active_since,
                    id_partida
                )
            )

            question = self._question_payload_by_order(
                id_partida,
                current_question
            )
            timer = self._timer_payload_from_values(
                partida["tiempo_por_pregunta"],
                partida["tiempo_por_pregunta"],
                active_since,
                0,
                sg.GAME_STATUS_IN_PROGRESS
            )

            self.dao.conexion.commit()
            self.dao.cerrar()
            return {
                "question": question,
                "timer": timer
            }

        except Exception as e:
            self.dao.conexion.rollback()
            print(f"Error al iniciar partida: {e}")
            self.dao.cerrar()
            return False

    def pause_game_transaction(
            self,
            id_partida
    ):

        if not self.dao.conectar():
            return False

        try:
            self.dao.cursor.execute(
                "BEGIN"
            )

            partida = self.dao.cursor.execute(
                """
                SELECT
                    estado,
                    tiempo_por_pregunta,
                    tiempo_restante_actual,
                    temporizador_activo_desde
                FROM partidas
                WHERE id_partida = ?;
                """,
                (id_partida,)
            ).fetchone()

            if partida is None:
                self.dao.conexion.rollback()
                self.dao.cerrar()
                return False

            remaining_source = partida["tiempo_restante_actual"]

            if remaining_source is None:
                remaining_source = partida["tiempo_por_pregunta"]

            remaining = self._calculate_remaining(
                remaining_source,
                partida["temporizador_activo_desde"]
            )

            self.dao.cursor.execute(
                """
                UPDATE partidas
                SET
                    estado = ?,
                    tiempo_restante_actual = ?,
                    temporizador_activo_desde = NULL,
                    tiempo_agotado = CASE
                        WHEN ? <= 0 THEN 1
                        ELSE tiempo_agotado
                    END
                WHERE id_partida = ?;
                """,
                (
                    sg.GAME_STATUS_PAUSED,
                    remaining,
                    remaining,
                    id_partida
                )
            )

            self.dao.conexion.commit()
            self.dao.cerrar()
            return True

        except Exception as e:
            self.dao.conexion.rollback()
            print(f"Error al pausar partida: {e}")
            self.dao.cerrar()
            return False

    def resume_game_transaction(
            self,
            id_partida
    ):

        if not self.dao.conectar():
            return False

        try:
            self.dao.cursor.execute(
                "BEGIN"
            )

            partida = self.dao.cursor.execute(
                """
                SELECT
                    tiempo_por_pregunta,
                    tiempo_restante_actual
                FROM partidas
                WHERE id_partida = ?;
                """,
                (id_partida,)
            ).fetchone()

            if partida is None:
                self.dao.conexion.rollback()
                self.dao.cerrar()
                return False

            remaining = partida["tiempo_restante_actual"]

            if remaining is None:
                remaining = partida["tiempo_por_pregunta"]

            self.dao.cursor.execute(
                """
                UPDATE partidas
                SET
                    estado = ?,
                    temporizador_activo_desde = ?
                WHERE id_partida = ?;
                """,
                (
                    sg.GAME_STATUS_IN_PROGRESS,
                    self._now_text(),
                    id_partida
                )
            )

            self.dao.conexion.commit()
            self.dao.cerrar()
            return True

        except Exception as e:
            self.dao.conexion.rollback()
            print(f"Error al reanudar partida: {e}")
            self.dao.cerrar()
            return False

    def create_game_transaction(
            self,
            partida,
            cuestionarios,
            preguntas
    ):

        if not self.dao.conectar():
            return None

        try:

            self.dao.cursor.execute(
                "BEGIN"
            )

            row = self.dao.cursor.execute(
                """
                INSERT INTO partidas(
                    codigo_partida,
                    nombre,
                    area,
                    tiempo_por_pregunta,
                    puntos_correcta,
                    penalizacion_incorrecta,
                    estado,
                    pregunta_actual,
                    fecha_creacion,
                    tiempo_restante_actual,
                    temporizador_activo_desde,
                    tiempo_agotado,
                    created_by
                )
                VALUES(
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                RETURNING id_partida;
                """,
                (
                    partida.get_codigo_partida(),
                    partida.get_nombre(),
                    partida.get_area(),
                    partida.get_tiempo_por_pregunta(),
                    partida.get_puntos_correcta(),
                    partida.get_penalizacion_incorrecta(),
                    partida.get_estado(),
                    partida.get_pregunta_actual(),
                    partida.get_fecha_creacion(),
                    partida.get_tiempo_restante_actual(),
                    partida.get_temporizador_activo_desde(),
                    partida.get_tiempo_agotado(),
                    current_owner()
                )
            ).fetchone()

            id_partida = row["id_partida"]

            if cuestionarios:
                self.dao.cursor.execute_values(
                    """
                    INSERT INTO partida_cuestionarios(
                        id_partida,
                        id_cuestionario
                    )
                    VALUES %s;
                    """,
                    [
                        (
                            id_partida,
                            cuestionario.get_id_cuestionario()
                        )
                        for cuestionario in cuestionarios
                    ]
                )

            if preguntas:
                self.dao.cursor.execute_values(
                    """
                    INSERT INTO partida_preguntas(
                        id_partida,
                        id_pregunta,
                        numero_orden,
                        estado
                    )
                    VALUES %s;
                    """,
                    [
                        (
                            id_partida,
                            pregunta.get_id_pregunta(),
                            index,
                            sg.GAME_QUESTION_STATUS_PENDING
                        )
                        for index, pregunta in enumerate(
                            preguntas,
                            start=1
                        )
                    ]
                )

            self.dao.conexion.commit()

            self.dao.cerrar()

            return id_partida

        except Exception as e:

            self.dao.conexion.rollback()

            print(
                f"Error al generar partida: {e}"
            )

            self.dao.cerrar()

            return None

    def get_total_questions(
            self,
            id_partida
    ):

        if not self.dao.conectar():
            return 0

        row = self.dao.obtener_uno(
            """
            SELECT COUNT(*)
            FROM partida_preguntas
            WHERE id_partida = ?;
            """,
            (id_partida,)
        )

        self.dao.cerrar()

        if row is None:
            return 0

        return row[0]

    def get_questions_by_game(
            self,
            id_partida
    ):

        if not self.dao.conectar():
            return []

        sql = """
        SELECT
            pp.id_partida_pregunta,
            pp.id_partida,
            pp.id_pregunta,
            pp.numero_orden,
            pp.estado AS estado,
            pp.estado AS estado_partida_pregunta,

            p.enunciado,
            p.nombre_imagen AS nombre_imagen_pregunta,

            c.nombre AS nombre_cuestionario,

            ri.ruta AS ruta_pregunta,
            ri.descripcion AS descripcion_ruta_pregunta,

            r.descripcion AS respuesta_correcta,
            r.nombre_imagen AS nombre_imagen_respuesta,

            rir.ruta AS ruta_respuesta,
            rir.descripcion AS descripcion_ruta_respuesta

        FROM partida_preguntas pp

        INNER JOIN preguntas p
            ON pp.id_pregunta = p.id_pregunta

        INNER JOIN cuestionarios c
            ON p.id_cuestionario = c.id_cuestionario

        LEFT JOIN rutas_imagenes ri
            ON p.id_ruta_imagen = ri.id_ruta

        LEFT JOIN respuestas r
            ON p.id_pregunta = r.id_pregunta

        LEFT JOIN rutas_imagenes rir
            ON r.id_ruta_imagen = rir.id_ruta

        WHERE pp.id_partida = ?
        ORDER BY pp.numero_orden;
        """

        rows = self.dao.obtener_todos(
            sql,
            (id_partida,)
        )

        questions = [
            dict(row)
            for row in rows
        ]

        self.dao.cerrar()

        return questions

    def get_current_question(
            self,
            id_partida
    ):

        if not self.dao.conectar():
            return None

        row = self.dao.obtener_uno(
            """
            SELECT
                pp.id_partida_pregunta,
                pp.id_partida,
                pp.id_pregunta,
                pp.numero_orden,
                pp.estado AS estado,
                pp.estado AS estado_partida_pregunta,

                p.enunciado,
                p.nombre_imagen AS nombre_imagen_pregunta,

                c.nombre AS nombre_cuestionario,

                ri.ruta AS ruta_pregunta,
                ri.descripcion AS descripcion_ruta_pregunta,

                r.descripcion AS respuesta_correcta,
                r.nombre_imagen AS nombre_imagen_respuesta,

                rir.ruta AS ruta_respuesta,
                rir.descripcion AS descripcion_ruta_respuesta

            FROM partidas pa

            INNER JOIN partida_preguntas pp
                ON pp.id_partida = pa.id_partida
                AND pp.numero_orden = pa.pregunta_actual

            INNER JOIN preguntas p
                ON pp.id_pregunta = p.id_pregunta

            INNER JOIN cuestionarios c
                ON p.id_cuestionario = c.id_cuestionario

            LEFT JOIN rutas_imagenes ri
                ON p.id_ruta_imagen = ri.id_ruta

            LEFT JOIN respuestas r
                ON p.id_pregunta = r.id_pregunta

            LEFT JOIN rutas_imagenes rir
                ON r.id_ruta_imagen = rir.id_ruta

            WHERE pa.id_partida = ?
            AND pa.pregunta_actual > 0
            LIMIT 1;
            """,
            (id_partida,)
        )

        self.dao.cerrar()

        if row is None:
            return None

        return dict(row)

    def get_question_by_order(
            self,
            id_partida,
            numero_orden
    ):

        if not self.dao.conectar():
            return None

        row = self.dao.obtener_uno(
            """
            SELECT
                pp.id_partida_pregunta,
                pp.id_partida,
                pp.id_pregunta,
                pp.numero_orden,
                pp.estado AS estado,
                pp.estado AS estado_partida_pregunta,

                p.enunciado,
                p.nombre_imagen AS nombre_imagen_pregunta,

                c.nombre AS nombre_cuestionario,

                ri.ruta AS ruta_pregunta,
                ri.descripcion AS descripcion_ruta_pregunta,

                r.descripcion AS respuesta_correcta,
                r.nombre_imagen AS nombre_imagen_respuesta,

                rir.ruta AS ruta_respuesta,
                rir.descripcion AS descripcion_ruta_respuesta

            FROM partida_preguntas pp

            INNER JOIN preguntas p
                ON pp.id_pregunta = p.id_pregunta

            INNER JOIN cuestionarios c
                ON p.id_cuestionario = c.id_cuestionario

            LEFT JOIN rutas_imagenes ri
                ON p.id_ruta_imagen = ri.id_ruta

            LEFT JOIN respuestas r
                ON p.id_pregunta = r.id_pregunta

            LEFT JOIN rutas_imagenes rir
                ON r.id_ruta_imagen = rir.id_ruta

            WHERE pp.id_partida = ?
            AND pp.numero_orden = ?
            LIMIT 1;
            """,
            (
                id_partida,
                numero_orden
            )
        )

        self.dao.cerrar()

        if row is None:
            return None

        return dict(row)

    def get_participants(
            self,
            id_partida
    ):

        if not self.dao.conectar():
            return []

        rows = self.dao.obtener_todos(
            """
            SELECT
                id_participante,
                id_partida,
                codigo_participante,
                nombre,
                sede,
                integrantes,
                puntaje,
                estado,
                conectado
            FROM participantes
            WHERE id_partida = ?
            ORDER BY sede, nombre;
            """,
            (id_partida,)
        )

        participants = [
            dict(row)
            for row in rows
        ]

        self.dao.cerrar()

        return participants

    def get_participant_by_code(
            self,
            id_partida,
            codigo_participante
    ):

        if not self.dao.conectar():
            return None

        row = self.dao.obtener_uno(
            """
            SELECT
                id_participante,
                id_partida,
                codigo_participante,
                nombre,
                sede,
                integrantes,
                puntaje,
                estado,
                conectado
            FROM participantes
            WHERE id_partida = ?
            AND codigo_participante = ?;
            """,
            (
                id_partida,
                codigo_participante
            )
        )

        self.dao.cerrar()

        if row is None:
            return None

        return dict(row)

    def get_participant_by_site(
            self,
            id_partida,
            sede
    ):

        if not self.dao.conectar():
            return None

        row = self.dao.obtener_uno(
            """
            SELECT
                id_participante,
                id_partida,
                codigo_participante,
                nombre,
                sede,
                integrantes,
                puntaje,
                estado,
                conectado
            FROM participantes
            WHERE id_partida = ?
            AND sede = ?;
            """,
            (
                id_partida,
                sede
            )
        )

        self.dao.cerrar()

        if row is None:
            return None

        return dict(row)

    def join_participant_transaction(
            self,
            id_partida,
            code_prefix,
            sede,
            nombre,
            integrantes=""
    ):

        if not self.dao.conectar():
            return {
                "success": False,
                "reason": "database"
            }

        try:
            self.dao.cursor.execute(
                "BEGIN"
            )

            game = self.dao.cursor.execute(
                """
                SELECT estado
                FROM partidas
                WHERE id_partida = ?;
                """,
                (id_partida,)
            ).fetchone()

            if (
                    game is None
                    or game["estado"] not in sg.RECOVERABLE_GAME_STATUS
            ):
                self.dao.conexion.rollback()
                self.dao.cerrar()
                return {
                    "success": False,
                    "reason": "game_unavailable"
                }

            participant = self.dao.cursor.execute(
                """
                SELECT
                    id_participante,
                    id_partida,
                    codigo_participante,
                    nombre,
                    sede,
                    integrantes,
                    puntaje,
                    estado,
                    conectado
                FROM participantes
                WHERE id_partida = ?
                AND sede = ?;
                """,
                (
                    id_partida,
                    sede
                )
            ).fetchone()

            reconnected = participant is not None

            if participant is not None:
                if participant["conectado"] == 1:
                    self.dao.conexion.rollback()
                    self.dao.cerrar()
                    return {
                        "success": False,
                        "reason": "already_connected"
                    }

                self.dao.cursor.execute(
                    """
                    UPDATE participantes
                    SET
                        estado = ?,
                        conectado = 1
                    WHERE id_participante = ?;
                    """,
                    (
                        sg.TEAM_STATUS_CONNECTED,
                        participant["id_participante"]
                    )
                )
            else:
                existing_codes = self.dao.cursor.execute(
                    """
                    SELECT codigo_participante
                    FROM participantes
                    WHERE id_partida = ?
                    AND codigo_participante LIKE ?;
                    """,
                    (
                        id_partida,
                        f"{code_prefix}-%"
                    )
                ).fetchall()

                sequence = 1

                for row in existing_codes:
                    try:
                        sequence = max(
                            sequence,
                            int(
                                row["codigo_participante"]
                                .rsplit("-", 1)[1]
                            ) + 1
                        )
                    except (IndexError, TypeError, ValueError):
                        continue

                participant_code = (
                    f"{code_prefix}-{sequence:03d}"
                )

                self.dao.cursor.execute(
                    """
                    INSERT INTO participantes(
                        id_partida,
                        codigo_participante,
                        nombre,
                        sede,
                        integrantes,
                        puntaje,
                        estado,
                        conectado
                    )
                    VALUES(?, ?, ?, ?, ?, 0, ?, 1);
                    """,
                    (
                        id_partida,
                        participant_code,
                        nombre,
                        sede,
                        integrantes,
                        sg.TEAM_STATUS_CONNECTED
                    )
                )

            participant = self.dao.cursor.execute(
                """
                SELECT
                    id_participante,
                    id_partida,
                    codigo_participante,
                    nombre,
                    sede,
                    integrantes,
                    puntaje,
                    estado,
                    conectado
                FROM participantes
                WHERE id_partida = ?
                AND sede = ?;
                """,
                (
                    id_partida,
                    sede
                )
            ).fetchone()

            self.dao.conexion.commit()
            result = dict(participant)
            self.dao.cerrar()

            return {
                "success": True,
                "participant": result,
                "reconnected": reconnected
            }

        except Exception as e:
            self.dao.conexion.rollback()
            print(f"Error al conectar participante: {e}")
            self.dao.cerrar()
            return {
                "success": False,
                "reason": "database"
            }

    def disconnect_participant(
            self,
            id_partida,
            codigo_participante
    ):

        if not self.dao.conectar():
            return False

        result = self.dao.ejecutar_sql(
            """
            UPDATE participantes
            SET
                estado = ?,
                conectado = 0
            WHERE id_partida = ?
            AND codigo_participante = ?;
            """,
            (
                sg.TEAM_STATUS_DISCONNECTED,
                id_partida,
                codigo_participante
            )
        )

        changed = (
            result
            and self.dao.cursor.rowcount > 0
        )

        self.dao.cerrar()
        return changed

    def delete_waiting_participant_transaction(
            self,
            id_partida,
            id_participante
    ):

        if not self.dao.conectar():
            return {
                "success": False,
                "reason": "database"
            }

        try:
            self.dao.cursor.execute(
                "BEGIN"
            )

            game = self.dao.cursor.execute(
                """
                SELECT estado
                FROM partidas
                WHERE id_partida = ?;
                """,
                (id_partida,)
            ).fetchone()

            if game is None:
                reason = "game_not_found"
            elif game["estado"] not in (
                    sg.GAME_STATUS_DRAFT,
                    sg.GAME_STATUS_WAITING
            ):
                reason = "invalid_game_state"
            else:
                reason = None

            participant = None

            if reason is None:
                participant = self.dao.cursor.execute(
                    """
                    SELECT id_participante
                    FROM participantes
                    WHERE id_partida = ?
                    AND id_participante = ?;
                    """,
                    (
                        id_partida,
                        id_participante
                    )
                ).fetchone()

                if participant is None:
                    reason = "participant_not_found"

            if reason is None:
                request_count = self.dao.cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM solicitudes_palabra
                    WHERE id_partida = ?
                    AND id_participante = ?;
                    """,
                    (
                        id_partida,
                        id_participante
                    )
                ).fetchone()[0]

                answer_count = self.dao.cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM respuestas_partida
                    WHERE id_partida = ?
                    AND id_participante = ?;
                    """,
                    (
                        id_partida,
                        id_participante
                    )
                ).fetchone()[0]

                if (
                        request_count > 0
                        or answer_count > 0
                ):
                    reason = "participant_has_history"

            if reason is not None:
                self.dao.conexion.rollback()
                self.dao.cerrar()
                return {
                    "success": False,
                    "reason": reason
                }

            self.dao.cursor.execute(
                """
                DELETE FROM participantes
                WHERE id_partida = ?
                AND id_participante = ?;
                """,
                (
                    id_partida,
                    id_participante
                )
            )

            if self.dao.cursor.rowcount == 0:
                self.dao.conexion.rollback()
                self.dao.cerrar()
                return {
                    "success": False,
                    "reason": "participant_not_found"
                }

            self.dao.conexion.commit()
            self.dao.cerrar()
            return {
                "success": True
            }

        except Exception as e:
            self.dao.conexion.rollback()
            print(f"Error al eliminar participante: {e}")
            self.dao.cerrar()
            return {
                "success": False,
                "reason": "database"
            }

    def get_participant_question_status(
            self,
            id_partida,
            id_partida_pregunta,
            id_participante
    ):

        if not self.dao.conectar():
            return None

        request = self.dao.obtener_uno(
            """
            SELECT
                id_solicitud,
                orden_solicitud,
                estado
            FROM solicitudes_palabra
            WHERE id_partida = ?
            AND id_partida_pregunta = ?
            AND id_participante = ?;
            """,
            (
                id_partida,
                id_partida_pregunta,
                id_participante
            )
        )

        answer = self.dao.obtener_uno(
            """
            SELECT resultado
            FROM respuestas_partida
            WHERE id_partida = ?
            AND id_partida_pregunta = ?
            AND id_participante = ?
            LIMIT 1;
            """,
            (
                id_partida,
                id_partida_pregunta,
                id_participante
            )
        )

        self.dao.cerrar()

        return {
            "request": (
                dict(request)
                if request is not None
                else None
            ),
            "has_answered": answer is not None
        }

    def request_word_transaction(
            self,
            id_partida,
            codigo_participante
    ):

        if not self.dao.conectar():
            return {
                "success": False,
                "reason": "database"
            }

        try:
            self.dao.cursor.execute(
                "BEGIN"
            )

            context = self.dao.cursor.execute(
                """
                SELECT
                    pa.estado AS game_state,
                    pa.pregunta_actual,
                    pa.tiempo_por_pregunta,
                    pa.tiempo_restante_actual,
                    pa.temporizador_activo_desde,
                    pa.tiempo_agotado,
                    pp.id_partida_pregunta,
                    pp.estado AS question_state,
                    p.id_participante,
                    p.conectado
                FROM partidas pa
                LEFT JOIN partida_preguntas pp
                    ON pp.id_partida = pa.id_partida
                    AND pp.numero_orden = pa.pregunta_actual
                LEFT JOIN participantes p
                    ON p.id_partida = pa.id_partida
                    AND p.codigo_participante = ?
                WHERE pa.id_partida = ?
                FOR UPDATE OF pa;
                """,
                (
                    codigo_participante,
                    id_partida
                )
            ).fetchone()

            if context is None:
                reason = "game_not_found"
            elif context["id_participante"] is None:
                reason = "participant_not_found"
            elif context["conectado"] != 1:
                reason = "participant_disconnected"
            elif context["game_state"] != sg.GAME_STATUS_IN_PROGRESS:
                reason = "game_not_in_progress"
            elif context["id_partida_pregunta"] is None:
                reason = "no_current_question"
            elif (
                    context["question_state"]
                    != sg.GAME_QUESTION_STATUS_CURRENT
            ):
                reason = "question_closed"
            else:
                remaining_source = (
                    context["tiempo_restante_actual"]
                )

                if remaining_source is None:
                    remaining_source = context[
                        "tiempo_por_pregunta"
                    ]

                remaining = self._calculate_remaining(
                    remaining_source,
                    context["temporizador_activo_desde"]
                )

                if (
                        context["tiempo_agotado"] == 1
                        or remaining <= 0
                ):
                    reason = "time_exhausted"
                else:
                    reason = None

            if reason is not None:
                self.dao.conexion.rollback()
                self.dao.cerrar()
                return {
                    "success": False,
                    "reason": reason
                }

            previous_request = self.dao.cursor.execute(
                """
                SELECT
                    orden_solicitud,
                    estado
                FROM solicitudes_palabra
                WHERE id_partida_pregunta = ?
                AND id_participante = ?;
                """,
                (
                    context["id_partida_pregunta"],
                    context["id_participante"]
                )
            ).fetchone()

            if previous_request is not None:
                self.dao.conexion.rollback()
                self.dao.cerrar()
                return {
                    "success": False,
                    "reason": "already_requested",
                    "request": dict(previous_request)
                }

            previous_answer = self.dao.cursor.execute(
                """
                SELECT COUNT(*)
                FROM respuestas_partida
                WHERE id_partida_pregunta = ?
                AND id_participante = ?;
                """,
                (
                    context["id_partida_pregunta"],
                    context["id_participante"]
                )
            ).fetchone()[0]

            if previous_answer > 0:
                self.dao.conexion.rollback()
                self.dao.cerrar()
                return {
                    "success": False,
                    "reason": "already_answered"
                }

            order = self.dao.cursor.execute(
                """
                SELECT COALESCE(MAX(orden_solicitud), 0) + 1
                FROM solicitudes_palabra
                WHERE id_partida_pregunta = ?;
                """,
                (
                    context["id_partida_pregunta"],
                )
            ).fetchone()[0]

            self.dao.cursor.execute(
                """
                INSERT INTO solicitudes_palabra(
                    id_partida,
                    id_partida_pregunta,
                    id_participante,
                    orden_solicitud,
                    fecha_hora,
                    estado
                )
                VALUES(?, ?, ?, ?, ?, ?);
                """,
                (
                    id_partida,
                    context["id_partida_pregunta"],
                    context["id_participante"],
                    order,
                    self._now_text(),
                    sg.WORD_REQUEST_STATUS_QUEUED
                )
            )

            request = self.dao.cursor.execute(
                """
                SELECT
                    sp.id_solicitud,
                    sp.id_partida,
                    sp.id_partida_pregunta,
                    sp.id_participante,
                    sp.orden_solicitud,
                    sp.fecha_hora,
                    sp.estado,
                    p.codigo_participante,
                    p.nombre,
                    p.sede
                FROM solicitudes_palabra sp
                INNER JOIN participantes p
                    ON sp.id_participante = p.id_participante
                WHERE sp.id_partida_pregunta = ?
                AND sp.id_participante = ?;
                """,
                (
                    context["id_partida_pregunta"],
                    context["id_participante"]
                )
            ).fetchone()

            queue = self.dao.cursor.execute(
                """
                SELECT
                    sp.id_solicitud,
                    sp.id_partida,
                    sp.id_partida_pregunta,
                    sp.id_participante,
                    sp.orden_solicitud,
                    sp.fecha_hora,
                    sp.estado,
                    p.codigo_participante,
                    p.nombre,
                    p.sede,
                    p.puntaje
                FROM solicitudes_palabra sp
                INNER JOIN participantes p
                    ON sp.id_participante = p.id_participante
                WHERE sp.id_partida_pregunta = ?
                AND sp.estado IN (?, ?)
                ORDER BY sp.orden_solicitud ASC;
                """,
                (
                    context["id_partida_pregunta"],
                    sg.WORD_REQUEST_STATUS_QUEUED,
                    sg.WORD_REQUEST_STATUS_TURN
                )
            ).fetchall()

            self.dao.conexion.commit()
            self.dao.cerrar()

            return {
                "success": True,
                "request_order": order,
                "request_status": sg.WORD_REQUEST_STATUS_QUEUED,
                "request": dict(request) if request is not None else None,
                "queue": [
                    dict(row)
                    for row in queue
                ]
            }

        except Exception as e:
            self.dao.conexion.rollback()
            print(f"Error al solicitar la palabra: {e}")
            self.dao.cerrar()
            return {
                "success": False,
                "reason": "database"
            }

    def get_word_requests(
            self,
            id_partida
    ):

        if not self.dao.conectar():
            return []

        rows = self.dao.obtener_todos(
            """
            SELECT
                sp.id_solicitud,
                sp.id_partida,
                sp.id_partida_pregunta,
                sp.id_participante,
                sp.orden_solicitud,
                sp.fecha_hora,
                sp.estado,
                p.codigo_participante,
                p.nombre,
                p.sede
            FROM solicitudes_palabra sp
            INNER JOIN participantes p
                ON sp.id_participante = p.id_participante
            WHERE sp.id_partida = ?
            ORDER BY
                sp.id_partida_pregunta,
                sp.orden_solicitud;
            """,
            (id_partida,)
        )

        word_requests = [
            dict(row)
            for row in rows
        ]

        self.dao.cerrar()

        return word_requests

    def get_word_request_by_id(
            self,
            id_solicitud
    ):

        if not self.dao.conectar():
            return None

        row = self.dao.obtener_uno(
            """
            SELECT
                sp.id_solicitud,
                sp.id_partida,
                sp.id_partida_pregunta,
                sp.id_participante,
                sp.orden_solicitud,
                sp.fecha_hora,
                sp.estado,
                p.codigo_participante,
                p.nombre,
                p.sede
            FROM solicitudes_palabra sp
            INNER JOIN participantes p
                ON sp.id_participante = p.id_participante
            WHERE sp.id_solicitud = ?;
            """,
            (id_solicitud,)
        )

        self.dao.cerrar()

        if row is None:
            return None

        return dict(row)

    def give_word_transaction(
            self,
            id_solicitud
    ):

        if not self.dao.conectar():
            return False

        try:
            self.dao.cursor.execute(
                "BEGIN"
            )

            request = self.dao.cursor.execute(
                """
                SELECT
                    id_solicitud,
                    id_partida,
                    id_partida_pregunta,
                    estado
                FROM solicitudes_palabra
                WHERE id_solicitud = ?;
                """,
                (id_solicitud,)
            ).fetchone()

            if (
                    request is None
                    or request["estado"]
                    != sg.WORD_REQUEST_STATUS_QUEUED
            ):
                self.dao.conexion.rollback()
                self.dao.cerrar()
                return False

            active_turn = self.dao.cursor.execute(
                """
                SELECT COUNT(*)
                FROM solicitudes_palabra
                WHERE id_partida = ?
                AND id_partida_pregunta = ?
                AND estado = ?;
                """,
                (
                    request["id_partida"],
                    request["id_partida_pregunta"],
                    sg.WORD_REQUEST_STATUS_TURN
                )
            ).fetchone()[0]

            if active_turn > 0:
                self.dao.conexion.rollback()
                self.dao.cerrar()
                return False

            self.dao.cursor.execute(
                """
                UPDATE solicitudes_palabra
                SET estado = ?
                WHERE id_solicitud = ?;
                """,
                (
                    sg.WORD_REQUEST_STATUS_TURN,
                    id_solicitud
                )
            )

            if not self._pause_question_timer(
                    request["id_partida"]
            ):
                self.dao.conexion.rollback()
                self.dao.cerrar()
                return False

            updated_request = self._request_payload(id_solicitud)
            timer_row = self.dao.cursor.execute(
                """
                SELECT
                    tiempo_por_pregunta,
                    tiempo_restante_actual,
                    temporizador_activo_desde,
                    tiempo_agotado,
                    estado
                FROM partidas
                WHERE id_partida = ?;
                """,
                (request["id_partida"],)
            ).fetchone()
            timer = None

            if timer_row is not None:
                timer = self._timer_payload_from_values(
                    timer_row["tiempo_por_pregunta"],
                    timer_row["tiempo_restante_actual"],
                    timer_row["temporizador_activo_desde"],
                    timer_row["tiempo_agotado"],
                    timer_row["estado"]
                )

            self.dao.conexion.commit()
            self.dao.cerrar()

            return {
                "request": updated_request,
                "timer": timer
            }

        except Exception as e:
            self.dao.conexion.rollback()
            print(f"Error al dar palabra: {e}")
            self.dao.cerrar()
            return False

    def mark_time_expired_transaction(
            self,
            id_partida
    ):

        if not self.dao.conectar():
            return False

        try:
            self.dao.cursor.execute(
                "BEGIN"
            )

            partida = self.dao.cursor.execute(
                """
                SELECT
                    pregunta_actual
                FROM partidas
                WHERE id_partida = ?;
                """,
                (id_partida,)
            ).fetchone()

            if partida is None:
                self.dao.conexion.rollback()
                self.dao.cerrar()
                return False

            current_question = self.dao.cursor.execute(
                """
                SELECT
                    id_partida_pregunta,
                    estado
                FROM partida_preguntas
                WHERE id_partida = ?
                AND numero_orden = ?;
                """,
                (
                    id_partida,
                    partida["pregunta_actual"]
                )
            ).fetchone()

            if current_question is not None:
                correct_count = self.dao.cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM respuestas_partida
                    WHERE id_partida_pregunta = ?
                    AND resultado = ?;
                    """,
                    (
                        current_question["id_partida_pregunta"],
                        sg.GAME_ANSWER_RESULT_CORRECT
                    )
                ).fetchone()[0]

                if correct_count == 0:
                    self.dao.cursor.execute(
                        """
                        UPDATE partida_preguntas
                        SET estado = ?
                        WHERE id_partida_pregunta = ?;
                        """,
                        (
                            sg.GAME_QUESTION_STATUS_NO_ANSWER,
                            current_question["id_partida_pregunta"]
                        )
                    )

            self.dao.cursor.execute(
                """
                UPDATE partidas
                SET
                    tiempo_restante_actual = 0,
                    temporizador_activo_desde = NULL,
                    tiempo_agotado = 1
                WHERE id_partida = ?;
                """,
                (id_partida,)
            )

            self.dao.conexion.commit()
            self.dao.cerrar()
            return True

        except Exception as e:
            self.dao.conexion.rollback()
            print(f"Error al marcar tiempo agotado: {e}")
            self.dao.cerrar()
            return False

    def mark_word_request_result_transaction(
            self,
            id_solicitud,
            resultado,
            puntos_aplicados
    ):

        if not self.dao.conectar():
            return False

        try:
            self.dao.cursor.execute(
                "BEGIN"
            )

            request = self.dao.cursor.execute(
                """
                SELECT
                    id_solicitud,
                    id_partida,
                    id_partida_pregunta,
                    id_participante,
                    estado
                FROM solicitudes_palabra
                WHERE id_solicitud = ?;
                """,
                (id_solicitud,)
            ).fetchone()

            if (
                    request is None
                    or request["estado"]
                    != sg.WORD_REQUEST_STATUS_TURN
            ):
                self.dao.conexion.rollback()
                self.dao.cerrar()
                return False

            previous_answer = self.dao.cursor.execute(
                """
                SELECT COUNT(*)
                FROM respuestas_partida
                WHERE id_partida_pregunta = ?
                AND id_participante = ?;
                """,
                (
                    request["id_partida_pregunta"],
                    request["id_participante"]
                )
            ).fetchone()[0]

            if previous_answer > 0:
                self.dao.conexion.rollback()
                self.dao.cerrar()
                return False

            self.dao.cursor.execute(
                """
                INSERT INTO respuestas_partida(
                    id_partida,
                    id_partida_pregunta,
                    id_participante,
                    resultado,
                    puntos_aplicados,
                    fecha_hora
                )
                VALUES(
                    ?, ?, ?, ?, ?, ?
                );
                """,
                (
                    request["id_partida"],
                    request["id_partida_pregunta"],
                    request["id_participante"],
                    resultado,
                    puntos_aplicados,
                    datetime.now().strftime(
                        "%d/%m/%Y %H:%M:%S"
                    )
                )
            )

            self.dao.cursor.execute(
                """
                UPDATE participantes
                SET puntaje = puntaje + ?
                WHERE id_participante = ?;
                """,
                (
                    puntos_aplicados,
                    request["id_participante"]
                )
            )

            new_status = sg.WORD_REQUEST_STATUS_CORRECT

            if resultado == sg.GAME_ANSWER_RESULT_INCORRECT:
                new_status = sg.WORD_REQUEST_STATUS_INCORRECT

            self.dao.cursor.execute(
                """
                UPDATE solicitudes_palabra
                SET estado = ?
                WHERE id_solicitud = ?;
                """,
                (
                    new_status,
                    id_solicitud
                )
            )

            if resultado == sg.GAME_ANSWER_RESULT_CORRECT:
                self.dao.cursor.execute(
                    """
                    UPDATE partida_preguntas
                    SET estado = ?
                    WHERE id_partida_pregunta = ?;
                    """,
                    (
                        sg.GAME_QUESTION_STATUS_ANSWERED,
                        request["id_partida_pregunta"]
                    )
                )

                self.dao.cursor.execute(
                    """
                    UPDATE solicitudes_palabra
                    SET estado = ?
                    WHERE id_partida_pregunta = ?
                    AND estado = ?;
                    """,
                    (
                        sg.WORD_REQUEST_STATUS_CANCELLED,
                        request["id_partida_pregunta"],
                        sg.WORD_REQUEST_STATUS_QUEUED
                    )
                )
            else:
                self.dao.cursor.execute(
                    """
                    UPDATE partida_preguntas
                    SET estado = ?
                    WHERE id_partida_pregunta = ?;
                    """,
                    (
                        sg.GAME_QUESTION_STATUS_CURRENT,
                        request["id_partida_pregunta"]
                    )
                )
                timer = self._resume_question_timer(
                    request["id_partida"]
                )

            updated_request = self._request_payload(id_solicitud)
            affected_requests = self.dao.cursor.execute(
                """
                SELECT
                    sp.id_solicitud,
                    sp.id_partida,
                    sp.id_partida_pregunta,
                    sp.id_participante,
                    sp.orden_solicitud,
                    sp.fecha_hora,
                    sp.estado,
                    p.codigo_participante,
                    p.nombre,
                    p.sede,
                    p.puntaje
                FROM solicitudes_palabra sp
                INNER JOIN participantes p
                    ON sp.id_participante = p.id_participante
                WHERE sp.id_partida_pregunta = ?
                AND sp.estado IN (?, ?, ?, ?, ?)
                ORDER BY sp.orden_solicitud;
                """,
                (
                    request["id_partida_pregunta"],
                    sg.WORD_REQUEST_STATUS_QUEUED,
                    sg.WORD_REQUEST_STATUS_TURN,
                    sg.WORD_REQUEST_STATUS_CORRECT,
                    sg.WORD_REQUEST_STATUS_INCORRECT,
                    sg.WORD_REQUEST_STATUS_CANCELLED
                )
            ).fetchall()
            ranking = self._ranking_payload(request["id_partida"])

            self.dao.conexion.commit()
            self.dao.cerrar()

            return {
                "request": updated_request,
                "affected_requests": [
                    dict(row)
                    for row in affected_requests
                ],
                "ranking": ranking,
                "resultado": resultado,
                "puntos_aplicados": puntos_aplicados,
                "timer": timer if resultado == sg.GAME_ANSWER_RESULT_INCORRECT else None
            }

        except Exception as e:
            self.dao.conexion.rollback()
            print(f"Error al registrar respuesta de partida: {e}")
            self.dao.cerrar()
            return False

    def pass_word_transaction(
            self,
            id_solicitud
    ):

        if not self.dao.conectar():
            return False

        try:
            self.dao.cursor.execute(
                "BEGIN"
            )

            request = self.dao.cursor.execute(
                """
                SELECT
                    id_solicitud,
                    id_partida,
                    id_partida_pregunta,
                    orden_solicitud,
                    estado
                FROM solicitudes_palabra
                WHERE id_solicitud = ?;
                """,
                (id_solicitud,)
            ).fetchone()

            if (
                    request is None
                    or request["estado"]
                    != sg.WORD_REQUEST_STATUS_TURN
            ):
                self.dao.conexion.rollback()
                self.dao.cerrar()
                return False

            self.dao.cursor.execute(
                """
                UPDATE solicitudes_palabra
                SET estado = ?
                WHERE id_solicitud = ?;
                """,
                (
                    sg.WORD_REQUEST_STATUS_CANCELLED,
                    id_solicitud
                )
            )

            next_request = self.dao.cursor.execute(
                """
                SELECT id_solicitud
                FROM solicitudes_palabra
                WHERE id_partida = ?
                AND id_partida_pregunta = ?
                AND estado = ?
                ORDER BY orden_solicitud
                LIMIT 1;
                """,
                (
                    request["id_partida"],
                    request["id_partida_pregunta"],
                    sg.WORD_REQUEST_STATUS_QUEUED
                )
            ).fetchone()

            if next_request is not None:
                self.dao.cursor.execute(
                    """
                    UPDATE solicitudes_palabra
                    SET estado = ?
                    WHERE id_solicitud = ?;
                    """,
                    (
                        sg.WORD_REQUEST_STATUS_TURN,
                        next_request["id_solicitud"]
                    )
                )

            self.dao.conexion.commit()
            self.dao.cerrar()

            return True

        except Exception as e:
            self.dao.conexion.rollback()
            print(f"Error al pasar palabra: {e}")
            self.dao.cerrar()
            return False

    def advance_question_transaction(
            self,
            id_partida,
            next_order
    ):

        if not self.dao.conectar():
            return False

        try:

            self.dao.cursor.execute(
                "BEGIN"
            )

            row = self.dao.cursor.execute(
                """
                SELECT
                    pregunta_actual,
                    tiempo_por_pregunta,
                    estado
                FROM partidas
                WHERE id_partida = ?;
                """,
                (id_partida,)
            ).fetchone()

            if row is None:
                self.dao.conexion.rollback()
                self.dao.cerrar()
                return False

            current_order = row["pregunta_actual"]

            if current_order > 0:
                current_partida_pregunta = self.dao.cursor.execute(
                    """
                    SELECT id_partida_pregunta
                    FROM partida_preguntas
                    WHERE id_partida = ?
                    AND numero_orden = ?;
                    """,
                    (
                        id_partida,
                        current_order
                    )
                ).fetchone()

                previous_status = (
                    sg.GAME_QUESTION_STATUS_NO_ANSWER
                )

                if current_partida_pregunta is not None:
                    correct_count = self.dao.cursor.execute(
                        """
                        SELECT COUNT(*)
                        FROM respuestas_partida
                        WHERE id_partida_pregunta = ?
                        AND resultado = ?;
                        """,
                        (
                            current_partida_pregunta[
                                "id_partida_pregunta"
                            ],
                            sg.GAME_ANSWER_RESULT_CORRECT
                        )
                    ).fetchone()[0]

                    if correct_count > 0:
                        previous_status = (
                            sg.GAME_QUESTION_STATUS_ANSWERED
                        )

                self.dao.cursor.execute(
                    """
                    UPDATE partida_preguntas
                    SET estado = ?
                    WHERE id_partida = ?
                    AND numero_orden = ?;
                    """,
                    (
                        previous_status,
                        id_partida,
                        current_order
                    )
                )

            self.dao.cursor.execute(
                """
                UPDATE partida_preguntas
                SET estado = ?
                WHERE id_partida = ?
                AND numero_orden = ?;
                """,
                (
                    sg.GAME_QUESTION_STATUS_CURRENT,
                    id_partida,
                    next_order
                )
            )

            if self.dao.cursor.rowcount == 0:
                self.dao.conexion.rollback()
                self.dao.cerrar()
                return False

            active_since = self._now_text()

            self.dao.cursor.execute(
                """
                UPDATE partidas
                SET
                    pregunta_actual = ?,
                    tiempo_restante_actual = ?,
                    temporizador_activo_desde = CASE
                        WHEN estado = ? THEN ?
                        ELSE NULL
                    END,
                    tiempo_agotado = 0
                WHERE id_partida = ?;
                """,
                (
                    next_order,
                    row["tiempo_por_pregunta"],
                    sg.GAME_STATUS_IN_PROGRESS,
                    active_since,
                    id_partida
                )
            )

            question = self._question_payload_by_order(
                id_partida,
                next_order
            )
            timer = self._timer_payload_from_values(
                row["tiempo_por_pregunta"],
                row["tiempo_por_pregunta"],
                active_since,
                0,
                sg.GAME_STATUS_IN_PROGRESS
            )

            self.dao.conexion.commit()

            self.dao.cerrar()

            return {
                "question": question,
                "timer": timer
            }

        except Exception as e:

            self.dao.conexion.rollback()

            print(
                f"Error al avanzar pregunta: {e}"
            )

            self.dao.cerrar()

            return False

