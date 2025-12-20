import win32com.client as win32

# Conecta con la instancia actual de Excel
excel = win32.Dispatch("Excel.Application")

# Recorre todos los workbooks abiertos
for wb in excel.Workbooks:
    try:
        # Si el archivo ya tiene ruta → Guardar directamente
        if wb.Path:
            wb.Save()
            print(f"Guardado: {wb.Name}")

        # Si NO tiene ruta (Libro1, Libro2…) → Guardarlo sin preguntar
        else:
            new_path = fr"C:\Temp\{wb.Name}.xlsx"
            wb.SaveAs(new_path)
            print(f"Guardado con SaveAs: {new_path}")

    except Exception as e:
        print(f"Error al guardar {wb.Name}: {e}")

print(" Todos los archivos abiertos fueron guardados.")
