import os
import sys
import xlwings as xw
import pandas as pd
import pyperclip

def main():
    rutaSRtxt = r"C:\SR.txt"
    rutaxlsx = r"C:\SR.xlsx"  # Usar barras normales

    # Eliminar archivos existentes si existen
    try:
        os.remove(rutaSRtxt)
    except OSError:
        pass  # Si el archivo no existe, no hay problema

    try:
        os.remove(rutaxlsx)
    except OSError:
        pass

    rutaexcel = r"C:\InfoList.XLSX"  # Corregido: barras normales
    try:
        app = xw.App(visible=False)
        wb = app.books.open(rutaexcel)
        hoja = wb.sheets["Sheet1"]
        df = hoja.used_range.options(pd.DataFrame, header=1, index=False).value
        df.columns = [col.replace("\n", "").lower().strip() for col in df.columns]

        # Verificar columnas
        required_columns = ["sr no.", "sold to desc.", "shipping type", "created date"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Error: Las siguientes columnas requeridas no se encontraron: {missing_columns}")
            raise ValueError("Columnas requeridas faltantes")

        # Filtrar datos
        df_filtrado = df[
            (df["sold to desc."].str.strip().str.lower() == "samsung electronics mexico".lower()) &
            (df["shipping type"].str.strip().str.lower() == "s1".lower())
        ]
        df_limpios = df_filtrado[["sr no."]].drop_duplicates()
        df_limpio2 = df_filtrado[["sr no.", "created date"]].drop_duplicates(keep=False)

        # Guardar TXT
        with open(rutaSRtxt, "w", encoding="utf-8") as f:
            f.write("\n".join(df_limpios["sr no."].astype(str)))

        # Guardar XLSX (corregido)
        df_limpio2.to_excel(rutaxlsx, index=False)

        print("Proceso completado: TXT y XLSX generados correctamente.")

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'wb' in locals():
            wb.close()
        if 'app' in locals():
            app.quit()

if __name__ == "__main__":
    main()
