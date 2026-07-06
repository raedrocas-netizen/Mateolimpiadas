from dao.dao import Dao

from data_representation.cuestionario import Cuestionario
from data_representation.materia import Materia

import helper.super_global as sg
from helpers.ownership import current_owner


class CuestionarioDao:

    BASE_SELECT = """
    SELECT
        c.id_cuestionario,
        c.nombre AS nombre_cuestionario,
        m.id_materia,
        m.nombre AS nombre_materia,
        c.area,
        c.estado,
        c.fecha_creacion
        FROM cuestionarios c
    INNER JOIN materias m
        ON c.id_materia = m.id_materia
    """

    def __init__(self):
        self.dao = Dao(sg.FULL_PATH)

    def _get_base_select(self):
        return self.BASE_SELECT

    def _row_to_cuestionario(self, row):

        materia = Materia()

        materia.set_id_materia(
            row["id_materia"]
        )

        materia.set_nombre(
            row["nombre_materia"]
        )

        cuestionario = Cuestionario()

        cuestionario.set_id_cuestionario(
            row["id_cuestionario"]
        )

        cuestionario.set_nombre(
            row["nombre_cuestionario"]
        )

        cuestionario.set_materia(
            materia
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

        return cuestionario

    def insert(self, cuestionario):

        if not self.dao.conectar():
            return False

        sql = """
        INSERT INTO cuestionarios(
            nombre,
            id_materia,
            area,
            estado,
            fecha_creacion,
            created_by
        )
        VALUES(
            ?, ?, ?, ?, ?, ?
        )
        RETURNING id_cuestionario;
        """

        try:
            row = self.dao.cursor.execute(
                sql,
                (
                    cuestionario.get_nombre(),
                    cuestionario.get_materia().get_id_materia(),
                    cuestionario.get_area(),
                    cuestionario.get_estado(),
                    cuestionario.get_fecha_creacion(),
                    current_owner()
                )
            ).fetchone()
            self.dao.conexion.commit()
            cuestionario.set_id_cuestionario(
                row["id_cuestionario"]
            )
            result = True
        except Exception as e:
            self.dao.conexion.rollback()
            print(f"Error al insertar cuestionario: {e}")
            result = False

        self.dao.cerrar()

        return result

    def get_by_id(self, id_cuestionario):

        if not self.dao.conectar():
            return None

        sql = f"""
        {self._get_base_select()}
        WHERE c.id_cuestionario = ?;
        """

        row = self.dao.obtener_uno(
            sql,
            (id_cuestionario,)
        )

        self.dao.cerrar()

        if row is None:
            return None

        return self._row_to_cuestionario(row)

    def get_all(self):

        if not self.dao.conectar():
            return []

        sql = f"""
        {self._get_base_select()}
        WHERE c.created_by = ?
        ORDER BY c.id_cuestionario;
        """

        rows = self.dao.obtener_todos(
            sql,
            (current_owner(),)
        )

        self.dao.cerrar()

        cuestionarios = []

        for row in rows:
            cuestionarios.append(
                self._row_to_cuestionario(row)
            )

        return cuestionarios

    def update(self, cuestionario):

        if not self.dao.conectar():
            return False

        sql = """
        UPDATE cuestionarios
        SET
            nombre = ?,
            id_materia = ?,
            area = ?,
            estado = ?,
            fecha_creacion = ?
        WHERE id_cuestionario = ?;
        """

        result = self.dao.ejecutar_sql(
            sql,
            (
                cuestionario.get_nombre(),
                cuestionario.get_materia().get_id_materia(),
                cuestionario.get_area(),
                cuestionario.get_estado(),
                cuestionario.get_fecha_creacion(),
                cuestionario.get_id_cuestionario()
            )
        )

        self.dao.cerrar()

        return result

    def delete(self, id_cuestionario):

        if not self.dao.conectar():
            return False

        sql = """
        DELETE FROM cuestionarios
        WHERE id_cuestionario = ?;
        """

        result = self.dao.ejecutar_sql(
            sql,
            (id_cuestionario,)
        )

        self.dao.cerrar()

        return result

    def get_by_name(self, nombre):

        if not self.dao.conectar():
            return None

        sql = f"""
        {self._get_base_select()}
        WHERE c.nombre = ?
        AND c.created_by = ?;
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

        return self._row_to_cuestionario(row)

    def exists(self, nombre):

        return self.get_by_name(
            nombre
        ) is not None

    def get_by_estado(self, estado):

        if not self.dao.conectar():
            return []

        sql = f"""
        {self._get_base_select()}
        WHERE c.estado = ?
        ORDER BY c.nombre;
        """

        rows = self.dao.obtener_todos(
            sql,
            (estado,)
        )

        self.dao.cerrar()

        cuestionarios = []

        for row in rows:
            cuestionarios.append(
                self._row_to_cuestionario(row)
            )

        return cuestionarios

    def get_by_area(self, area):

        if not self.dao.conectar():
            return []

        sql = f"""
        {self._get_base_select()}
        WHERE c.area = ?
        ORDER BY c.nombre;
        """

        rows = self.dao.obtener_todos(
            sql,
            (area,)
        )

        self.dao.cerrar()

        cuestionarios = []

        for row in rows:
            cuestionarios.append(
                self._row_to_cuestionario(row)
            )

        return cuestionarios

    def get_by_materia(self, id_materia):

        if not self.dao.conectar():
            return []

        sql = f"""
        {self._get_base_select()}
        WHERE c.id_materia = ?
        ORDER BY c.nombre;
        """

        rows = self.dao.obtener_todos(
            sql,
            (id_materia,)
        )

        self.dao.cerrar()

        cuestionarios = []

        for row in rows:
            cuestionarios.append(
                self._row_to_cuestionario(row)
            )

        return cuestionarios

    def count_questions_with_answer_by_questionnaire(
            self,
            id_cuestionario
    ):

        if not self.dao.conectar():
            return 0

        sql = """
        SELECT COUNT(DISTINCT p.id_pregunta)
        FROM preguntas p
        INNER JOIN respuestas r
            ON r.id_pregunta = p.id_pregunta
        WHERE p.id_cuestionario = ?
        AND TRIM(COALESCE(r.descripcion, '')) <> '';
        """

        row = self.dao.obtener_uno(
            sql,
            (id_cuestionario,)
        )

        self.dao.cerrar()

        if row is None:
            return 0

        return row[0]
