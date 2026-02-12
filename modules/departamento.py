from __future__ import annotations
from datetime import datetime as Datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from modules.config import db

if TYPE_CHECKING:
    from modules.reclamo import Reclamo
    from modules.usuario_admin import UsuarioAdmin


class Departamento(db.Model):
    """Departamento que gestiona reclamos"""

    __tablename__ = "departamento"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(unique=True, nullable=False)
    nombre_mostrar: Mapped[str] = mapped_column(nullable=False)
    es_secretaria_tecnica: Mapped[bool] = mapped_column(default=False)
    creado_en: Mapped[Datetime] = mapped_column(default=Datetime.now)

    # Relaciones
    reclamos: Mapped[list["Reclamo"]] = relationship("Reclamo", back_populates="departamento")
    usuarios_admin: Mapped[list["UsuarioAdmin"]] = relationship("UsuarioAdmin", back_populates="departamento")

    def __init__(self, nombre: str, nombre_mostrar: str, es_secretaria_tecnica: bool = False):
        self.nombre = nombre
        self.nombre_mostrar = nombre_mostrar
        self.es_secretaria_tecnica = es_secretaria_tecnica

    def __repr__(self):
        return f"<Departamento {self.nombre}>"

    @staticmethod
    def obtener_todos() -> list[Departamento]:
        return db.session.query(Departamento).order_by(Departamento.nombre_mostrar).all()

    @staticmethod
    def obtener_por_id(departamento_id: int) -> Departamento | None:
        return db.session.get(Departamento, departamento_id)

    @staticmethod
    def obtener_secretaria_tecnica() -> Departamento | None:
        return db.session.query(Departamento).filter_by(es_secretaria_tecnica=True).first()

    @staticmethod
    def obtener_por_nombre(nombre: str) -> Departamento | None:
        return db.session.query(Departamento).filter_by(nombre=nombre).first()

    @staticmethod
    def obtener_para_admin(usuario_admin: "UsuarioAdmin") -> list[Departamento]:
        if usuario_admin.es_secretario_tecnico:
            return Departamento.obtener_todos()
        if usuario_admin.departamento_id is None:
            return []
        departamento = Departamento.obtener_por_id(usuario_admin.departamento_id)
        return [departamento] if departamento else []
