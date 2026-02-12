"""Tests para Clasificador."""

import unittest
from modules.clasificador import Clasificador


class _DummyClassifier:
    def __init__(self, etiqueta: str):
        self._etiqueta = etiqueta

    def classify(self, X):
        return [self._etiqueta]


class TestClasificador(unittest.TestCase):
    """Tests para el clasificador automático."""

    def setUp(self):
        """Crea clasificador real (carga pickle)."""
        self.clasificador = Clasificador()

    def test_carga_modelo_pickle(self):
        """Verifica que se cargue el modelo desde pickle."""
        self.assertIsNotNone(self.clasificador._Clasificador__clf)

    def test_mapea_soporte_informatico(self):
        """Mapea etiqueta 'soporte informático' a departamento interno."""
        self.clasificador._Clasificador__clf = _DummyClassifier("soporte informático")
        resultado = self.clasificador.clasificar("Texto de prueba")
        self.assertEqual(resultado, "Secretario Informartico - secretario_informatico")

    def test_mapea_secretaria_tecnica(self):
        """Mapea etiqueta 'secretaría técnica' a departamento interno."""
        self.clasificador._Clasificador__clf = _DummyClassifier("secretaría técnica")
        resultado = self.clasificador.clasificar("Texto de prueba")
        self.assertEqual(resultado, "Secretario Técnico - secretario_tecnico")

    def test_mapea_maestranza(self):
        """Mapea etiqueta 'maestranza' a departamento interno."""
        self.clasificador._Clasificador__clf = _DummyClassifier("maestranza")
        resultado = self.clasificador.clasificar("Texto de prueba")
        self.assertEqual(resultado, "Maestranza - maestranza")

    def test_modelo_disponible_verdadero(self):
        """Verifica que modelo_disponible retorna True cuando hay modelo cargado."""
        self.assertTrue(self.clasificador.modelo_disponible())

    def test_modelo_disponible_falso(self):
        """Verifica que modelo_disponible retorna False sin modelo."""
        clasificador_vacio = Clasificador()
        clasificador_vacio._Clasificador__clf = None
        self.assertFalse(clasificador_vacio.modelo_disponible())


if __name__ == "__main__":
    unittest.main()
