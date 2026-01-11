import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.utils import cosine_sim, idf, tfidf_vec, tokenize


class BDCSearch:
    def __init__(self):
        self.docs = []
        self.idf_map = {}
        self.doc_vectors = []

    def ingest(self, docs):
        # docs: list of {"id": str, "text": str, "meta": dict}
        self.docs.extend(docs)
        self._rebuild()

    def _rebuild(self):
        all_tokens = [tokenize(doc["text"]) for doc in self.docs]
        self.idf_map = idf(all_tokens)
        self.doc_vectors = [
            {
                "id": doc["id"],
                "vec": tfidf_vec(doc["text"], self.idf_map),
                "meta": doc.get("meta", {}),
            }
            for doc in self.docs
        ]

    def search(self, query, k=5):
        query_vec = tfidf_vec(query, self.idf_map)
        results = []
        for doc_vec in self.doc_vectors:
            sim = cosine_sim(query_vec, doc_vec["vec"])
            results.append({"id": doc_vec["id"], "score": sim, "meta": doc_vec["meta"]})

        # Ordenar por score descendente
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]

    def run(self, payload):
        op = payload.get("op")
        if op == "ingest":
            self.ingest(payload.get("docs", []))
            return {"status": "success", "count": len(self.docs)}
        elif op == "search":
            query = payload.get("query", "")
            k = payload.get("k", 5)
            return self.search(query, k)
        else:
            raise ValueError(f"Unknown operation '{op}' for BDC-Search")
