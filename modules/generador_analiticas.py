"""Generador de Analíticas y Estadísticas para el panel de administración."""

from __future__ import annotations

import base64
import io
import re
from collections import Counter
from typing import TYPE_CHECKING

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from modules.config import db
from modules.reclamo import Reclamo, EstadoReclamo
from modules.utils.constantes import STOPWORDS_ESPANOL_SET
from modules.utils.texto import normalizar_texto

if TYPE_CHECKING:
    from modules.departamento import Departamento


class GeneradorAnaliticas:
    """Generador de métricas y visualizaciones de reclamos."""

    COLORES_ESTADO = {
        "Pendiente": "#ffc107",
        "En proceso": "#17a2b8",
        "Resuelto": "#28a745",
        "Inválido": "#dc3545",
    }

    ETIQUETAS_ESTADO = {
        EstadoReclamo.PENDIENTE: "Pendiente",
        EstadoReclamo.EN_PROCESO: "En proceso",
        EstadoReclamo.RESUELTO: "Resuelto",
        EstadoReclamo.INVALIDO: "Inválido",
    }

    @staticmethod
    def obtener_estadisticas_reclamos(departamentos: list["Departamento"] | None = None) -> dict:
        conteos_crudos = Reclamo.obtener_conteo_estados(departamentos=departamentos)

        conteos_estado: dict[str, int] = {}
        for estado, conteo in conteos_crudos.items():
            if conteo > 0:
                etiqueta = GeneradorAnaliticas.ETIQUETAS_ESTADO[estado]
                conteos_estado[etiqueta] = conteo

        total = sum(conteos_estado.values())

        if total == 0:
            return {
                "total_reclamos": 0,
                "conteos_estado": {},
                "porcentajes_estado": {},
            }

        porcentajes_estado: dict[str, float] = {
            etiqueta: round((conteo / total) * 100, 1)
            for etiqueta, conteo in conteos_estado.items()
        }

        return {
            "total_reclamos": total,
            "conteos_estado": conteos_estado,
            "porcentajes_estado": porcentajes_estado,
        }

    @staticmethod
    def obtener_frecuencias_palabras(
        departamentos: list["Departamento"] | None = None, top_n: int = 20
    ) -> dict[str, int]:
        query = db.session.query(Reclamo.detalle)

        if departamentos is not None:
            if len(departamentos) == 0:
                return {}
            ids = [d.id for d in departamentos]
            query = query.filter(Reclamo.departamento_id.in_(ids))

        detalles = [fila[0] for fila in query.all()]

        if not detalles:
            return {}

        todas_palabras: list[str] = []
        for detalle in detalles:
            normalizado = normalizar_texto(detalle)
            palabras = re.findall(r"\b\w+\b", normalizado)
            filtradas = [
                p
                for p in palabras
                if p not in STOPWORDS_ESPANOL_SET and len(p) > 2 and not p.isdigit()
            ]
            todas_palabras.extend(filtradas)

        if not todas_palabras:
            return {}

        conteo_palabras = Counter(todas_palabras).most_common(top_n)
        return dict(conteo_palabras)

    @staticmethod
    def generar_grafico_torta(conteos_estado: dict[str, int]) -> str | None:
        if not conteos_estado:
            return None

        stats_filtradas = {k: v for k, v in conteos_estado.items() if v > 0}
        if not stats_filtradas:
            return None

        fig, ax = plt.subplots(figsize=(8, 6))
        colores = [
            GeneradorAnaliticas.COLORES_ESTADO.get(k, "#6c757d")
            for k in stats_filtradas.keys()
        ]

        wedges, texts, autotexts = ax.pie(
            stats_filtradas.values(),
            labels=stats_filtradas.keys(),
            colors=colores,
            autopct="%1.1f%%",
            startangle=90,
            textprops={"fontsize": 11},
        )

        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")

        ax.set_title(
            "Distribución de Reclamos por Estado", fontsize=14, fontweight="bold"
        )
        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(
            buffer, format="png", dpi=100, bbox_inches="tight", facecolor="white"
        )
        plt.close(fig)
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    @staticmethod
    def generar_nube_palabras(frecuencias_palabras: dict[str, int]) -> str | None:
        if not frecuencias_palabras:
            return None

        try:
            from wordcloud import WordCloud
        except ImportError:
            return None

        nube = WordCloud(
            width=800,
            height=400,
            background_color="white",
            colormap="viridis",
            max_words=50,
            min_font_size=10,
            prefer_horizontal=0.7,
        ).generate_from_frequencies(frecuencias_palabras)

        buffer = io.BytesIO()
        nube.to_image().save(buffer, format="PNG")
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    @staticmethod
    def obtener_analiticas_completas(departamentos: list["Departamento"] | None = None) -> dict:
        estadisticas = GeneradorAnaliticas.obtener_estadisticas_reclamos(departamentos)
        palabras_clave = GeneradorAnaliticas.obtener_frecuencias_palabras(departamentos)

        grafico_torta = GeneradorAnaliticas.generar_grafico_torta(
            estadisticas.get("conteos_estado", {})
        )
        nube_palabras = GeneradorAnaliticas.generar_nube_palabras(palabras_clave)

        return {
            "estadisticas": estadisticas,
            "grafico_torta": grafico_torta,
            "nube_palabras": nube_palabras,
            "palabras_clave": palabras_clave,
        }
