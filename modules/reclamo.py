from __future__ import annotations

from datetime import datetime as Datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column, relationship

from modules.config import db

if TYPE_CHECKING:
    from modules.historial_estado_reclamo import HistorialEstadoReclamo
    from modules.adherente_reclamo import AdherenteReclamo
    from modules.derivacion_reclamo import DerivacionReclamo
    from modules.departamento import Departamento
    from modules.usuario_final import UsuarioFinal


class EstadoReclamo(Enum):
    """Estado de un reclamo"""

    INVALIDO = "Inválido"
    PENDIENTE = "Pendiente"
    EN_PROCESO = "En proceso"
    RESUELTO = "Resuelto"


class Reclamo(db.Model):
    """Reclamo creado por un usuario final"""

    __tablename__ = "reclamo"

    id: Mapped[int] = mapped_column(primary_key=True)
    detalle: Mapped[str] = mapped_column(nullable=False)
    estado: Mapped[EstadoReclamo] = mapped_column(default=EstadoReclamo.PENDIENTE)
    ruta_imagen: Mapped[str | None] = mapped_column(nullable=True)
    creado_en: Mapped[Datetime] = mapped_column(default=Datetime.now)
    actualizado_en: Mapped[Datetime] = mapped_column(
        default=Datetime.now, onupdate=Datetime.now
    )

    # Claves Foráneas
    departamento_id: Mapped[int] = mapped_column(
        ForeignKey("departamento.id"), nullable=False
    )
    creador_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)

    # Relaciones
    departamento: Mapped["Departamento"] = relationship(
        "Departamento", back_populates="reclamos"
    )
    creador: Mapped["UsuarioFinal"] = relationship(
        "UsuarioFinal", back_populates="reclamos_creados"
    )
    adherentes: Mapped[list["AdherenteReclamo"]] = relationship(
        "AdherenteReclamo", back_populates="reclamo", cascade="all, delete-orphan"
    )
    historial_estados: Mapped[list["HistorialEstadoReclamo"]] = relationship(
        "HistorialEstadoReclamo", back_populates="reclamo", cascade="all, delete-orphan"
    )
    derivaciones: Mapped[list["DerivacionReclamo"]] = relationship(
        "DerivacionReclamo", back_populates="reclamo", cascade="all, delete-orphan"
    )

    def __init__(
        self,
        detalle: str,
        departamento_id: int,
        creador_id: int,
        ruta_imagen: str | None = None,
    ):
        self.detalle = detalle
        self.departamento_id = departamento_id
        self.creador_id = creador_id
        self.ruta_imagen = ruta_imagen

    @property
    def cantidad_adherentes(self) -> int:
        """Retorna el número de adherentes"""
        return len(self.adherentes)

    def __repr__(self):
        return f"<Reclamo {self.id} - {self.estado.value}>"

    # ── Helpers privados ─────────────────────────────────────────────

    @staticmethod
    def _obtener_id_secretaria_tecnica() -> int | None:
        from modules.departamento import Departamento
        secretaria_tecnica = Departamento.obtener_secretaria_tecnica()
        return secretaria_tecnica.id if secretaria_tecnica else None

    @staticmethod
    def _clasificar_departamento(detalle: str) -> int | None:
        from modules.clasificador import clasificador
        from modules.departamento import Departamento

        try:
            nombre_predicho = clasificador.clasificar(detalle)
            departamento_predicho = Departamento.obtener_por_nombre(nombre_predicho)
            return departamento_predicho.id if departamento_predicho else None
        except Exception:
            return None

    @staticmethod
    def _resolver_departamento_id(
        detalle: str, departamento_id: int | None
    ) -> tuple[int | None, str | None]:
        from modules.departamento import Departamento

        if departamento_id is not None:
            departamento = Departamento.obtener_por_id(departamento_id)
            if not departamento:
                return None, "Departamento no válido"
            return departamento_id, None
        #este if va a ser utilizado para cargar reclamos en la base de datos para la prueba del programa. cuando se crea uno nuevo desde la pagina, se utiliza el clasificador automatico 
        
        id_clasificado = Reclamo._clasificar_departamento(detalle)
        if id_clasificado is not None:
            return id_clasificado, None

        id_tecnico = Reclamo._obtener_id_secretaria_tecnica()
        if id_tecnico is None:
            return None, "No se encontró la Secretaría Técnica"

        return id_tecnico, None

    # ── Métodos estáticos de creación / actualización ────────────────

    @staticmethod
    def crear(
        usuario_id: int,
        detalle: str,
        departamento_id: int | None = None,
        ruta_imagen: str | None = None,
    ) -> tuple["Reclamo | None", str | None]:
        if not detalle or detalle.strip() == "":
            return None, "El detalle del reclamo no puede estar vacío"

        departamento_id_resuelto, error = Reclamo._resolver_departamento_id(
            detalle, departamento_id
        )
        if error or not departamento_id_resuelto:
            return None, error

        reclamo = Reclamo(
            detalle=detalle.strip(),
            departamento_id=departamento_id_resuelto,
            creador_id=usuario_id,
            ruta_imagen=ruta_imagen,
        )

        db.session.add(reclamo)
        db.session.commit()

        return reclamo, None

    @staticmethod
    def actualizar_estado(
        reclamo_id: int, nuevo_estado: EstadoReclamo, usuario_admin_id: int
    ) -> tuple[bool, str | None]:
        from modules.historial_estado_reclamo import HistorialEstadoReclamo
        from modules.adherente_reclamo import AdherenteReclamo
        from modules.notificacion_usuario import NotificacionUsuario

        reclamo = db.session.get(Reclamo, reclamo_id)

        if not reclamo:
            return False, "Reclamo no encontrado"

        estado_anterior = reclamo.estado

        if estado_anterior == nuevo_estado:
            return False, "El estado no ha cambiado"

        reclamo.estado = nuevo_estado

        entrada_historial = HistorialEstadoReclamo(
            reclamo_id=reclamo_id,
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado,
            cambiado_por_id=usuario_admin_id,
        )

        db.session.add(entrada_historial)
        db.session.flush()

        notificacion_creador = NotificacionUsuario(
            usuario_id=reclamo.creador_id, historial_estado_reclamo_id=entrada_historial.id
        )
        db.session.add(notificacion_creador)

        adherentes = db.session.query(AdherenteReclamo).filter_by(reclamo_id=reclamo_id).all()
        for adherente in adherentes:
            notificacion_adherente = NotificacionUsuario(
                usuario_id=adherente.usuario_id, historial_estado_reclamo_id=entrada_historial.id
            )
            db.session.add(notificacion_adherente)

        db.session.commit()

        return True, None

    # ── Consultas estáticas ──────────────────────────────────────────

    @staticmethod
    def obtener_por_id(reclamo_id: int) -> "Reclamo | None":
        return db.session.get(Reclamo, reclamo_id)

    @staticmethod
    def obtener_pendientes(filtro_departamento_id: int | None = None) -> list["Reclamo"]:
        query = db.session.query(Reclamo).filter_by(estado=EstadoReclamo.PENDIENTE)
        if filtro_departamento_id is not None:
            query = query.filter_by(departamento_id=filtro_departamento_id)
        return query.order_by(Reclamo.creado_en.desc()).all()

    @staticmethod
    def obtener_todos_con_filtros(
        filtro_departamento: int | None = None, filtro_estado: EstadoReclamo | None = None
    ) -> list["Reclamo"]:
        query = db.session.query(Reclamo)
        if filtro_departamento is not None:
            query = query.filter_by(departamento_id=filtro_departamento)
        if filtro_estado is not None:
            query = query.filter_by(estado=filtro_estado)
        return query.order_by(Reclamo.creado_en.desc()).all()

    @staticmethod
    #con este vamos a ver cuantos reclamos hay en cada estado
    def obtener_conteo_estados(
        departamentos: list["Departamento"] | None = None,
    ) -> dict[EstadoReclamo, int]:
        #vamos a inicializar un diccionario donde por cada clave (estado (invalido, en proceso, etc.)) vamos a darle el valor=0
        conteos: dict[EstadoReclamo, int] = {estado: 0 for estado in EstadoReclamo}
        if departamentos is not None and len(departamentos) == 0:
            return conteos
        #iniciamos una consulta donde nos fijamos unicamente en la columna de estado
        query = db.session.query(Reclamo.estado, func.count(Reclamo.id))
        if departamentos is not None:
            ids = [d.id for d in departamentos]
            query = query.filter(Reclamo.departamento_id.in_(ids))
        conteos_query = query.group_by(Reclamo.estado).all()
        for estado, conteo in conteos_query:
            conteos[estado] = int(conteo)
        return conteos

    @staticmethod
    def obtener_conteos_dashboard(
        departamentos: list["Departamento"] | None = None,
    ) -> dict[str, int]:
        if departamentos is not None and len(departamentos) == 0:
            return {
                "total_reclamos": 0,
                "reclamos_pendientes": 0,
                "reclamos_en_proceso": 0,
                "reclamos_resueltos": 0,
                "reclamos_invalidos": 0,
            }
        conteo_estados = Reclamo.obtener_conteo_estados(departamentos)
        query_total = db.session.query(Reclamo)
        if departamentos is not None:
            ids = [d.id for d in departamentos]
            query_total = query_total.filter(Reclamo.departamento_id.in_(ids))
        total_reclamos = int(query_total.count() or 0)
        return {
            "total_reclamos": total_reclamos,
            "reclamos_pendientes": conteo_estados[EstadoReclamo.PENDIENTE],
            "reclamos_en_proceso": conteo_estados[EstadoReclamo.EN_PROCESO],
            "reclamos_resueltos": conteo_estados[EstadoReclamo.RESUELTO],
            "reclamos_invalidos": conteo_estados[EstadoReclamo.INVALIDO],
        }

    @staticmethod
    def obtener_conteos_dashboard_departamento(
        departamentos: list["Departamento"],
    ) -> dict[int, dict[str, int]]:
        if len(departamentos) == 0:
            return {}
        ids = [d.id for d in departamentos]
        por_depto: dict[int, dict[str, int]] = {
            depto_id: {
                "total": 0, "pendientes": 0, "en_proceso": 0, "resueltos": 0, "invalidos": 0,
            }
            for depto_id in ids
        }
        filas = (
            db.session.query(Reclamo.departamento_id, Reclamo.estado, func.count(Reclamo.id))
            .filter(Reclamo.departamento_id.in_(ids))
            .group_by(Reclamo.departamento_id, Reclamo.estado)
            .all()
        )
        for depto_id, estado, conteo in filas:
            depto_id_int = int(depto_id)
            conteo_int = int(conteo)
            por_depto[depto_id_int]["total"] += conteo_int
            if estado == EstadoReclamo.PENDIENTE:
                por_depto[depto_id_int]["pendientes"] = conteo_int
            elif estado == EstadoReclamo.EN_PROCESO:
                por_depto[depto_id_int]["en_proceso"] = conteo_int
            elif estado == EstadoReclamo.RESUELTO:
                por_depto[depto_id_int]["resueltos"] = conteo_int
            elif estado == EstadoReclamo.INVALIDO:
                por_depto[depto_id_int]["invalidos"] = conteo_int
        return por_depto

    # ── Adherentes ───────────────────────────────────────────────────

    @staticmethod
    def agregar_adherente(reclamo_id: int, usuario_id: int) -> tuple[bool, str | None]:
        from modules.adherente_reclamo import AdherenteReclamo

        reclamo = Reclamo.obtener_por_id(reclamo_id)
        if not reclamo:
            return False, "Reclamo no encontrado"
        if reclamo.creador_id == usuario_id:
            return False, "No puedes adherirte a tu propio reclamo"
        if Reclamo.es_usuario_adherente(reclamo_id, usuario_id):
            return False, "Ya estás adherido a este reclamo"

        adherente = AdherenteReclamo(reclamo_id=reclamo_id, usuario_id=usuario_id)
        try:
            db.session.add(adherente)
            db.session.commit()
            return True, None
        except IntegrityError:
            db.session.rollback()
            return False, "Error al adherirse al reclamo"

    @staticmethod
    def quitar_adherente(reclamo_id: int, usuario_id: int) -> tuple[bool, str | None]:
        from modules.adherente_reclamo import AdherenteReclamo

        adherente = (
            db.session.query(AdherenteReclamo)
            .filter_by(reclamo_id=reclamo_id, usuario_id=usuario_id)
            .first()
        )

        if not adherente:
            return False, "No estás adherido a este reclamo"

        db.session.delete(adherente)
        db.session.commit()
        return True, None

    @staticmethod
    def es_usuario_adherente(reclamo_id: int, usuario_id: int) -> bool:
        from modules.adherente_reclamo import AdherenteReclamo
        adherente = (
            db.session.query(AdherenteReclamo)
            .filter_by(reclamo_id=reclamo_id, usuario_id=usuario_id)
            .first()
        )
        return adherente is not None

    @staticmethod
    def obtener_por_usuario(usuario_id: int) -> list["Reclamo"]:
        reclamos = (
            db.session.query(Reclamo)
            .filter_by(creador_id=usuario_id)
            .order_by(Reclamo.creado_en.desc())
            .all()
        )
        return reclamos

    @staticmethod
    def obtener_adheridos_por_usuario(usuario_id: int) -> list["Reclamo"]:
        from modules.adherente_reclamo import AdherenteReclamo
        reclamos = (
            db.session.query(Reclamo)
            .join(AdherenteReclamo, Reclamo.id == AdherenteReclamo.reclamo_id)
            .filter(AdherenteReclamo.usuario_id == usuario_id)
            .order_by(AdherenteReclamo.creado_en.desc())
            .all()
        )
        return reclamos

    @staticmethod
    def obtener_por_departamentos(departamentos: list["Departamento"]) -> list["Reclamo"]:
        if not departamentos:
            return []
        ids = [d.id for d in departamentos]
        return (
            db.session.query(Reclamo)
            .filter(Reclamo.departamento_id.in_(ids))
            .order_by(Reclamo.creado_en.desc())
            .all()
        )

    @staticmethod
    def obtener_ids_adherentes(reclamo_id: int) -> list[int]:
        from modules.adherente_reclamo import AdherenteReclamo
        filas = (
            db.session.query(AdherenteReclamo.usuario_id)
            .filter_by(reclamo_id=reclamo_id)
            .order_by(AdherenteReclamo.creado_en.asc())
            .all()
        )
        return [int(usuario_id) for (usuario_id,) in filas]
