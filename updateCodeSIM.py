import os
from time import time
from datetime import datetime

def update_codes_text(new_data:list,path_file:str) -> None:
    """Actual.izacion del conternido del archivo local de codigos alarmas"""
    local_path = os.path.join(os.path.dirname(__file__), path_file)
    try:
        with open(local_path, "w", encoding="utf-8") as f:
                f.write("\n".join(new_data))
                f.write(f"\n{time.strftime('%Y-%m-%d %H:%M:%S')}")  # Agrega una nueva línea al final del archivo
    except IOError as exc:
        raise RuntimeError(f"Error al escribir en el archivo {local_path}") from exc

def read_last_update_time(path_file:str) -> str:
    """Lee la última fecha de actualización del archivo de códigos."""
    local_path = os.path.join(os.path.dirname(__file__), path_file)
    try:
        with open(local_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                return lines[-1].strip()  # Devuelve la última línea como fecha de actualización
            else:
                return "Archivo vacío"
    except IOError as exc:
        raise RuntimeError(f"Error al leer el archivo {local_path}") from exc

def do_update(last_local_update:str, last_drive_update:str) -> bool:
    """Determina si se debe actualizar el archivo local basado en las fechas de actualización."""
    if last_local_update == "Archivo vacío":
        return True  # Si el archivo local está vacío, se debe actualizar
    try:
        local_time = datetime.strptime(last_local_update, "%Y-%m-%d %H:%M:%S")
        drive_time = datetime.strptime(last_drive_update, "%Y-%m-%d %H:%M:%S")
        return drive_time > local_time  # Actualiza si la fecha de Drive es más reciente
    except ValueError as exc:
        raise RuntimeError("Formato de fecha no válido en las actualizaciones") from exc

if __name__ == "__main__":
    print(read_last_update_time("utils/codigosSIM.txt"))
    print(do_update(read_last_update_time("utils/codigosSIM.txt"), "2026-06-12 19:50:53"))