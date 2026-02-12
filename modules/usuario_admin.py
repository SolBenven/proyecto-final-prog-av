from enum import Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from modules.usuario import Usuario
from modules.config import db
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modules.departamento import Departamento


class RolAdmin(Enum):
    """Rol de un usuario administrativo"""

    JEFE_DEPARTAMENTO = "jefe_departamento"
    SECRETARIO_TECNICO = "secretario_tecnico"


class UsuarioAdmin(Usuario):
    """Usuario administrativo que gestiona reclamos"""

    # Campos específicos de UsuarioAdmin
    departamento_id: Mapped[int | None] = mapped_column(
        ForeignKey("departamento.id"), nullable=True
    )
    rol_admin: Mapped[RolAdmin | None] = mapped_column(nullable=True)

    # Relaciones
    departamento: Mapped["Departamento"] = relationship(
        "Departamento", back_populates="usuarios_admin"
    )

    __mapper_args__ = {"polymorphic_identity": "usuario_admin"}

    def __init__(
        self,
        nombre: str,
        apellido: str,
        correo: str,
        nombre_usuario: str,
        rol_admin: RolAdmin,
        departamento_id: int | None = None,
    ):
        self.nombre = nombre
        self.apellido = apellido
        self.correo = correo
        self.nombre_usuario = nombre_usuario
        self.rol_admin = rol_admin
        self.departamento_id = departamento_id

    @property
    def es_jefe_departamento(self) -> bool:
        return self.rol_admin == RolAdmin.JEFE_DEPARTAMENTO

    @property
    def es_secretario_tecnico(self) -> bool:
        return self.rol_admin == RolAdmin.SECRETARIO_TECNICO

    def puede_acceder_reclamo(self, reclamo) -> bool:
        """Verifica si este admin puede gestionar un reclamo específico."""
        if self.es_secretario_tecnico:
            return True
        return self.es_jefe_departamento and self.departamento_id == reclamo.departamento_id

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido} - {self.rol_admin.value if self.rol_admin else 'sin rol'}"

    @staticmethod
    def crear(
        nombre: str,
        apellido: str,
        correo: str,
        nombre_usuario: str,
        rol_admin: RolAdmin,
        contrasena: str,
        departamento_id: int | None = None,
    ) -> tuple["UsuarioAdmin | None", str | None]:
        """
        Crea un nuevo usuario administrativo (solo por scripts de sistema).
        Retorna (usuario, None) si exitoso, (None, mensaje_error) si falla.
        """
        usuario = UsuarioAdmin(
            nombre=nombre,
            apellido=apellido,
            correo=correo,
            nombre_usuario=nombre_usuario,
            rol_admin=rol_admin,
            departamento_id=departamento_id,
        )
        return Usuario._validar_y_persistir(usuario, contrasena)
