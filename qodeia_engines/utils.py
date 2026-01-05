from __future__ import annotations
from typing import Any, Dict, Iterable, List, Tuple
import math
import hashlib
import time

def sha256_hex(s: str) -> str:
    """Hash SHA-256 de string"""
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()

def stable_hash(obj: Any) -> str:
    """Hash estable de objeto"""
    return sha256_hex(repr(obj))

def clamp(x: float, lo: float, hi: float) -> float:
    """Limita valor entre min y max"""
    return max(lo, min(hi, x))

def mean(xs: Iterable[float]) -> float:
    """Media aritmética"""
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0

def stdev(xs: Iterable[float]) -> float:
    """Desviación estándar"""
    xs = list(xs)
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    var = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return math.sqrt(var)

def now_ms() -> int:
    """Timestamp en milisegundos"""
    return int(time.time() * 1000)

def tokenize(text: str) -> List[str]:
    """Tokenización simple pero determinista"""
    t = "".join(ch.lower() if ch.isalnum() else " " for ch in (text or ""))
    return [w for w in t.split() if w]

def cosine_sim(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Similitud coseno entre vectores sparse"""
    if not a or not b:
        return 0.0
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in a)
    na = math.sqrt(sum(v*v for v in a.values()))
    nb = math.sqrt(sum(v*v for v in b.values()))
    return dot / (na * nb) if (na > 0 and nb > 0) else 0.0

def tf(text: str) -> Dict[str, float]:
    """Term Frequency normalizado"""
    toks = tokenize(text)
    d: Dict[str, float] = {}
    for w in toks:
        d[w] = d.get(w, 0.0) + 1.0
    n = float(len(toks) or 1)
    return {k: v / n for k, v in d.items()}

def idf(docs: List[str]) -> Dict[str, float]:
    """Inverse Document Frequency (smooth)"""
    N = len(docs) or 1
    df: Dict[str, int] = {}
    for doc in docs:
        for w in set(tokenize(doc)):
            df[w] = df.get(w, 0) + 1
    return {w: math.log((N + 1) / (c + 1)) + 1.0 for w, c in df.items()}

def tfidf_vec(text: str, idf_map: Dict[str, float]) -> Dict[str, float]:
    """Vector TF-IDF"""
    t = tf(text)
    return {w: t[w] * idf_map.get(w, 0.0) for w in t}
