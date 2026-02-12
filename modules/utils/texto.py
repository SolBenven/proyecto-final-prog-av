"""Utilidades para procesamiento de texto."""

from __future__ import annotations

import unicodedata


def normalizar_texto(texto: str) -> str:
    """
    Normaliza el texto removiendo acentos y caracteres especiales.
    """
    texto = texto.lower()
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )
    return texto
