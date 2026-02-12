from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from sqlalchemy.orm import Mapped, mapped_column
from modules.config import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


# Combinar metaclases de ABC y SQLAlchemy para evitar conflicto
class MetaModeloABC(ABCMeta, type(db.Model)):
    """Metaclase combinada para permitir ABC con SQLAlchemy Model."""

    pass


class Usuario(UserMixin, db.Model, ABC, metaclass=MetaModeloABC):
    """Clase base abstracta para todos los usuarios (Single Table Inheritance)"""

    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(nullable=False)
    apellido: Mapped[str] = mapped_column(nullable=False)
    correo: Mapped[str] = mapped_column(unique=True, nullable=False)
    nombre_usuario: Mapped[str] = mapped_column(unique=True, nullable=False)
    hash_contrasena: Mapped[str] = mapped_column(nullable=False)

    # Columna discriminadora para herencia
    tipo_usuario: Mapped[str] = mapped_column(nullable=False)

    __mapper_args__ = {"polymorphic_on": tipo_usuario, "polymorphic_identity": "usuario"}

    def establecer_contrasena(self, contrasena: str):
        self.hash_contrasena = generate_password_hash(contrasena)

    def verificar_contrasena(self, contrasena: str) -> bool:
        return check_password_hash(self.hash_contrasena, contrasena)

    @property
    @abstractmethod
    def nombre_completo(self) -> str:
        """Retorna el nombre completo con información de rol/claustro.

        Debe ser implementado por las subclases UsuarioFinal y UsuarioAdmin.
        """
        pass

    @staticmethod
    def obtener_por_nombre_usuario(nombre_usuario: str) -> Usuario | None:
        return db.session.query(Usuario).filter_by(nombre_usuario=nombre_usuario).first()

    @staticmethod
    def obtener_por_correo(correo: str) -> Usuario | None:
        return db.session.query(Usuario).filter_by(correo=correo).first()

    @staticmethod
    def obtener_por_id(usuario_id: int) -> Usuario | None:
        usuario = db.session.get(Usuario, usuario_id)
        if usuario is not None:
            print(f"Se obtuvo al usuario: {usuario.nombre_completo}")
        return usuario

    @staticmethod
    def correo_existe(correo: str) -> bool:
        """Verifica si el correo ya está registrado"""
        return Usuario.query.filter_by(correo=correo).first() is not None

    @staticmethod
    def nombre_usuario_existe(nombre_usuario: str) -> bool:
        """Verifica si el nombre de usuario ya está registrado"""
        return Usuario.query.filter_by(nombre_usuario=nombre_usuario).first() is not None

    @classmethod
    def autenticar(cls, nombre_usuario: str, contrasena: str) -> "Usuario | None":
        """Autentica un usuario por nombre_usuario y contraseña"""
        usuario = cls.query.filter_by(nombre_usuario=nombre_usuario).first()
        if usuario and usuario.verificar_contrasena(contrasena):
            return usuario
        return None

    @classmethod
    def _validar_y_persistir(cls, usuario: "Usuario", contrasena: str) -> tuple["Usuario | None", str | None]:
        """Valida unicidad de correo/nombre_usuario, setea contraseña y persiste.

        Returns:
            (usuario, None) si exitoso, (None, mensaje_error) si falla.
        """
        if Usuario.correo_existe(usuario.correo):
            return None, "El email ya está registrado"
        if Usuario.nombre_usuario_existe(usuario.nombre_usuario):
            return None, "El nombre de usuario ya está en uso"

        usuario.establecer_contrasena(contrasena)
        db.session.add(usuario)
        db.session.commit()
        return usuario, None

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.nombre_usuario}>"
