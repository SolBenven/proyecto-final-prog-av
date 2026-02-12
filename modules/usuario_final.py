from enum import Enum
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from modules.usuario import Usuario
from modules.config import db

if TYPE_CHECKING:
    from modules.reclamo import Reclamo
    from modules.adherente_reclamo import AdherenteReclamo


class Claustro(Enum):
    """Claustro al que pertenece un usuario final"""

    ESTUDIANTE = "estudiante"
    DOCENTE = "docente"
    PAYS = "PAyS"  # Personal de Apoyo y Servicios


class UsuarioFinal(Usuario):
    """Usuario final que crea y adhiere a reclamos"""

    # Campos específicos de UsuarioFinal
    claustro: Mapped[Claustro | None] = mapped_column(nullable=True)

    # Relaciones
    reclamos_creados: Mapped[list["Reclamo"]] = relationship(
        "Reclamo", back_populates="creador"
    )
    reclamos_adheridos: Mapped[list["AdherenteReclamo"]] = relationship(
        "AdherenteReclamo", back_populates="usuario"
    )

    __mapper_args__ = {"polymorphic_identity": "usuario_final"}

    def __init__(
        self,
        nombre: str,
        apellido: str,
        correo: str,
        nombre_usuario: str,
        claustro: Claustro,
    ):
        self.nombre = nombre
        self.apellido = apellido
        self.correo = correo
        self.nombre_usuario = nombre_usuario
        self.claustro = claustro

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido} - {self.claustro.value if self.claustro else 'sin claustro'}"

    @staticmethod
    def registrar(
        nombre: str,
        apellido: str,
        correo: str,
        nombre_usuario: str,
        claustro: Claustro,
        contrasena: str,
    ) -> tuple["UsuarioFinal | None", str | None]:
        """
        Registra un nuevo usuario final.
        Retorna (usuario, None) si exitoso, (None, mensaje_error) si falla.
        """
        usuario = UsuarioFinal(
            nombre=nombre,
            apellido=apellido,
            correo=correo,
            nombre_usuario=nombre_usuario,
            claustro=claustro,
        )
        return Usuario._validar_y_persistir(usuario, contrasena)
