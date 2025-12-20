import os
import pyperclip
ruta = r"C:\SR.txt"   #-----------------Listado de SRs

try:
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"El archivo no existe en {ruta}")
    with open(ruta, "r", encoding="utf-8") as file:
        lines = file.readlines()
    if not lines:
        raise ValueError("No hay lineas")
    first_line = lines[0].strip()  #---------------------------------------Tomar primer elemento
    pyperclip.copy(first_line)
    print(f"Copiado al portapapeles: '{first_line}'")
    new_lines = lines[1:]          #---------------------------------------Lista primer elemento
    with open(ruta, "w", encoding="utf-8") as file:
        file.writelines(new_lines)
    print("Archivo actualizado: Primer elemento eliminado")
except Exception as e:
    print(f"Error: {str(e)}")
