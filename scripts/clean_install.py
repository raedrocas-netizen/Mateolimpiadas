import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2.extensions import adapt
from psycopg2.extensions import quote_ident
from psycopg2.extras import DictCursor


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKUP_DIR = ROOT_DIR / "outputs" / "backups"
UPLOADS_DIR = ROOT_DIR / "static" / "uploads"

APP_TABLES = (
    "respuestas_partida",
    "solicitudes_palabra",
    "participantes",
    "partida_preguntas",
    "partida_cuestionarios",
    "partidas",
    "respuestas",
    "preguntas",
    "cuestionarios",
    "materias",
    "rutas_imagenes",
)


def timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def database_url():
    value = os.getenv("DATABASE_URL")

    if not value:
        raise RuntimeError("Debe configurar DATABASE_URL antes de limpiar la base de datos.")

    return value


def connect():
    return psycopg2.connect(database_url(), cursor_factory=DictCursor)


def ensure_backup_dir():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def backup_uploads(label):
    ensure_backup_dir()
    backup_path = BACKUP_DIR / f"uploads_backup_{label}.zip"

    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as archive:
        if UPLOADS_DIR.exists():
            for file_path in UPLOADS_DIR.rglob("*"):
                if file_path.is_file():
                    archive.write(file_path, file_path.relative_to(ROOT_DIR))

    return backup_path


def app_tables_present(cursor):
    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE';
        """
    )
    existing = {row["table_name"] for row in cursor.fetchall()}
    return [table for table in APP_TABLES if table in existing]


def table_columns(cursor, table):
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = %s
        ORDER BY ordinal_position;
        """,
        (table,)
    )
    return [row["column_name"] for row in cursor.fetchall()]


def sql_literal(value):
    if value is None:
        return "NULL"

    return adapt(value).getquoted().decode("utf-8")


def sql_identifier(connection, value):
    return quote_ident(value, connection)


def fallback_sql_backup(connection, label):
    backup_path = BACKUP_DIR / f"database_backup_{label}.sql"

    with connection.cursor() as cursor:
        tables = app_tables_present(cursor)

        with backup_path.open("w", encoding="utf-8") as backup:
            backup.write("-- Respaldo de datos de Olimpiadas del Conocimiento\n")
            backup.write(f"-- Generado: {datetime.now().isoformat(timespec='seconds')}\n")
            backup.write("-- Este respaldo contiene datos, no recrea la estructura.\n\n")
            backup.write("BEGIN;\n")
            backup.write(
                "TRUNCATE TABLE "
                + ", ".join(sql_identifier(connection, table) for table in tables)
                + " RESTART IDENTITY CASCADE;\n\n"
            )

            for table in reversed(tables):
                columns = table_columns(cursor, table)

                if not columns:
                    continue

                cursor.execute(f"SELECT * FROM {sql_identifier(connection, table)};")
                rows = cursor.fetchall()

                if not rows:
                    continue

                column_sql = ", ".join(
                    sql_identifier(connection, column)
                    for column in columns
                )
                table_sql = sql_identifier(connection, table)

                for row in rows:
                    values = ", ".join(sql_literal(row[column]) for column in columns)
                    backup.write(f"INSERT INTO {table_sql} ({column_sql}) VALUES ({values});\n")

                backup.write("\n")

            backup.write("COMMIT;\n")

    return backup_path


def pg_dump_backup(label):
    pg_dump = shutil.which("pg_dump")

    if pg_dump is None:
        return None

    backup_path = BACKUP_DIR / f"database_backup_{label}.dump"
    result = subprocess.run(
        [
            pg_dump,
            "--format=custom",
            "--file",
            str(backup_path),
            database_url(),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "pg_dump no pudo generar el respaldo.")

    return backup_path


def backup_database(connection, label):
    ensure_backup_dir()
    pg_dump_path = pg_dump_backup(label)

    if pg_dump_path is not None:
        return pg_dump_path

    return fallback_sql_backup(connection, label)


def clean_database(connection):
    with connection.cursor() as cursor:
        tables = app_tables_present(cursor)

        if not tables:
            return []

        cursor.execute(
            "TRUNCATE TABLE "
            + ", ".join(sql_identifier(connection, table) for table in tables)
            + " RESTART IDENTITY CASCADE;"
        )
        connection.commit()
        return tables


def clean_uploads():
    if not UPLOADS_DIR.exists():
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        return 0

    deleted = 0

    for file_path in UPLOADS_DIR.rglob("*"):
        if file_path.is_file():
            file_path.unlink()
            deleted += 1

    for directory in sorted(
        [path for path in UPLOADS_DIR.rglob("*") if path.is_dir()],
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        if directory != UPLOADS_DIR and not any(directory.iterdir()):
            directory.rmdir()

    return deleted


def count_rows(connection):
    with connection.cursor() as cursor:
        rows = {}

        for table in app_tables_present(cursor):
            cursor.execute(f"SELECT COUNT(*) AS total FROM {sql_identifier(connection, table)};")
            rows[table] = cursor.fetchone()["total"]

        return rows


def main():
    parser = argparse.ArgumentParser(
        description="Respalda y limpia los datos de prueba sin modificar la estructura."
    )
    parser.add_argument(
        "--confirm",
        choices=("LIMPIAR",),
        help="Confirma la limpieza destructiva de datos de prueba."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo muestra conteos y verifica la conexion."
    )
    args = parser.parse_args()

    try:
        label = timestamp()

        with connect() as connection:
            before_counts = count_rows(connection)

            if args.dry_run:
                print("Conexion correcta. Conteos actuales:")
                for table, total in before_counts.items():
                    print(f"- {table}: {total}")
                return 0

            if args.confirm != "LIMPIAR":
                print("No se ejecuto limpieza. Use: --confirm LIMPIAR")
                return 2

            database_backup = backup_database(connection, label)
            uploads_backup = backup_uploads(label)
            cleaned_tables = clean_database(connection)
            deleted_uploads = clean_uploads()
            after_counts = count_rows(connection)

        print("Limpieza completada correctamente.")
        print(f"Respaldo de base de datos: {database_backup}")
        print(f"Respaldo de imagenes: {uploads_backup}")
        print(f"Tablas limpiadas: {', '.join(cleaned_tables) if cleaned_tables else 'ninguna'}")
        print(f"Imagenes eliminadas de static/uploads: {deleted_uploads}")
        print("Conteos finales:")

        for table, total in after_counts.items():
            print(f"- {table}: {total}")

        return 0

    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
