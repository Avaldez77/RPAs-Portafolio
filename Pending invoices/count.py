import os
import pyperclip
pyperclip.copy("")
ruta = r"C:\SR.txt"

try:
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"El archivo no existe en {ruta}")

    with open(ruta, "r", encoding="utf-8") as file:
        lines = file.readlines()
        conteo = len(lines)  # 🔹 cuenta las líneas

    # Copiar el conteo al portapapeles
    pyperclip.copy(str(conteo))
    print(f"Conteo ({conteo}) copiado al portapapeles.")

except Exception as e:
    print(f"Error: {str(e)}")
