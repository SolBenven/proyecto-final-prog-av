"""
Configuración base para tests con unittest.
Provee una clase base que configura la aplicación Flask y la base de datos.
"""

import sys
from pathlib import Path
import unittest

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class CasoTestBase(unittest.TestCase):
    """Clase base para todos los tests con configuración de Flask y SQLAlchemy."""

    def setUp(self):
        """Crea la aplicación y base de datos para cada test."""
        from modules.config import create_app, db

        # Crear aplicación de prueba
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-key",
        })

        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        # Crear tablas
        db.create_all()

        # Crear datos de prueba básicos
        self._crear_departamentos_prueba()

    def tearDown(self):
        """Limpia la base de datos después de cada test."""
        from modules.config import db

        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _crear_departamentos_prueba(self):
        """Crea departamentos de prueba."""
        from modules.config import db
        from modules.departamento import Departamento

        # Secretaría Técnica
        st = Departamento(
            nombre="secretaria_tecnica",
            nombre_mostrar="Secretaría Técnica",
            es_secretaria_tecnica=True,
        )
        # Departamentos regulares
        depto1 = Departamento(
            nombre="ciencias",
            nombre_mostrar="Departamento de Ciencias",
            es_secretaria_tecnica=False,
        )
        depto2 = Departamento(
            nombre="humanidades",
            nombre_mostrar="Departamento de Humanidades",
            es_secretaria_tecnica=False,
        )

        db.session.add_all([st, depto1, depto2])
        db.session.commit()

        # Guardar IDs para uso en tests
        self.departamentos_prueba = {
            "st_id": st.id,
            "depto1_id": depto1.id,
            "depto2_id": depto2.id,
        }
