from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .base import BaseEngine
from .utils import cosine_sim, idf, tfidf_vec


class BDCSearchEngine(BaseEngine):
    """
    BDC Search: Índice semántico para AMA-Intent

    Igual que Associative Memory pero con namespace "bdc"
    para compatibilidad con nomenclatura existente.
    """

    name = "BDC-Search"
    version = "1.0.0"

    def __init__(self):
        self.docs: List[Dict[str, Any]] = []
        self._idf: Dict[str, float] = {}

    def _rebuild(self) -> None:
        texts = [d["text"] for d in self.docs]
        self._idf = idf(texts)
        for d in self.docs:
            d["vec"] = tfidf_vec(d["text"], self._idf)

    def _run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        op = payload.get("op", "search")
        if op == "ingest":
            new_docs = payload.get("docs", [])
            # Asegurar que cada doc tenga lo necesario
            for d in new_docs:
                if "id" not in d: d["id"] = str(len(self.docs))
                if "text" not in d: d["text"] = ""
            self.docs.extend(new_docs)
            self._rebuild()
            # Compatibilidad con EngineResult: debe ser un dict
            return {"status": "ingested", "count": len(new_docs)}

        query = payload.get("query", "")
        k = payload.get("k", 5)
        q_vec = tfidf_vec(query, self._idf)

        results = []
        q_toks = set(tokenize(query))
        for d in self.docs:
            sim = cosine_sim(q_vec, d.get("vec", {}))
            # Fallback para pocos documentos: coincidencia de palabras clave
            if sim == 0 and q_toks:
                d_toks = set(tokenize(d["text"]))
                if q_toks & d_toks:
                    sim = 0.1
            results.append({"id": d["id"], "score": sim, "text": d["text"]})

        results.sort(key=lambda x: x["score"], reverse=True)
        # Compatibilidad con tests: devolver lista directamente
        return results[:k]
