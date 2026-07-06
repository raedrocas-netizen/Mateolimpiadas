from dao.dao import Dao

from data_representation.pregunta import Pregunta
from data_representation.cuestionario import Cuestionario
from data_representation.ruta_imagen import RutaImagen

import helper.super_global as sg


class PreguntaDao:

    BASE_SELECT = """
    SELECT
        p.id_pregunta,
        p.enunciado,
        p.id_ruta_imagen,
        p.nombre_imagen,

        c.id_cuestionario,
        c.nombre AS nombre_cuestionario,
        c.area,
        c.estado,
        c.fecha_creacion,

        r.descripcion AS descripcion_ruta,
        r.ruta AS ruta_imagen

    FROM preguntas p

    INNER JOIN cuestionarios c
        ON p.id_cuestionario = c.id_cuestionario

    LEFT JOIN rutas_imagenes r
        ON p.id_ruta_imagen = r.id_ruta
    """

    def __init__(self):
        self.dao = Dao(sg.FULL_PATH)

    def _get_base_select(self):
        return self.BASE_SELECT

    def _row_to_pregunta(self, row):

        cuestionario = Cuestionario()

        cuestionario.set_id_cuestionario(
            row["id_cuestionario"]
        )

        cuestionario.set_nombre(
            row["nombre_cuestionario"]
        )

        cuestionario.set_area(
            row["area"]
        )

        cuestionario.set_estado(
            row["estado"]
        )

        cuestionario.set_fecha_creacion(
            row["fecha_creacion"]
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

        pregunta.set_ruta_imagen(
            ruta_imagen
        )

        pregunta.set_nombre_imagen(
            row["nombre_imagen"] or ""
        )

        return pregunta

    def insert(self, pregunta):

        if not self.dao.conectar():
            return False

        sql = """
        INSERT INTO preguntas(
            id_cuestionario,
            enunciado,
            id_ruta_imagen,
            nombre_imagen
        )
        VALUES(
            ?, ?, ?, ?
        )
        RETURNING id_pregunta;
        """

        id_ruta = None

        if pregunta.get_ruta_imagen() is not None:
            id_ruta = (
                pregunta
                .get_ruta_imagen()
                .get_id_ruta()
            )

        try:
            row = self.dao.cursor.execute(
                sql,
                (
                    pregunta.get_cuestionario()
                    .get_id_cuestionario(),

                    pregunta.get_enunciado(),

                    id_ruta,

                    pregunta.get_nombre_imagen()
                )
            ).fetchone()
            self.dao.conexion.commit()
            pregunta.set_id_pregunta(
                row["id_pregunta"]
            )
            result = True
        except Exception as e:
            self.dao.conexion.rollback()
            print(f"Error al insertar pregunta: {e}")
            result = False

        self.dao.cerrar()

        return result

    def get_by_id(self, id_pregunta):

        if not self.dao.conectar():
            return None

        sql = f"""
        {self._get_base_select()}
        WHERE p.id_pregunta = ?;
        """

        row = self.dao.obtener_uno(
            sql,
            (id_pregunta,)
        )

        self.dao.cerrar()

        if row is None:
            return None

        return self._row_to_pregunta(row)

    def get_all(self):

        if not self.dao.conectar():
            return []

        sql = f"""
        {self._get_base_select()}
        ORDER BY p.id_pregunta;
        """

        rows = self.dao.obtener_todos(sql)

        self.dao.cerrar()

        preguntas = []

        for row in rows:
            preguntas.append(
                self._row_to_pregunta(row)
            )

        return preguntas

    def get_by_cuestionario(self, id_cuestionario):

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

        preguntas = []

        for row in rows:
            preguntas.append(
                self._row_to_pregunta(row)
            )

        return preguntas

    def update(self, pregunta):

        if not self.dao.conectar():
            return False

        sql = """
        UPDATE preguntas
        SET
            id_cuestionario = ?,
            enunciado = ?,
            id_ruta_imagen = ?,
            nombre_imagen = ?
        WHERE id_pregunta = ?;
        """

        id_ruta = None

        if pregunta.get_ruta_imagen() is not None:
            id_ruta = (
                pregunta
                .get_ruta_imagen()
                .get_id_ruta()
            )

        result = self.dao.ejecutar_sql(
            sql,
            (
                pregunta.get_cuestionario()
                .get_id_cuestionario(),

                pregunta.get_enunciado(),

                id_ruta,

                pregunta.get_nombre_imagen(),

                pregunta.get_id_pregunta()
            )
        )

        self.dao.cerrar()

        return result

    def count_by_route(
            self,
            id_ruta,
            exclude_id_pregunta=None
    ):

        if not self.dao.conectar():
            return 0

        sql = """
        SELECT COUNT(*)
        FROM preguntas
        WHERE id_ruta_imagen = ?
        """

        parametros = [
            id_ruta
        ]

        if exclude_id_pregunta is not None:

            sql += """
            AND id_pregunta != ?
            """

            parametros.append(
                exclude_id_pregunta
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
            exclude_id_pregunta
    ):

        if not self.dao.conectar():
            return False

        sql = """
        UPDATE preguntas
        SET id_ruta_imagen = ?
        WHERE id_ruta_imagen = ?
        AND id_pregunta != ?;
        """

        result = self.dao.ejecutar_sql(
            sql,
            (
                new_id_ruta,
                old_id_ruta,
                exclude_id_pregunta
            )
        )

        self.dao.cerrar()

        return result

    def delete(self, id_pregunta):

        if not self.dao.conectar():
            return False

        sql = """
        DELETE FROM preguntas
        WHERE id_pregunta = ?;
        """

        result = self.dao.ejecutar_sql(
            sql,
            (id_pregunta,)
        )

        self.dao.cerrar()

        return result
