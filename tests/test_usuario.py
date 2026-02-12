"""Tests para métodos estáticos y de clase de Usuario."""

import unittest
from tests.conftest import CasoTestBase
from modules.config import db
from modules.usuario import Usuario
from modules.usuario_final import UsuarioFinal, Claustro


class TestUsuarioMetodos(CasoTestBase):
    """Tests para métodos de búsqueda y autenticación de Usuario."""

    def setUp(self):
        """Crea un usuario de prueba."""
        super().setUp()

        usuario = UsuarioFinal(
            nombre="Test",
            apellido="User",
            correo="test@test.com",
            nombre_usuario="testuser",
            claustro=Claustro.ESTUDIANTE,
        )
        usuario.establecer_contrasena("password123")
        db.session.add(usuario)
        db.session.commit()
        self.usuario_id = usuario.id

    def test_obtener_por_nombre_usuario(self):
        """Verifica obtener_por_nombre_usuario con usuario existente."""
        usuario = Usuario.obtener_por_nombre_usuario("testuser")
        self.assertIsNotNone(usuario)
        self.assertEqual(usuario.nombre_usuario, "testuser")

    def test_obtener_por_nombre_usuario_inexistente(self):
        """Verifica obtener_por_nombre_usuario con usuario inexistente."""
        usuario = Usuario.obtener_por_nombre_usuario("noexiste")
        self.assertIsNone(usuario)

    def test_obtener_por_correo(self):
        """Verifica obtener_por_correo con correo existente."""
        usuario = Usuario.obtener_por_correo("test@test.com")
        self.assertIsNotNone(usuario)
        self.assertEqual(usuario.correo, "test@test.com")

    def test_obtener_por_id(self):
        """Verifica obtener_por_id con ID existente."""
        usuario = Usuario.obtener_por_id(self.usuario_id)
        self.assertIsNotNone(usuario)
        self.assertEqual(usuario.id, self.usuario_id)

    def test_obtener_por_id_inexistente(self):
        """Verifica obtener_por_id con ID inexistente retorna None."""
        usuario = Usuario.obtener_por_id(9999)
        self.assertIsNone(usuario)

    def test_autenticar_exitoso(self):
        """Verifica autenticación exitosa."""
        usuario = Usuario.autenticar("testuser", "password123")
        self.assertIsNotNone(usuario)
        self.assertEqual(usuario.nombre_usuario, "testuser")

    def test_autenticar_contrasena_incorrecta(self):
        """Verifica que autenticación falla con contraseña incorrecta."""
        usuario = Usuario.autenticar("testuser", "wrongpassword")
        self.assertIsNone(usuario)

    def test_autenticar_usuario_inexistente(self):
        """Verifica que autenticación falla con usuario inexistente."""
        usuario = Usuario.autenticar("noexiste", "password123")
        self.assertIsNone(usuario)

    def test_repr(self):
        """Verifica la representación string del usuario."""
        usuario = Usuario.obtener_por_id(self.usuario_id)
        repr_str = repr(usuario)
        self.assertIn("testuser", repr_str)


if __name__ == "__main__":
    unittest.main()
