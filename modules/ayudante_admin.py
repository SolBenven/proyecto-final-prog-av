"""Helper para gestión de reclamos desde el panel de administración."""

from __future__ import annotations

from sqlalchemy.orm import joinedload, selectinload

from modules.config import db
from modules.reclamo import Reclamo, EstadoReclamo
from modules.departamento import Departamento
from modules.usuario_admin import UsuarioAdmin


class AyudanteAdmin:
    """Helper para gestión de reclamos con permisos de administración."""

    @staticmethod
    def obtener_reclamos_para_admin(
        usuario_admin: UsuarioAdmin, departamento_id: int | None = None
    ) -> list[Reclamo]:
        """Lista reclamos visibles para un admin."""
        departamentos_visibles = Departamento.obtener_para_admin(usuario_admin)

        if not departamentos_visibles:
            return []

        ids_visibles = [d.id for d in departamentos_visibles]

        if departamento_id is not None:
            if departamento_id not in ids_visibles:
                return []
            ids_filtro = [departamento_id]
        else:
            ids_filtro = ids_visibles

        return (
            db.session.query(Reclamo)
            .filter(Reclamo.departamento_id.in_(ids_filtro))
            .order_by(Reclamo.creado_en.desc())
            .all()
        )

    @staticmethod
    def obtener_reclamo_para_admin(usuario_admin: UsuarioAdmin, reclamo_id: int) -> Reclamo | None:
        reclamo = db.session.query(Reclamo).filter_by(id=reclamo_id).first()
        if not reclamo:
            return None
        return reclamo if usuario_admin.puede_acceder_reclamo(reclamo) else None

    @staticmethod
    def actualizar_estado_reclamo(
        usuario_admin: UsuarioAdmin, reclamo_id: int, nuevo_estado: EstadoReclamo
    ) -> tuple[bool, str | None]:
        reclamo = db.session.get(Reclamo, reclamo_id)
        if not reclamo:
            return False, "Reclamo no encontrado"

        if not usuario_admin.puede_acceder_reclamo(reclamo):
            return False, "No tienes permiso para gestionar este reclamo"

        return Reclamo.actualizar_estado(reclamo_id, nuevo_estado, usuario_admin.id)
