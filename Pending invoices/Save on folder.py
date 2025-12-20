import os
import shutil

# === RUTAS ===
origen = "C:\Temp"
destino = "100-SEMMails"

# Crear destino si no existe
os.makedirs(destino, exist_ok=True)

# Obtener lista de archivos
archivos = [f for f in os.listdir(origen) if os.path.isfile(os.path.join(origen, f))]

# Si no hay archivos, detener
if not archivos:
    print(" No hay archivos en la carpeta de origen. Proceso detenido.")
else:
    for archivo in archivos:
        ruta_origen = os.path.join(origen, archivo)
        ruta_destino = os.path.join(destino, archivo)
        shutil.move(ruta_origen, ruta_destino)
        print(f"Movido: {archivo}")

    print(" Todos los archivos fueron movidos correctamente.")
