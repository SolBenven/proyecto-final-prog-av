"""Generador de Reportes para el panel de administración."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

from flask import render_template

from modules.reclamo import Reclamo
from modules.departamento import Departamento
from modules.generador_analiticas import GeneradorAnaliticas
from modules.utils.constantes import CSS_PDF

if TYPE_CHECKING:
    pass


class Reporte(ABC):
    """Clase base abstracta para generación de reportes."""

    def __init__(self, departamentos: list[Departamento], es_secretario_tecnico: bool = False):
        self.departamentos = departamentos
        self.es_secretario_tecnico = es_secretario_tecnico

    def _obtener_reclamos(self) -> list[Reclamo]:
        return Reclamo.obtener_por_departamentos(self.departamentos)

    def _obtener_estadisticas(self) -> dict:
        return GeneradorAnaliticas.obtener_estadisticas_reclamos(self.departamentos)

    @abstractmethod
    def generar(self) -> str | bytes | None:
        pass


class ReporteHTML(Reporte):
    def generar(self) -> str:
        estadisticas = self._obtener_estadisticas()
        # Adaptar claves para template
        stats_template = {
            "total_claims": estadisticas.get("total_reclamos", 0),
            "status_counts": estadisticas.get("conteos_estado", {}),
            "status_percentages": estadisticas.get("porcentajes_estado", {}),
        }
        return render_template(
            "reports/department_report.html",
            departments=self.departamentos,
            claims=self._obtener_reclamos(),
            stats=stats_template,
            is_technical_secretary=self.es_secretario_tecnico,
            generated_at=datetime.now(),
            pdf_css=CSS_PDF,
        )


class ReportePDF(Reporte):
    def generar(self) -> bytes | None:
        try:
            from io import BytesIO
            from xhtml2pdf import pisa
        except ImportError:
            return None

        try:
            reporte_html = ReporteHTML(self.departamentos, self.es_secretario_tecnico)
            contenido_html = reporte_html.generar()

            buffer_pdf = BytesIO()
            estado_pisa = pisa.CreatePDF(src=contenido_html, dest=buffer_pdf)

            if estado_pisa.err:
                return None

            bytes_pdf = buffer_pdf.getvalue()
            buffer_pdf.close()
            return bytes_pdf
        except Exception:
            return None


def crear_reporte(
    formato_reporte: str,
    departamentos: list[Departamento],
    es_secretario_tecnico: bool = False,
) -> Reporte:
    if formato_reporte == "pdf":
        return ReportePDF(departamentos, es_secretario_tecnico)
    return ReporteHTML(departamentos, es_secretario_tecnico)
