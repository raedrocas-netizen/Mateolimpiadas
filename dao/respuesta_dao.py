from dao.dao import Dao

from data_representation.respuesta import Respuesta
from data_representation.pregunta import Pregunta
from data_representation.cuestionario import Cuestionario
from data_representation.ruta_imagen import RutaImagen

import helper.super_global as sg


class RespuestaDao:

    BASE_SELECT = """
    SELECT
        r.id_respuesta,
        r.descripcion,
        r.id_ruta_imagen,
        r.nombre_imagen,

        p.id_pregunta,
        p.enunciado,
        p.id_cuestionario,
        p.nombre_imagen AS nombre_imagen_pregunta,

        c.nombre AS nombre_cuestionario,

        ri.descripcion AS descripcion_ruta,
        ri.ruta AS ruta_imagen

    FROM respuestas r

    INNER JOIN preguntas p
        ON r.id_pregunta = p.id_pregunta

    INNER JOIN cuestionarios c
        ON p.id_cuestionario = c.id_cuestionario

    LEFT JOIN rutas_imagenes ri
        ON r.id_ruta_imagen = ri.id_ruta
    """

    def __init__(self):
        self.dao = Dao(sg.FULL_PATH)

    def _get_base_select(self):
        return self.BASE_SELECT

    def _row_to_respuesta(self, row):

        cuestionario = Cuestionario()

        cuestionario.set_id_cuestionario(
            row["id_cuestionario"]
        )

        cuestionario.set_nombre(
            row["nombre_cuestionario"]
        )

        pregunta = Pregunta()

        pregunta.set_id_pregunta(
            row["id_pregunta"]
        )

        pregunta.set_cuestionario(
            cuestionario
        )

        pregunta.set_enunciado(
            row["enunciado"]
        )

        pregunta.set_nombre_imagen(
            row["nombre_imagen_pregunta"] or ""
        )

        ruta_imagen = None

        if row["id_ruta_imagen"] is not None:

            ruta_imagen = RutaImagen()

            ruta_imagen.set_id_ruta(
                row["id_ruta_imagen"]
            )

            ruta_imagen.set_descripcion(
                row["descripcion_ruta"]
            )

            ruta_imagen.set_ruta(
                row["ruta_imagen"]
            )

        respuesta = Respuesta()

        respuesta.set_id_respuesta(
            row["id_respuesta"]
        )

        respuesta.set_pregunta(
            pregunta
        )

        respuesta.set_descripcion(
            row["descripcion"]
        )

        respuesta.set_ruta_imagen(
            ruta_imagen
        )

        respuesta.set_nombre_imagen(
            row["nombre_imagen"] or ""
        )

        return respuesta

    def insert(self, respuesta):

        if not self.dao.conectar():
            return False

        sql = """
        INSERT INTO respuestas(
            id_pregunta,
            descripcion,
            id_ruta_imagen,
            nombre_imagen
        )
        VALUES(
            ?, ?, ?, ?
        );
        """

        id_ruta = None

        if respuesta.get_ruta_imagen() is not None:
            id_ruta = (
                respuesta
                .get_ruta_imagen()
                .get_id_ruta()
            )

        result = self.dao.ejecutar_sql(
            sql,
            (
                respuesta.get_pregunta()
                .get_id_pregunta(),
                respuesta.get_descripcion(),
                id_ruta,
                respuesta.get_nombre_imagen()
            )
        )

        if result:
            respuesta.set_id_respuesta(
                self.dao.obtener_ultimo_id()
            )

        self.dao.cerrar()

        return result

    def get_by_id(self, id_respuesta):

        if not self.dao.conectar():
            return None

        sql = f"""
        {self._get_base_select()}
        WHERE r.id_respuesta = ?;
        """

        row = self.dao.obtener_uno(
            sql,
            (id_respuesta,)
        )

        self.dao.cerrar()

        if row is None:
            return None

        return self._row_to_respuesta(row)

    def get_by_pregunta(self, id_pregunta):

        if not self.dao.conectar():
            return None

        sql = f"""
        {self._get_base_select()}
        WHERE r.id_pregunta = ?;
        """

        row = self.dao.obtener_uno(
            sql,
            (id_pregunta,)
        )

        self.dao.cerrar()

        if row is None:
            return None

        return self._row_to_respuesta(row)

    def get_all(self):

        if not self.dao.conectar():
            return []

        sql = f"""
        {self._get_base_select()}
        ORDER BY r.id_respuesta;
        """

        rows = self.dao.obtener_todos(sql)

        self.dao.cerrar()

        return [
            self._row_to_respuesta(row)
            for row in rows
        ]

    def get_by_cuestionario(
            self,
            id_cuestionario
    ):

        if not self.dao.conectar():
            return []

        sql = f"""
        {self._get_base_select()}
        WHERE p.id_cuestionario = ?
        ORDER BY p.id_pregunta;
        """

        rows = self.dao.obtener_todos(
            sql,
            (id_cuestionario,)
        )

        self.dao.cerrar()

        return [
            self._row_to_respuesta(row)
            for row in rows
        ]

    def update(self, respuesta):

        if not self.dao.conectar():
            return False

        sql = """
        UPDATE respuestas
        SET
            id_pregunta = ?,
            descripcion = ?,
            id_ruta_imagen = ?,
            nombre_imagen = ?
        WHERE id_respuesta = ?;
        """

        id_ruta = None

        if respuesta.get_ruta_imagen() is not None:
            id_ruta = (
                respuesta
                .get_ruta_imagen()
                .get_id_ruta()
            )

        result = self.dao.ejecutar_sql(
            sql,
            (
                respuesta.get_pregunta()
                .get_id_pregunta(),
                respuesta.get_descripcion(),
                id_ruta,
                respuesta.get_nombre_imagen(),
                respuesta.get_id_respuesta()
            )
        )

        self.dao.cerrar()

        return result

    def delete(self, id_respuesta):

        if not self.dao.conectar():
            return False

        sql = """
        DELETE FROM respuestas
        WHERE id_respuesta = ?;
        """

        result = self.dao.ejecutar_sql(
            sql,
            (id_respuesta,)
        )

        self.dao.cerrar()

        return result

    def count_by_route(
            self,
            id_ruta,
            exclude_id_respuesta=None
    ):

        if not self.dao.conectar():
            return 0

        sql = """
        SELECT COUNT(*)
        FROM respuestas
        WHERE id_ruta_imagen = ?
        """

        parametros = [id_ruta]

        if exclude_id_respuesta is not None:

            sql += """
            AND id_respuesta != ?
            """

            parametros.append(
                exclude_id_respuesta
            )

        row = self.dao.obtener_uno(
            sql,
            tuple(parametros)
        )

        self.dao.cerrar()

        if row is None:
            return 0

        return row[0]

    def update_shared_route(
            self,
            old_id_ruta,
            new_id_ruta,
            exclude_id_respuesta
    ):

        if not self.dao.conectar():
            return False

        sql = """
        UPDATE respuestas
        SET
            id_ruta_imagen = ?,
            nombre_imagen = CASE
                WHEN ? IS NULL THEN ''
                ELSE nombre_imagen
            END
        WHERE id_ruta_imagen = ?
        AND id_respuesta != ?;
        """

        result = self.dao.ejecutar_sql(
            sql,
            (
                new_id_ruta,
                new_id_ruta,
                old_id_ruta,
                exclude_id_respuesta
            )
        )

        self.dao.cerrar()

        return result
