"""
Tests para HistorialEstadoReclamo.
"""

import unittest
from tests.conftest import CasoTestBase
from modules.config import db
from modules.reclamo import Reclamo, EstadoReclamo
from modules.historial_estado_reclamo import HistorialEstadoReclamo
from modules.usuario_final import UsuarioFinal, Claustro
from modules.usuario_admin import UsuarioAdmin, RolAdmin


class TestHistorialEstadoReclamo(CasoTestBase):
    """Tests para el historial de estados de reclamos."""

    def setUp(self):
        """Crea usuario, admin y reclamo de prueba."""
        super().setUp()

        usuario = UsuarioFinal(
            nombre="Test", apellido="Usuario",
            correo="usuario@test.com", nombre_usuario="testusuario",
            claustro=Claustro.ESTUDIANTE,
        )
        usuario.establecer_contrasena("test123")
        db.session.add(usuario)
        db.session.commit()
        self.usuario_id = usuario.id

        admin, _ = UsuarioAdmin.crear(
            nombre="Admin", apellido="Test", correo="admin@test.com",
            nombre_usuario="admin", rol_admin=RolAdmin.SECRETARIO_TECNICO,
            contrasena="admin123", departamento_id=self.departamentos_prueba["st_id"],
        )
        self.admin_id = admin.id

        reclamo, _ = Reclamo.crear(
            usuario_id=self.usuario_id, detalle="Reclamo historial",
            departamento_id=self.departamentos_prueba["depto1_id"],
        )
        self.reclamo_id = reclamo.id

    def test_cambio_estado_crea_historial(self):
        """Verifica que cambiar estado genera entrada en historial."""
        Reclamo.actualizar_estado(self.reclamo_id, EstadoReclamo.EN_PROCESO, self.admin_id)

        historial = HistorialEstadoReclamo.query.filter_by(reclamo_id=self.reclamo_id).all()

        self.assertEqual(len(historial), 1)
        self.assertEqual(historial[0].estado_anterior, EstadoReclamo.PENDIENTE)
        self.assertEqual(historial[0].estado_nuevo, EstadoReclamo.EN_PROCESO)

    def test_multiples_cambios_estado(self):
        """Verifica que múltiples cambios generan múltiples entradas."""
        Reclamo.actualizar_estado(self.reclamo_id, EstadoReclamo.EN_PROCESO, self.admin_id)
        Reclamo.actualizar_estado(self.reclamo_id, EstadoReclamo.RESUELTO, self.admin_id)

        historial = HistorialEstadoReclamo.query.filter_by(reclamo_id=self.reclamo_id).all()

        self.assertEqual(len(historial), 2)

    def test_repr_historial(self):
        """Verifica la representación string del historial."""
        Reclamo.actualizar_estado(self.reclamo_id, EstadoReclamo.EN_PROCESO, self.admin_id)

        historial = HistorialEstadoReclamo.query.filter_by(reclamo_id=self.reclamo_id).first()
        representacion = repr(historial)

        self.assertIn("HistorialEstadoReclamo", representacion)
        self.assertIn("Pendiente", representacion)
        self.assertIn("En proceso", representacion)


if __name__ == "__main__":
    unittest.main()
