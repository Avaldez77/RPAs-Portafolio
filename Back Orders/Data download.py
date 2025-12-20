import os
import sys
from datetime import datetime, timedelta

import pandas as pd
import xlwings as xw

# Configurar el entorno para evitar problemas con matplotlib (si aplica en tu runtime)
os.environ["MPLBACKEND"] = "Agg"

# --------------------------------------------------------------------------------------------
# CONFIG (SANITIZED)
# --------------------------------------------------------------------------------------------

# Ruta genérica a un Excel compartido (reemplaza por tu path real en tu ambiente)
EXCEL_PATH = r"\\FILESERVER\Shared\Operations\Reports\DistyBO.xlsx"

SHEET_NAME = "Sheet1"
SOURCE_DATE_COLUMN = "ERDAT"     # columna original con fecha
TARGET_HEADER_CELL = "T1"
TARGET_COLUMN_RANGE_START = "T2" # desde T2 hasta la última fila

def main():
    app = None
    wb = None

    try:
        # Iniciar Excel en background
        app = xw.App(visible=False)
        app.display_alerts = False
        app.screen_updating = False

        # Abrir archivo
        wb = app.books.open(EXCEL_PATH)
        print(f"Archivo abierto en segundo plano: {EXCEL_PATH}")

        # Leer datos
        sheet = wb.sheets[SHEET_NAME]
        df = sheet.used_range.options(pd.DataFrame, header=1, index=False).value

        # Validaciones básicas
        if df is None or df.empty:
            raise ValueError("La hoja no tiene datos (DataFrame vacío).")

        if SOURCE_DATE_COLUMN not in df.columns:
            raise KeyError(f"No existe la columna requerida: '{SOURCE_DATE_COLUMN}'")

        # Convertir columna a datetime (tolerante a errores)
        df[SOURCE_DATE_COLUMN] = pd.to_datetime(df[SOURCE_DATE_COLUMN], errors="coerce")

        # Encontrar fecha máxima válida
        last_date = df[SOURCE_DATE_COLUMN].max()
        if pd.isna(last_date):
            raise ValueError(f"No se encontraron fechas válidas en '{SOURCE_DATE_COLUMN}'")

        print(f"La última fecha en '{SOURCE_DATE_COLUMN}' es: {last_date}")

        # Escribir encabezado en T1
        sheet.range(TARGET_HEADER_CELL).value = "BO Data Date"

        # Insertar la fecha máxima en columna T para todas las filas con datos
        last_row = len(df) + 1  # +1 por header en Excel
        sheet.range(f"{TARGET_COLUMN_RANGE_START}:T{last_row}").value = [[last_date]] * len(df)

        # Guardar cambios en el mismo archivo
        wb.save(EXCEL_PATH)
        print("Cambios guardados en el archivo.")

    except Exception as e:
        print(f"Se produjo un error: {e}")

    finally:
        # Cerrar recursos
        if wb is not None:
            wb.close()
        if app is not None:
            app.quit()
        print("Libro cerrado y Excel terminado.")

if __name__ == "__main__":
    main()
