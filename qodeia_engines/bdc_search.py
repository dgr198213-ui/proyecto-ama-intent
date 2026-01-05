from __future__ import annotations
from typing import Dict, Any, List, Tuple
from .base import BaseEngine
from .utils import idf, tfidf_vec, cosine_sim

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
            self.docs.extend(new_docs)
            self._rebuild()
            return {"status": "ingested", "count": len(new_docs)}
        
        query = payload.get("query", "")
        k = payload.get("k", 5)
        q_vec = tfidf_vec(query, self._idf)
        
        results = []
        for d in self.docs:
            sim = cosine_sim(q_vec, d.get("vec", {}))
            results.append({"id": d["id"], "score": sim, "text": d["text"]})
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return {"bdc": {"results": results[:k]}}
