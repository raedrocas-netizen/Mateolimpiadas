from flask import session

from dao.dao import Dao


OWNED_TABLES = {
    "materias": "id_materia",
    "cuestionarios": "id_cuestionario",
    "partidas": "id_partida",
    "rutas_imagenes": "id_ruta"
}


def current_owner():
    try:
        return session.get("judge_name") or session.get("judge_username") or "global"
    except RuntimeError:
        return "global"


def assign_owner(table_name, id_column, id_value, owner=None):
    if table_name not in OWNED_TABLES.values() and table_name not in OWNED_TABLES:
        return False

    dao = Dao()

    if not dao.conectar():
        return False

    result = dao.ejecutar_sql(
        f"""
        UPDATE {table_name}
        SET created_by = ?
        WHERE {id_column} = ?;
        """,
        (
            owner or current_owner(),
            id_value
        )
    )
    dao.cerrar()
    return result


def assign_owner_by_value(table_name, lookup_column, lookup_value, owner=None):
    id_column = OWNED_TABLES.get(table_name)

    if id_column is None:
        return False

    dao = Dao()

    if not dao.conectar():
        return False

    row = dao.obtener_uno(
        f"""
        SELECT {id_column}
        FROM {table_name}
        WHERE {lookup_column} = ?
        ORDER BY {id_column} DESC
        LIMIT 1;
        """,
        (lookup_value,)
    )

    success = False

    if row is not None:
        success = dao.ejecutar_sql(
            f"""
            UPDATE {table_name}
            SET created_by = ?
            WHERE {id_column} = ?;
            """,
            (
                owner or current_owner(),
                row[id_column]
            )
        )

    dao.cerrar()
    return success


def is_owned(table_name, id_column, id_value, owner=None):
    dao = Dao()

    if not dao.conectar():
        return False

    row = dao.obtener_uno(
        f"""
        SELECT 1
        FROM {table_name}
        WHERE {id_column} = ?
        AND created_by = ?;
        """,
        (
            id_value,
            owner or current_owner()
        )
    )
    dao.cerrar()
    return row is not None


def filter_owned_entities(entities, table_name, id_column, getter):
    ids = {
        str(item)
        for item in get_owned_ids(table_name, id_column)
    }

    return [
        entity
        for entity in entities
        if str(getter(entity)) in ids
    ]


def get_owned_ids(table_name, id_column, owner=None):
    dao = Dao()

    if not dao.conectar():
        return []

    rows = dao.obtener_todos(
        f"""
        SELECT {id_column}
        FROM {table_name}
        WHERE created_by = ?;
        """,
        (owner or current_owner(),)
    )
    dao.cerrar()
    return [
        row[id_column]
        for row in rows
    ]
