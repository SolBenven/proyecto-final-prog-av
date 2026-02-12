from datetime import datetime as Datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, joinedload

from modules.config import db

if TYPE_CHECKING:
    from modules.historial_estado_reclamo import HistorialEstadoReclamo
    from modules.usuario import Usuario


class NotificacionUsuario(db.Model):
    """
    Notificación individual por usuario.
    Cada cambio de estado de un reclamo genera una entrada por cada usuario afectado.
    """

    __tablename__ = "notificacion_usuario"

    id: Mapped[int] = mapped_column(primary_key=True)
    leido_en: Mapped[Datetime | None] = mapped_column(nullable=True, default=None)
    creado_en: Mapped[Datetime] = mapped_column(default=Datetime.now)

    # Claves Foráneas
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    historial_estado_reclamo_id: Mapped[int] = mapped_column(
        ForeignKey("historial_estado_reclamo.id"), nullable=False
    )

    # Relaciones
    usuario: Mapped["Usuario"] = relationship("Usuario")
    historial_estado_reclamo: Mapped["HistorialEstadoReclamo"] = relationship(
        "HistorialEstadoReclamo", back_populates="notificaciones_usuario"
    )

    def __init__(self, usuario_id: int, historial_estado_reclamo_id: int):
        self.usuario_id = usuario_id
        self.historial_estado_reclamo_id = historial_estado_reclamo_id

    @property
    def esta_leido(self) -> bool:
        return self.leido_en is not None

    def marcar_como_leido(self) -> None:
        if self.leido_en is None:
            self.leido_en = Datetime.now()

    def __repr__(self):
        estado = "leída" if self.esta_leido else "Pendiente"
        return f"<NotificacionUsuario usuario_id={self.usuario_id} {estado}>"

    @staticmethod
    def obtener_pendientes_usuario(usuario_id: int) -> list["NotificacionUsuario"]:
        from modules.historial_estado_reclamo import HistorialEstadoReclamo

        notificaciones = (
            db.session.query(NotificacionUsuario)
            .filter_by(usuario_id=usuario_id, leido_en=None)
            .options(
                joinedload(NotificacionUsuario.historial_estado_reclamo).joinedload(
                    HistorialEstadoReclamo.reclamo
                ),
                joinedload(NotificacionUsuario.historial_estado_reclamo).joinedload(
                    HistorialEstadoReclamo.cambiado_por
                ),
            )
            .order_by(NotificacionUsuario.creado_en.desc())
            .all()
        )
        return notificaciones

    @staticmethod
    def obtener_conteo_no_leidas(usuario_id: int) -> int:
        conteo = (
            db.session.query(NotificacionUsuario)
            .filter_by(usuario_id=usuario_id, leido_en=None)
            .count()
        )
        return conteo

    @staticmethod
    def marcar_notificacion_como_leida(
        notificacion_id: int, usuario_id: int
    ) -> tuple[bool, str | None]:
        notificacion = db.session.get(NotificacionUsuario, notificacion_id)
        if not notificacion:
            return False, "Notificación no encontrada"
        if notificacion.usuario_id != usuario_id:
            return False, "No tienes permiso para marcar esta notificación"
        notificacion.marcar_como_leido()
        db.session.commit()
        return True, None

    @staticmethod
    def marcar_todas_como_leidas_usuario(usuario_id: int) -> int:
        notificaciones = NotificacionUsuario.obtener_pendientes_usuario(usuario_id)
        conteo = 0
        for notificacion in notificaciones:
            notificacion.marcar_como_leido()
            conteo += 1
        db.session.commit()
        return conteo
