from datetime import datetime as Datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from modules.config import db

if TYPE_CHECKING:
    from modules.reclamo import Reclamo
    from modules.usuario_final import UsuarioFinal


class AdherenteReclamo(db.Model):
    """Adherente a un reclamo"""

    __tablename__ = "adherente_reclamo"
    __table_args__ = (
        UniqueConstraint("reclamo_id", "usuario_id", name="uq_adherente_reclamo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    creado_en: Mapped[Datetime] = mapped_column(default=Datetime.now)

    # Claves Foráneas
    reclamo_id: Mapped[int] = mapped_column(ForeignKey("reclamo.id"), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)

    # Relaciones
    reclamo: Mapped["Reclamo"] = relationship("Reclamo", back_populates="adherentes")
    usuario: Mapped["UsuarioFinal"] = relationship("UsuarioFinal", back_populates="reclamos_adheridos")

    def __init__(self, reclamo_id: int, usuario_id: int):
        self.reclamo_id = reclamo_id
        self.usuario_id = usuario_id

    def __repr__(self):
        return f"<AdherenteReclamo reclamo={self.reclamo_id} usuario={self.usuario_id}>"
