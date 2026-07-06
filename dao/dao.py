import os
import threading
import time

import psycopg2
from psycopg2 import pool
from psycopg2.extensions import TRANSACTION_STATUS_IDLE
from psycopg2.extras import DictCursor, execute_values

from helpers.performance import record_metric, record_sql


_pool = None
_pool_lock = threading.Lock()


def _pool_size(name, default):
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _get_pool(database_url):
    global _pool

    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = pool.ThreadedConnectionPool(
                    _pool_size("DB_POOL_MIN", 1),
                    _pool_size("DB_POOL_MAX", 12),
                    database_url,
                    cursor_factory=DictCursor
                )

    return _pool


class CursorAdapter:

    def __init__(self, cursor):
        self._cursor = cursor
        self.lastrowid = None

    def _translate_sql(self, sql):
        return sql.replace("?", "%s")

    def execute(self, sql, parametros=()):
        translated = self._translate_sql(sql)
        started_at = time.perf_counter()
        self._cursor.execute(translated, parametros)
        record_sql(translated, time.perf_counter() - started_at)

        normalized = translated.lstrip().upper()

        if normalized.startswith("INSERT") and " RETURNING " not in normalized:
            try:
                started_at = time.perf_counter()
                self._cursor.execute("SELECT LASTVAL();")
                record_sql("SELECT LASTVAL();", time.perf_counter() - started_at)
                row = self._cursor.fetchone()
                self.lastrowid = row[0] if row else None
            except Exception:
                self.lastrowid = None

        return self

    def executemany(self, sql, parametros):
        translated = self._translate_sql(sql)
        started_at = time.perf_counter()
        self._cursor.executemany(translated, parametros)
        record_sql(translated, time.perf_counter() - started_at)
        return self

    def execute_values(self, sql, parametros):
        started_at = time.perf_counter()
        execute_values(self._cursor, sql, parametros)
        record_sql(sql, time.perf_counter() - started_at)
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
            started_at = time.perf_counter()
            self.conexion = _get_pool(database_url).getconn()
            record_metric("DB connection", time.perf_counter() - started_at)
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
                self.cursor = None

            if self.conexion:
                if not self.conexion.closed:
                    try:
                        if self.conexion.get_transaction_status() != TRANSACTION_STATUS_IDLE:
                            self.conexion.rollback()
                    except psycopg2.Error:
                        pass

                    _get_pool(os.getenv("DATABASE_URL")).putconn(self.conexion)

                self.conexion = None

        except psycopg2.Error as e:
            print(f"Error al cerrar conexion: {e}")
