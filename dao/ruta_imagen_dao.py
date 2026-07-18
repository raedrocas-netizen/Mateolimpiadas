from dao.dao import Dao

from data_representation.ruta_imagen import RutaImagen

import helper.super_global as sg
from helpers.ownership import current_owner


class RutaImagenDao:

    def __init__(self):
        self.dao = Dao(sg.FULL_PATH)

    def _row_to_ruta_imagen(self, row):

        ruta_imagen = RutaImagen()

        ruta_imagen.set_id_ruta(
            row["id_ruta"]
        )

        ruta_imagen.set_descripcion(
            row["descripcion"]
        )

        ruta_imagen.set_ruta(
            row["ruta"]
        )

        return ruta_imagen

    def insert(self, ruta_imagen):

        if not self.dao.conectar():
            return False

        sql = """
        INSERT INTO rutas_imagenes(
            descripcion,
            ruta,
            created_by
        )
        VALUES(
            ?, ?, ?
        )
        RETURNING id_ruta;
        """

        try:
            row = self.dao.cursor.execute(
                sql,
                (
                    ruta_imagen.get_descripcion(),
                    ruta_imagen.get_ruta(),
                    current_owner()
                )
            ).fetchone()
            self.dao.conexion.commit()
            ruta_imagen.set_id_ruta(
                row["id_ruta"]
            )
            result = True
        except Exception as e:
            self.dao.conexion.rollback()
            print(f"Error al insertar ruta de imagen: {e}")
            result = False

        self.dao.cerrar()

        return result

    def get_by_id(self, id_ruta):

        if not self.dao.conectar():
            return None

        sql = """
        SELECT *
        FROM rutas_imagenes
        WHERE id_ruta = ?;
        """

        row = self.dao.obtener_uno(
            sql,
            (id_ruta,)
        )

        self.dao.cerrar()

        if row is None:
            return None

        return self._row_to_ruta_imagen(row)

    def get_by_description(self, descripcion):

        if not self.dao.conectar():
            return None

        sql = """
        SELECT *
        FROM rutas_imagenes
        WHERE descripcion = ?;
        """

        row = self.dao.obtener_uno(
            sql,
            (descripcion,)
        )

        self.dao.cerrar()

        if row is None:
            return None

        return self._row_to_ruta_imagen(row)

    def get_all(self):

        if not self.dao.conectar():
            return []

        sql = """
        SELECT *
        FROM rutas_imagenes
        WHERE created_by = ?
        ORDER BY descripcion;
        """

        rows = self.dao.obtener_todos(
            sql,
            (current_owner(),)
        )

        self.dao.cerrar()

        rutas = []

        for row in rows:
            rutas.append(
                self._row_to_ruta_imagen(row)
            )

        return rutas

    def update(self, ruta_imagen):

        if not self.dao.conectar():
            return False

        sql = """
        UPDATE rutas_imagenes
        SET
            descripcion = ?,
            ruta = ?
        WHERE id_ruta = ?;
        """

        result = self.dao.ejecutar_sql(
            sql,
            (
                ruta_imagen.get_descripcion(),
                ruta_imagen.get_ruta(),
                ruta_imagen.get_id_ruta()
            )
        )

        self.dao.cerrar()

        return result

    def delete(self, id_ruta):

        if not self.dao.conectar():
            return False

        sql = """
        DELETE FROM rutas_imagenes
        WHERE id_ruta = ?;
        """

        result = self.dao.ejecutar_sql(
            sql,
            (id_ruta,)
        )

        self.dao.cerrar()

        return result

    def exists(self, descripcion):

        return (
            self.get_by_description(
                descripcion
            )
            is not None
        )

    def get_by_path(
            self,
            ruta
    ):

        if not self.dao.conectar():
            return None

        sql = """
        SELECT *
        FROM rutas_imagenes
        WHERE ruta = ?;
        """

        row = self.dao.obtener_uno(
            sql,
            (ruta,)
        )

        self.dao.cerrar()

        if row is None:
            return None

        return self._row_to_ruta_imagen(
            row
        )

    def exists_path(
            self,
            ruta
    ):

        return (
                self.get_by_path(
                    ruta
                )
                is not None
        )

    def count_question_uses(
            self,
            id_ruta
    ):

        if not self.dao.conectar():
            return 0

        sql = """
        SELECT COUNT(*)
        FROM preguntas
        WHERE id_ruta_imagen = ?;
        """

        row = self.dao.obtener_uno(
            sql,
            (id_ruta,)
        )

        self.dao.cerrar()

        if row is None:
            return 0

        return row[0]

    def count_answer_uses(
            self,
            id_ruta
    ):

        if not self.dao.conectar():
            return 0

        sql = """
        SELECT COUNT(*)
        FROM respuestas
        WHERE id_ruta_imagen = ?;
        """

        row = self.dao.obtener_uno(
            sql,
            (id_ruta,)
        )

        self.dao.cerrar()

        if row is None:
            return 0

        return row[0]

    def count_question_attachment_uses(
            self,
            id_ruta,
            image_name
    ):

        if not self.dao.conectar():
            return None

        sql = """
        SELECT COUNT(*)
        FROM preguntas
        WHERE id_ruta_imagen = ?
        AND nombre_imagen = ?;
        """

        row = self.dao.obtener_uno(
            sql,
            (id_ruta, image_name)
        )

        self.dao.cerrar()

        if row is None:
            return None

        return row[0]

    def count_answer_attachment_uses(
            self,
            id_ruta,
            image_name
    ):

        if not self.dao.conectar():
            return None

        sql = """
        SELECT COUNT(*)
        FROM respuestas
        WHERE id_ruta_imagen = ?
        AND nombre_imagen = ?;
        """

        row = self.dao.obtener_uno(
            sql,
            (id_ruta, image_name)
        )

        self.dao.cerrar()

        if row is None:
            return None

        return row[0]

