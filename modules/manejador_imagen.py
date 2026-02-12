"""Gestión de imágenes de reclamos"""

import os
import uuid
from pathlib import Path
from typing import Tuple
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

# Configuración
CARPETA_SUBIDA = "static/uploads/claims"
EXTENSIONES_PERMITIDAS = {"png", "jpg", "jpeg", "gif"}
TAMANO_MAXIMO_ARCHIVO = 5 * 1024 * 1024  # 5MB


class ManejadorImagen:
    """Gestión de imágenes para reclamos"""

    @staticmethod
    def archivo_permitido(nombre_archivo: str) -> bool:
        return (
            "." in nombre_archivo and nombre_archivo.rsplit(".", 1)[1].lower() in EXTENSIONES_PERMITIDAS
        )

    @staticmethod
    def validar_imagen(archivo: FileStorage) -> Tuple[bool, str | None]:
        if not archivo or not archivo.filename:
            return False, "No se proporcionó ningún archivo"
        if archivo.filename == "":
            return False, "El archivo no tiene nombre"
        if not ManejadorImagen.archivo_permitido(archivo.filename):
            return (
                False,
                f"Tipo de archivo no permitido. Use: {', '.join(EXTENSIONES_PERMITIDAS)}",
            )

        archivo.seek(0, os.SEEK_END)
        tamano_archivo = archivo.tell()
        archivo.seek(0)

        if tamano_archivo > TAMANO_MAXIMO_ARCHIVO:
            return False, f"El archivo excede el tamaño máximo de 5MB"

        return True, None

    @staticmethod
    def guardar_imagen_reclamo(archivo: FileStorage) -> Tuple[str | None, str | None]:
        es_valido, error = ManejadorImagen.validar_imagen(archivo)
        if not es_valido:
            return None, error

        directorio_subida = Path(CARPETA_SUBIDA)
        directorio_subida.mkdir(parents=True, exist_ok=True)

        nombre_original = secure_filename(archivo.filename or "")
        extension = nombre_original.rsplit(".", 1)[1].lower()
        nombre_unico = f"{uuid.uuid4()}.{extension}"

        ruta_archivo = directorio_subida.joinpath(nombre_unico)
        try:
            archivo.save(str(ruta_archivo))
        except Exception as e:
            return None, f"Error al guardar el archivo: {str(e)}"

        ruta_relativa = f"{CARPETA_SUBIDA}/{nombre_unico}"
        return ruta_relativa, None

    @staticmethod
    def eliminar_imagen_reclamo(ruta_imagen: str) -> bool:
        if not ruta_imagen:
            return False
        try:
            ruta_archivo = Path(ruta_imagen)
            if ruta_archivo.exists():
                ruta_archivo.unlink()
                return True
            return False
        except Exception:
            return False
