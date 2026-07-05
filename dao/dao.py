import os

import psycopg2
from psycopg2.extras import DictCursor


class CursorAdapter:

    def __init__(self, cursor):
        self._cursor = cursor
        self.lastrowid = None

    def _translate_sql(self, sql):
        return sql.replace("?", "%s")

    def execute(self, sql, parametros=()):
        translated = self._translate_sql(sql)
        self._cursor.execute(translated, parametros)

        if translated.lstrip().upper().startswith("INSERT"):
            try:
                self._cursor.execute("SELECT LASTVAL();")
                row = self._cursor.fetchone()
                self.lastrowid = row[0] if row else None
            except Exception:
                self.lastrowid = None

        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def __getattr__(self, name):
        return getattr(self._cursor, name)

    def close(self):
        self._cursor.close()


class Dao:

    def __init__(self, database_name=None):
        self.database_name = database_name
        self.conexion = None
        self.cursor = None

    def conectar(self):
        database_url = os.getenv("DATABASE_URL")

        if not database_url:
            print("[ERROR] Debe configurar la variable DATABASE_URL.")
            return False

        try:
            self.conexion = psycopg2.connect(
                database_url,
                cursor_factory=DictCursor
            )
            self.cursor = CursorAdapter(
                self.conexion.cursor()
            )
            return True

        except psycopg2.Error as e:
            print(f"Error al conectar a PostgreSQL: {e}")
            return False

    def ejecutar_sql(self, sql, parametros=()):
        if self.conexion is None:
            print("No existe una conexion activa.")
            return False

        try:
            self.cursor.execute(sql, parametros)
            self.conexion.commit()
            return True

        except psycopg2.Error as e:
            self.conexion.rollback()
            print(f"Error al ejecutar SQL: {e}")
            return False

    def ejecutar_sql_query(self, sql, parametros=()):
        if self.conexion is None:
            print("No existe una conexion activa.")
            return None

        try:
            self.cursor.execute(sql, parametros)
            return self.cursor

        except psycopg2.Error as e:
            print(f"Error en consulta SQL: {e}")
            return None

    def obtener_uno(self, sql, parametros=()):
        cursor = self.ejecutar_sql_query(
            sql,
            parametros
        )

        if cursor:
            return cursor.fetchone()

        return None

    def obtener_todos(self, sql, parametros=()):
        cursor = self.ejecutar_sql_query(
            sql,
            parametros
        )

        if cursor:
            return cursor.fetchall()

        return []

    def obtener_ultimo_id(self):
        if self.cursor:
            return self.cursor.lastrowid

        return None

    def cerrar(self):
        try:
            if self.cursor:
                self.cursor.close()

            if self.conexion:
                self.conexion.close()

        except psycopg2.Error as e:
            print(f"Error al cerrar conexion: {e}")
