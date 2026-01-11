from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .base import BaseEngine
from .utils import cosine_sim, idf, tfidf_vec


class AssociativeMemoryEngine(BaseEngine):
    """
    Memoria Asociativa con búsqueda semántica

    Operaciones:
    - ingest: añadir documentos
    - query: buscar por similitud
    - stats: estadísticas de índice
    """

    name = "Associative-Memory"
    version = "1.0.0"

    def __init__(self):
        self.items: List[Dict[str, Any]] = []
        self._idf: Dict[str, float] = {}

    def _rebuild(self) -> None:
        """Reconstruye índice TF-IDF"""
        docs = [it["text"] for it in self.items]
        self._idf = idf(docs)

    def _run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        op = payload.get("op", "query")

        if op == "ingest":
            return self._ingest(payload)
        elif op == "stats":
            return self._stats()
        else:
            return self._query(payload)

    def _ingest(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Añade items al índice"""
        item = {
            "id": str(payload.get("id", f"item_{len(self.items)+1}")),
            "text": str(payload.get("text", "")),
            "meta": dict(payload.get("meta") or {}),
        }
        self.items.append(item)
        self._rebuild()

        return {"associative": {"ingested": item["id"], "count": len(self.items)}}

    def _query(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Búsqueda por similitud"""
        q = str(payload.get("query", payload.get("text", "")))
        k = int(payload.get("k", 5))

        if not self.items:
            return {"associative": {"results": [], "count": 0}}

        qv = tfidf_vec(q, self._idf)
        scored: List[Tuple[float, Dict[str, Any]]] = []

        for it in self.items:
            iv = tfidf_vec(it["text"], self._idf)
            scored.append((cosine_sim(qv, iv), it))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = [
            {
                "score": float(s),
                "id": it["id"],
                "meta": it["meta"],
                "text": it["text"][:400],
            }
            for s, it in scored[:k]
        ]

        return {
            "associative": {
                "results": results,
                "count": len(self.items),
                "query": q[:100],
            }
        }

    def _stats(self) -> Dict[str, Any]:
        """Estadísticas del índice"""
        return {
            "associative": {
                "total_items": len(self.items),
                "vocabulary_size": len(self._idf),
                "avg_text_len": sum(len(it["text"]) for it in self.items)
                / max(1, len(self.items)),
            }
        }
