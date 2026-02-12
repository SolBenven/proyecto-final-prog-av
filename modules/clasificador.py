"""
Clasificador automático de reclamos usando pickle + ClaimsClassifier.
"""

from __future__ import annotations
import os
import pickle


class Clasificador:
    """Clasificador automático de reclamos a departamentos"""

    RUTA_MODELO = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "claims_clf.pkl")

    def __init__(self):
        self.__clf = None
        if os.path.exists(self.RUTA_MODELO):
            with open(self.RUTA_MODELO, "rb") as archivo:
                self.__clf = pickle.load(archivo)

    def clasificar(self, texto: str) -> str:
        """Clasifica un texto y devuelve el nombre de departamento interno."""
        resultado = self.__clf.classify([texto])[0]
        tabla = {
            "soporte informático": "Secretario Informartico - secretario_informatico",
            "secretaría técnica": "Secretario Técnico - secretario_tecnico",
            "maestranza": "Maestranza - maestranza",
        }
        return tabla[resultado]

    def modelo_disponible(self) -> bool:
        """Retorna True si el modelo fue cargado correctamente."""
        return self.__clf is not None


# Instancia global del clasificador
clasificador = Clasificador()
