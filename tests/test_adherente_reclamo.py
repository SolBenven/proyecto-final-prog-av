"""
Tests para sistema de adherentes (AdherenteReclamo).
"""

import unittest
from tests.conftest import CasoTestBase
from modules.config import db
from modules.reclamo import Reclamo
from modules.usuario_final import UsuarioFinal, Claustro


class TestAdherenteReclamo(CasoTestBase):
    """Tests para el sistema de adherentes."""

    def setUp(self):
        """Crea usuarios y reclamo de prueba."""
        super().setUp()

        # Usuario creador
        creador = UsuarioFinal(
            nombre="Creador",
            apellido="Usuario",
            correo="creador@test.com",
            nombre_usuario="creador",
            claustro=Claustro.DOCENTE,
        )
        creador.establecer_contrasena("test123")

        # Usuario adherente
        adherente = UsuarioFinal(
            nombre="Adherente",
            apellido="Usuario",
            correo="adherente@test.com",
            nombre_usuario="adherente",
            claustro=Claustro.ESTUDIANTE,
        )
        adherente.establecer_contrasena("test123")

        db.session.add_all([creador, adherente])
        db.session.commit()

        self.creador_id = creador.id
        self.adherente_id = adherente.id

        # Crear reclamo
        reclamo, _ = Reclamo.crear(
            usuario_id=self.creador_id,
            detalle="Reclamo para adherentes",
            departamento_id=self.departamentos_prueba["depto1_id"],
        )
        self.reclamo_id = reclamo.id

    def test_agregar_adherente_exitoso(self):
        """Verifica que un usuario puede adherirse a un reclamo."""
        exito, error = Reclamo.agregar_adherente(self.reclamo_id, self.adherente_id)

        self.assertTrue(exito)
        self.assertIsNone(error)

    def test_es_usuario_adherente_verdadero(self):
        """Verifica que es_usuario_adherente retorna True cuando está adherido."""
        Reclamo.agregar_adherente(self.reclamo_id, self.adherente_id)

        es_adherente = Reclamo.es_usuario_adherente(self.reclamo_id, self.adherente_id)

        self.assertTrue(es_adherente)

    def test_es_usuario_adherente_falso(self):
        """Verifica que es_usuario_adherente retorna False cuando no está adherido."""
        es_adherente = Reclamo.es_usuario_adherente(self.reclamo_id, self.adherente_id)

        self.assertFalse(es_adherente)

    def test_agregar_adherente_dos_veces_falla(self):
        """Verifica que no se puede adherir dos veces."""
        Reclamo.agregar_adherente(self.reclamo_id, self.adherente_id)

        exito, error = Reclamo.agregar_adherente(self.reclamo_id, self.adherente_id)

        self.assertFalse(exito)
        self.assertIsNotNone(error)

    def test_creador_no_puede_adherirse_propio_reclamo(self):
        """Verifica que el creador no puede adherirse a su propio reclamo."""
        exito, error = Reclamo.agregar_adherente(self.reclamo_id, self.creador_id)

        self.assertFalse(exito)
        self.assertIsNotNone(error)

    def test_quitar_adherente_exitoso(self):
        """Verifica que un usuario puede quitar su adhesión."""
        Reclamo.agregar_adherente(self.reclamo_id, self.adherente_id)

        exito, error = Reclamo.quitar_adherente(self.reclamo_id, self.adherente_id)

        self.assertTrue(exito)
        self.assertIsNone(error)

    def test_quitar_adherente_cuando_no_adherido(self):
        """Verifica que no se puede quitar adhesión si no está adherido."""
        exito, error = Reclamo.quitar_adherente(self.reclamo_id, self.adherente_id)

        self.assertFalse(exito)
        self.assertIsNotNone(error)

    def test_agregar_adherente_reclamo_invalido(self):
        """Verifica que no se puede adherir a reclamo inexistente."""
        exito, error = Reclamo.agregar_adherente(9999, self.adherente_id)

        self.assertFalse(exito)
        self.assertIsNotNone(error)

    def test_obtener_adheridos_por_usuario(self):
        """Verifica que obtener_adheridos_por_usuario retorna reclamos adheridos."""
        Reclamo.agregar_adherente(self.reclamo_id, self.adherente_id)

        adheridos = Reclamo.obtener_adheridos_por_usuario(self.adherente_id)

        self.assertEqual(len(adheridos), 1)
        self.assertEqual(adheridos[0].id, self.reclamo_id)

    def test_obtener_ids_adherentes(self):
        """Verifica que obtener_ids_adherentes retorna los IDs de adherentes."""
        Reclamo.agregar_adherente(self.reclamo_id, self.adherente_id)

        ids = Reclamo.obtener_ids_adherentes(self.reclamo_id)

        self.assertIn(self.adherente_id, ids)

    def test_multiples_adherentes(self):
        """Verifica que múltiples usuarios pueden adherirse."""
        # Crear otro usuario
        adherente2 = UsuarioFinal(
            nombre="Segundo",
            apellido="Adherente",
            correo="adherente2@test.com",
            nombre_usuario="adherente2",
            claustro=Claustro.PAYS,
        )
        adherente2.establecer_contrasena("test123")
        db.session.add(adherente2)
        db.session.commit()

        Reclamo.agregar_adherente(self.reclamo_id, self.adherente_id)
        Reclamo.agregar_adherente(self.reclamo_id, adherente2.id)

        self.assertTrue(Reclamo.es_usuario_adherente(self.reclamo_id, self.adherente_id))
        self.assertTrue(Reclamo.es_usuario_adherente(self.reclamo_id, adherente2.id))


if __name__ == "__main__":
    unittest.main()
