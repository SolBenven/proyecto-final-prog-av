from datetime import datetime as Datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from modules.config import db
from modules.reclamo import EstadoReclamo

if TYPE_CHECKING:
    from modules.reclamo import Reclamo
    from modules.usuario_admin import UsuarioAdmin
    from modules.notificacion_usuario import NotificacionUsuario


class HistorialEstadoReclamo(db.Model):
    """Historial de cambios de estado de un reclamo"""

    __tablename__ = "historial_estado_reclamo"

    id: Mapped[int] = mapped_column(primary_key=True)
    estado_anterior: Mapped[EstadoReclamo] = mapped_column(nullable=False)
    estado_nuevo: Mapped[EstadoReclamo] = mapped_column(nullable=False)
    cambiado_en: Mapped[Datetime] = mapped_column(default=Datetime.now)

    # Claves Foráneas
    reclamo_id: Mapped[int] = mapped_column(ForeignKey("reclamo.id"), nullable=False)
    cambiado_por_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)

    # Relaciones
    reclamo: Mapped["Reclamo"] = relationship("Reclamo", back_populates="historial_estados")
    cambiado_por: Mapped["UsuarioAdmin"] = relationship("UsuarioAdmin")
    notificaciones_usuario: Mapped[list["NotificacionUsuario"]] = relationship(
        "NotificacionUsuario", back_populates="historial_estado_reclamo"
    )

    def __init__(
        self,
        reclamo_id: int,
        estado_anterior: EstadoReclamo,
        estado_nuevo: EstadoReclamo,
        cambiado_por_id: int,
    ):
        self.reclamo_id = reclamo_id
        self.estado_anterior = estado_anterior
        self.estado_nuevo = estado_nuevo
        self.cambiado_por_id = cambiado_por_id

    def __repr__(self):
        return (
            f"<HistorialEstadoReclamo {self.estado_anterior.value} -> {self.estado_nuevo.value}>"
        )
