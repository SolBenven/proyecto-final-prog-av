"""
Detector de reclamos similares usando TF-IDF y similitud coseno.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from modules.utils.constantes import STOPWORDS_ESPANOL
from modules.utils.texto import normalizar_texto

if TYPE_CHECKING:
    from modules.reclamo import Reclamo


class BuscadorSimilitud:
    """Buscador de reclamos similares"""

    def __init__(self):
        self.vectorizador = TfidfVectorizer(
            stop_words=STOPWORDS_ESPANOL,
            min_df=1,
            ngram_range=(1, 2),
            max_features=1000,
            preprocessor=normalizar_texto,
        )

    def buscar_reclamos_similares(
        self,
        texto: str,
        departamento_id: int | None = None,
        umbral: float = 0.25,
        limite: int = 5,
    ) -> list[tuple["Reclamo", float]]:
        if not texto or not texto.strip():
            return []

        from modules.reclamo import Reclamo

        reclamos = Reclamo.obtener_pendientes(filtro_departamento_id=departamento_id)

        if not reclamos:
            return []

        textos = [texto] + [r.detalle for r in reclamos]

        try:
            matriz_tfidf = self.vectorizador.fit_transform(textos)
        except ValueError:
            return []

        similitudes = cosine_similarity(matriz_tfidf[0:1], matriz_tfidf[1:]).flatten()

        similares = [
            (reclamos[i], float(sim))
            for i, sim in enumerate(similitudes)
            if sim > umbral
        ]

        similares.sort(key=lambda x: x[1], reverse=True)

        return similares[:limite]


# Instancia global del buscador de similitud
buscador_similitud = BuscadorSimilitud()
