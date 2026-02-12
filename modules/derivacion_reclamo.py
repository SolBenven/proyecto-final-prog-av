from __future__ import annotations

from datetime import datetime as Datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from modules.config import db

if TYPE_CHECKING:
    from modules.reclamo import Reclamo
    from modules.departamento import Departamento
    from modules.usuario_admin import UsuarioAdmin


class DerivacionReclamo(db.Model):
    """Derivación de un reclamo entre departamentos"""

    __tablename__ = "derivacion_reclamo"

    id: Mapped[int] = mapped_column(primary_key=True)
    motivo: Mapped[str | None] = mapped_column(nullable=True)
    derivado_en: Mapped[Datetime] = mapped_column(default=Datetime.now)

    # Claves Foráneas
    reclamo_id: Mapped[int] = mapped_column(ForeignKey("reclamo.id"), nullable=False)
    departamento_origen_id: Mapped[int] = mapped_column(ForeignKey("departamento.id"), nullable=False)
    departamento_destino_id: Mapped[int] = mapped_column(ForeignKey("departamento.id"), nullable=False)
    derivado_por_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)

    # Relaciones
    reclamo: Mapped["Reclamo"] = relationship("Reclamo", back_populates="derivaciones")
    departamento_origen: Mapped["Departamento"] = relationship("Departamento", foreign_keys=[departamento_origen_id])
    departamento_destino: Mapped["Departamento"] = relationship("Departamento", foreign_keys=[departamento_destino_id])
    derivado_por: Mapped["UsuarioAdmin"] = relationship("UsuarioAdmin")

    def __init__(
        self,
        reclamo_id: int,
        departamento_origen_id: int,
        departamento_destino_id: int,
        derivado_por_id: int,
        motivo: str | None = None,
    ):
        self.reclamo_id = reclamo_id
        self.departamento_origen_id = departamento_origen_id
        self.departamento_destino_id = departamento_destino_id
        self.derivado_por_id = derivado_por_id
        self.motivo = motivo

    def __repr__(self):
        return f"<DerivacionReclamo reclamo={self.reclamo_id} {self.departamento_origen_id} -> {self.departamento_destino_id}>"

    @staticmethod
    def derivar(
        reclamo_id: int,
        departamento_destino_id: int,
        derivado_por_id: int,
        motivo: str | None = None,
    ) -> tuple["DerivacionReclamo | None", str | None]:
        from modules.reclamo import Reclamo
        from modules.departamento import Departamento

        reclamo = db.session.get(Reclamo, reclamo_id)
        if not reclamo:
            return None, "Reclamo no encontrado"

        departamento_destino = Departamento.obtener_por_id(departamento_destino_id)
        if not departamento_destino:
            return None, "Departamento destino no válido"

        if reclamo.departamento_id == departamento_destino_id:
            return None, "El reclamo ya pertenece a ese departamento"

        departamento_origen_id = reclamo.departamento_id

        derivacion = DerivacionReclamo(
            reclamo_id=reclamo_id,
            departamento_origen_id=departamento_origen_id,
            departamento_destino_id=departamento_destino_id,
            derivado_por_id=derivado_por_id,
            motivo=motivo.strip() if motivo else None,
        )

        reclamo.departamento_id = departamento_destino_id

        db.session.add(derivacion)
        db.session.commit()

        return derivacion, None

    @staticmethod
    def obtener_historial_reclamo(reclamo_id: int) -> list["DerivacionReclamo"]:
        return (
            db.session.query(DerivacionReclamo)
            .filter(DerivacionReclamo.reclamo_id == reclamo_id)
            .order_by(DerivacionReclamo.derivado_en.desc())
            .all()
        )

    @staticmethod
    def obtener_departamentos_disponibles(departamento_actual_id: int) -> list["Departamento"]:
        from modules.departamento import Departamento
        todos_departamentos = Departamento.obtener_todos()
        return [d for d in todos_departamentos if d.id != departamento_actual_id]

    @staticmethod
    def puede_derivar(usuario_admin) -> bool:
        return usuario_admin.es_secretario_tecnico
