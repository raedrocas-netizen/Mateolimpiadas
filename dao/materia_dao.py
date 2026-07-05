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
        );
        """

        result = self.dao.ejecutar_sql(
            sql,
            (
                materia.get_nombre(),
                current_owner()
            )
        )

        if result:
            materia.set_id_materia(
                self.dao.obtener_ultimo_id()
            )

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
        ORDER BY id_materia;
        """

        rows = self.dao.obtener_todos(sql)

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
