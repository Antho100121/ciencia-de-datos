import os
import sys
import tempfile
from pathlib import Path

import requests
import snowflake.connector


BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"

PERIODS = (
    [f"2025-{month:02d}" for month in range(1, 13)]
    +
    [f"2026-{month:02d}" for month in range(1, 9)]
)


def get_connection():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ["SNOWFLAKE_ROLE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
    )


def already_loaded(cursor, file_name):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM NYC_TAXI_LAB.BRONZE.INGESTION_LOG
        WHERE SOURCE_FILE = %s
        """,
        (file_name,),
    )

    return cursor.fetchone()[0] > 0


def download_file(file_name, destination):
    url = f"{BASE_URL}/{file_name}"

    print(f"Descargando {file_name}...")
    print(url)

    with requests.get(
        url,
        stream=True,
        timeout=(30, 300)
    ) as response:

        response.raise_for_status()

        total_bytes = 0

        with open(destination, "wb") as file:
            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):
                if chunk:
                    file.write(chunk)
                    total_bytes += len(chunk)

    size_mb = total_bytes / (1024 * 1024)

    print(
        f"Descarga completada: {size_mb:.2f} MB"
    )


def upload_to_stage(cursor, local_path):
    file_uri = Path(local_path).resolve().as_uri()

    print("Subiendo archivo al stage...")

    cursor.execute(
        f"""
        PUT '{file_uri}'
        @NYC_TAXI_LAB.BRONZE.NYC_TAXI_STAGE
        AUTO_COMPRESS = FALSE
        OVERWRITE = TRUE
        """
    )

    print("Archivo cargado al stage.")


def copy_to_bronze(cursor, file_name, period):
    print("Cargando registros en Bronze...")

    sql = f"""
        COPY INTO NYC_TAXI_LAB.BRONZE.YELLOW_TAXI_RAW
        (
            RAW_RECORD,
            SOURCE_FILE,
            SOURCE_PERIOD,
            SOURCE_ROW_NUMBER,
            LOADED_AT
        )
        FROM
        (
            SELECT
                t.$1,
                METADATA$FILENAME,
                '{period}',
                METADATA$FILE_ROW_NUMBER,
                CURRENT_TIMESTAMP()
            FROM
                @NYC_TAXI_LAB.BRONZE.NYC_TAXI_STAGE/{file_name}
                (
                    FILE_FORMAT =>
                    NYC_TAXI_LAB.BRONZE.PARQUET_FORMAT
                ) t
        )
        ON_ERROR = ABORT_STATEMENT
    """

    cursor.execute(sql)

    results = cursor.fetchall()

    for result in results:
        print(result)


def count_loaded_rows(cursor, period):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM NYC_TAXI_LAB.BRONZE.YELLOW_TAXI_RAW
        WHERE SOURCE_PERIOD = %s
        """,
        (period,),
    )

    return cursor.fetchone()[0]


def register_ingestion(
    cursor,
    file_name,
    period,
    row_count
):
    cursor.execute(
        """
        INSERT INTO NYC_TAXI_LAB.BRONZE.INGESTION_LOG
        (
            SOURCE_FILE,
            SOURCE_PERIOD,
            ROW_COUNT,
            LOADED_AT
        )
        VALUES (%s, %s, %s, CURRENT_TIMESTAMP())
        """,
        (
            file_name,
            period,
            row_count,
        ),
    )


def remove_from_stage(cursor, file_name):
    cursor.execute(
        f"""
        REMOVE
        @NYC_TAXI_LAB.BRONZE.NYC_TAXI_STAGE/{file_name}
        """
    )


def process_period(connection, cursor, period):

    file_name = f"yellow_tripdata_{period}.parquet"

    print()
    print("=" * 60)
    print(f"PERIODO: {period}")
    print("=" * 60)

    if already_loaded(cursor, file_name):
        print(f"{file_name} ya fue procesado.")
        print("Se omite para evitar duplicados.")
        return

    with tempfile.TemporaryDirectory() as temp_dir:

        local_path = Path(temp_dir) / file_name

        # --------------------------------------------------------
        # DESCARGA
        # --------------------------------------------------------

        try:
            download_file(
                file_name,
                local_path
            )

        except requests.HTTPError as exc:

            status_code = (
                exc.response.status_code
                if exc.response is not None
                else None
            )

            if status_code in (403, 404):
                print()
                print(
                    f"{file_name} todavía no está "
                    "disponible en NYC TLC."
                )
                print(
                    "Se omite temporalmente. "
                    "Al volver a ejecutar el pipeline "
                    "se intentará nuevamente."
                )
                return

            raise

        # --------------------------------------------------------
        # CARGA A SNOWFLAKE
        # --------------------------------------------------------

        try:

            upload_to_stage(
                cursor,
                local_path
            )

            copy_to_bronze(
                cursor,
                file_name,
                period
            )

            row_count = count_loaded_rows(
                cursor,
                period
            )

            if row_count <= 0:
                raise RuntimeError(
                    f"No se cargaron registros para {period}"
                )

            register_ingestion(
                cursor,
                file_name,
                period,
                row_count
            )

            connection.commit()

            print(
                f"Periodo {period} completado: "
                f"{row_count:,} filas."
            )

        except Exception:
            connection.rollback()
            raise

        finally:

            try:
                remove_from_stage(
                    cursor,
                    file_name
                )

            except Exception as cleanup_error:
                print(
                    "Advertencia al limpiar stage:"
                )
                print(cleanup_error)

def main():

    connection = None
    cursor = None

    try:
        print("=" * 60)
        print("NYC YELLOW TAXI")
        print("INGESTA BRONZE 2025-01 A 2026-08")
        print("=" * 60)

        print(
            f"Periodos definidos: {len(PERIODS)}"
        )

        connection = get_connection()
        connection.autocommit(False)

        cursor = connection.cursor()

        for period in PERIODS:
            process_period(
                connection,
                cursor,
                period
            )

        print()
        print("=" * 60)
        print("INGESTA BRONZE FINALIZADA")
        print("=" * 60)

    except Exception as exc:

        if connection is not None:
            connection.rollback()

        print()
        print("ERROR DURANTE LA INGESTA:")
        print(exc)

        sys.exit(1)

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()