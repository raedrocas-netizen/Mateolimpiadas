from dao.dao import Dao

from data_representation.materia import Materia

import helper.super_global as sg
from helpers.ownership import current_owner


class MateriaDao:

    def __init__(self):
        self.dao = Dao(sg.FULL_PATH)

    def _row_to_materia(self, row):

        materia = Materia()

        materia.set_id_materia(
            row["id_materia"]
        )

        materia.set_nombre(
            row["nombre"]
        )

        return materia

    def insert(self, materia):

        if not self.dao.conectar():
            return False

        sql = """
        INSERT INTO materias(
            nombre,
            created_by
        )
        VALUES(
            ?, ?
        )
        RETURNING id_materia;
        """

        try:
            row = self.dao.cursor.execute(
                sql,
                (
                    materia.get_nombre(),
                    current_owner()
                )
            ).fetchone()
            self.dao.conexion.commit()
            materia.set_id_materia(
                row["id_materia"]
            )
            result = True
        except Exception as e:
            self.dao.conexion.rollback()
            print(f"Error al insertar materia: {e}")
            result = False

        self.dao.cerrar()

        return result

    def get_by_id(self, id_materia):

        if not self.dao.conectar():
            return None

        sql = """
        SELECT *
        FROM materias
        WHERE id_materia = ?;
        """

        row = self.dao.obtener_uno(
            sql,
            (id_materia,)
        )

        self.dao.cerrar()

        if row is None:
            return None

        return self._row_to_materia(row)

    def get_all(self):

        if not self.dao.conectar():
            return []

        sql = """
        SELECT *
        FROM materias
        WHERE created_by = ?
        ORDER BY id_materia;
        """

        rows = self.dao.obtener_todos(
            sql,
            (current_owner(),)
        )

        self.dao.cerrar()

        materias = []

        for row in rows:
            materias.append(
                self._row_to_materia(row)
            )

        return materias

    def update(self, materia):

        if not self.dao.conectar():
            return False

        sql = """
        UPDATE materias
        SET nombre = ?
        WHERE id_materia = ?;
        """

        result = self.dao.ejecutar_sql(
            sql,
            (
                materia.get_nombre(),
                materia.get_id_materia()
            )
        )

        self.dao.cerrar()

        return result

    def delete(self, id_materia):

        if not self.dao.conectar():
            return False

        sql = """
        DELETE FROM materias
        WHERE id_materia = ?;
        """

        result = self.dao.ejecutar_sql(
            sql,
            (id_materia,)
        )

        self.dao.cerrar()

        return result

    def count_questionnaires(self, id_materia):

        if not self.dao.conectar():
            return 0

        row = self.dao.obtener_uno(
            """
            SELECT COUNT(*)
            FROM cuestionarios
            WHERE id_materia = ?;
            """,
            (id_materia,)
        )

        self.dao.cerrar()

        if row is None:
            return 0

        return row[0]

    def get_by_name(self, nombre):

        if not self.dao.conectar():
            return None

        sql = """
        SELECT *
        FROM materias
        WHERE nombre = ?
        AND created_by = ?;
        """

        row = self.dao.obtener_uno(
            sql,
            (
                nombre,
                current_owner()
            )
        )

        self.dao.cerrar()

        if row is None:
            return None

        return self._row_to_materia(row)

    def get_id_by_name(self, nombre):

        materia = self.get_by_name(
            nombre
        )

        if materia is None:
            return None

        return materia.get_id_materia()

    def exists(self, nombre):

        return self.get_by_name(
            nombre
        ) is not None

    def get_all_names(self):

        materias = self.get_all()

        return [
            materia.get_nombre()
            for materia in materias
        ]
