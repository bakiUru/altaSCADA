"""Helpers para leer y actualizar un archivo de texto en Google Drive.

Flujo:
- carga `credentials.json` como cuenta de servicio;
- abre el archivo remoto con `DRIVE_FILE_ID`;
- si no hay credenciales o acceso, usa el archivo local.
"""

from __future__ import annotations

import io
import os
from pathlib import Path



LOCAL_CODES_PATH = Path("utils/codigosSIM.txt")
DRIVE_FILE_ID = os.getenv("GOOGLE_DRIVE_TEXT_FILE_ID","14WQ9VevN2S-kTwLfkW3WRpoC_JaocDC8")
GOOGLE_CREDENTIALS_PATH = Path(os.getenv("GOOGLE_DRIVE_CREDENTIALS_JSON", "credentials.json"))
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/drive"]


def _drive_enabled() -> bool:
    print(f"DRIVE_FILE_ID: {DRIVE_FILE_ID}")
    return bool(DRIVE_FILE_ID)


def _read_local_codes_text() -> str:
    return LOCAL_CODES_PATH.read_text(encoding="utf-8")


def _write_local_codes_text(content: str) -> None:
    LOCAL_CODES_PATH.write_text(content, encoding="utf-8")


def _build_drive_service():
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Faltan dependencias de Google Drive. Instala: google-api-python-client y google-auth"
        ) from exc

    if not GOOGLE_CREDENTIALS_PATH.exists():
        raise FileNotFoundError(f"No existe el archivo de credenciales: {GOOGLE_CREDENTIALS_PATH}")

    try:
        credentials = service_account.Credentials.from_service_account_file(
            str(GOOGLE_CREDENTIALS_PATH),
            scopes=GOOGLE_SCOPES,
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError(
            f"El archivo {GOOGLE_CREDENTIALS_PATH} no parece ser un JSON de service account valido"
        ) from exc

    return build("drive", "v3", credentials=credentials)


def read_codes_text() -> dict | str:
    """Lee el contenido del archivo de codigos desde Drive o desde disco local."""
    if _drive_enabled():
        try:
            service = _build_drive_service()
            request = service.files().get_media(fileId=DRIVE_FILE_ID, supportsAllDrives=True)
        except (FileNotFoundError, RuntimeError):
            return {"payload":_read_local_codes_text(), "mode": "Error con Drive", "status": "Error con Drive, usando local"}

        try:
            from googleapiclient.http import MediaIoBaseDownload
        except ImportError as exc:
            raise RuntimeError("Falta google-api-python-client para descargar desde Drive") from exc

        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        return {"payload": buffer.getvalue().decode("utf-8"), "mode": "drive", "status": "Success"}
    
    # Si no se usa Drive, siempre cae al archivo local.
    
    return {"payload": _read_local_codes_text(), "mode": "local", "status": "Usando Archivo Local"}


def write_codes_text(content: str) -> None:
    """Escribe el contenido del archivo de codigos en Drive o en disco local."""
    if _drive_enabled():
        try:
            service = _build_drive_service()
        except (FileNotFoundError, RuntimeError):
            _write_local_codes_text(content)
            return

        try:
            from googleapiclient.http import MediaIoBaseUpload
        except ImportError as exc:
            raise RuntimeError("Falta google-api-python-client para subir a Drive") from exc

        media_body = MediaIoBaseUpload(
            io.BytesIO(content.encode("utf-8")),
            mimetype="text/plain",
            resumable=False,
        )
        service.files().update(
            fileId=DRIVE_FILE_ID,
            media_body=media_body,
            supportsAllDrives=True,
        ).execute()
        return

    # Fallback local cuando no hay Drive o credenciales validas.
    _write_local_codes_text(content)


def get_data_from_api(url=None):
    """Compatibilidad con el nombre anterior; devuelve el texto del archivo."""
    return read_codes_text()


if __name__ == "__main__":
    print(read_codes_text())
