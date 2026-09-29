import os
import sys

import snowflake.connector


def main():
    required_variables = [
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_USER",
        "SNOWFLAKE_PASSWORD",
        "SNOWFLAKE_ROLE",
        "SNOWFLAKE_WAREHOUSE",
        "SNOWFLAKE_DATABASE",
    ]

    missing_variables = [
        variable
        for variable in required_variables
        if not os.getenv(variable)
    ]

    if missing_variables:
        print("ERROR: faltan variables de entorno:")
        for variable in missing_variables:
            print(f" - {variable}")
        sys.exit(1)

    print("Conectando a Snowflake...")

    connection = None

    try:
        connection = snowflake.connector.connect(
            account=os.environ["SNOWFLAKE_ACCOUNT"],
            user=os.environ["SNOWFLAKE_USER"],
            password=os.environ["SNOWFLAKE_PASSWORD"],
            role=os.environ["SNOWFLAKE_ROLE"],
            warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
            database=os.environ["SNOWFLAKE_DATABASE"],
        )

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                CURRENT_USER(),
                CURRENT_ROLE(),
                CURRENT_WAREHOUSE(),
                CURRENT_DATABASE()
            """
        )

        user, role, warehouse, database = cursor.fetchone()

        print("Conexion exitosa.")
        print(f"Usuario:    {user}")
        print(f"Rol:        {role}")
        print(f"Warehouse:  {warehouse}")
        print(f"Database:   {database}")

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.SCHEMATA
            WHERE SCHEMA_NAME IN ('BRONZE', 'SILVER', 'GOLD')
            """
        )

        schema_count = cursor.fetchone()[0]

        print(f"Capas encontradas: {schema_count}/3")

        if schema_count == 3:
            print("Snowflake esta listo para continuar.")
        else:
            print("ADVERTENCIA: no se encontraron las tres capas.")

        cursor.close()

    except Exception as exc:
        print("ERROR al conectar con Snowflake:")
        print(exc)
        sys.exit(1)

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()