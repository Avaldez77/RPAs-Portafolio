import pandas as pd
from tableauhyperapi import (
    HyperProcess, Telemetry, Connection, CreateMode,
    TableDefinition, SqlType, TableName, Inserter
)

# --------------------------------------------------------------------------------------------
# CONFIG (SANITIZED)
# --------------------------------------------------------------------------------------------

XLSX_FILE = r"\\FILESERVER\Shared\Operations\Reports\DistyBO.xlsx"
HYPER_FILE = r"\\FILESERVER\Shared\Operations\Reports\Output.hyper"

# 1) Leer el Excel con pandas
df = pd.read_excel(XLSX_FILE)

# 2) Iniciar Hyper Process
with HyperProcess(telemetry=Telemetry.SEND_USAGE_DATA_TO_TABLEAU) as hyper:
    with Connection(
        endpoint=hyper.endpoint,
        database=HYPER_FILE,
        create_mode=CreateMode.CREATE_AND_REPLACE
    ) as connection:

        # 3) Definir esquema y tabla
        schema_name = "Extract"
        table_name = TableName(schema_name, "Extract")

        table = TableDefinition(table_name)

        for column in df.columns:
            table.add_column(str(column), SqlType.text())  # todo como texto (genérico)

        # Crear esquema y tabla
        connection.catalog.create_schema(schema_name)
        connection.catalog.create_table(table)

        # 4) Insertar datos
        with Inserter(connection, table) as inserter:
            inserter.add_rows(rows=df.astype(str).values.tolist())
            inserter.execute()

print(f"Archivo convertido: {HYPER_FILE}")
