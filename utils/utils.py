import hashlib
import json
import math
import re
import time


def sha256_hex(text):
    return hashlib.sha256(text.encode()).hexdigest()


def stable_hash(obj):
    text = json.dumps(obj, sort_keys=True)
    return sha256_hex(text)


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def mean(values):
    if not values:
        return 0.0
    return sum(values) / len(values)


def stdev(values):
    if not values or len(values) < 2:
        return 0.0
    m = mean(values)
    variance = sum((x - m) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)


def now_ms():
    return int(time.time() * 1000)


def tokenize(text):
    # Tokenización determinista simple
    text = text.lower()
    tokens = re.findall(r"\w+", text)
    return tokens


def tf(text):
    tokens = tokenize(text)
    if not tokens:
        return {}
    counts = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    total = len(tokens)
    return {t: count / total for t, count in counts.items()}


def idf(docs_tokens):
    # docs_tokens es una lista de listas de tokens
    N = len(docs_tokens)
    if N == 0:
        return {}
    all_tokens = set(t for doc in docs_tokens for t in doc)
    idf_map = {}
    for t in all_tokens:
        df = sum(1 for doc in docs_tokens if t in doc)
        idf_map[t] = math.log(N / (1 + df))
    return idf_map


def tfidf_vec(text, idf_map):
    term_tf = tf(text)
    vec = {}
    for t, val in term_tf.items():
        if t in idf_map:
            vec[t] = val * idf_map[t]
    return vec


def cosine_sim(vec_a, vec_b):
    # Similitud coseno para vectores sparse (diccionarios)
    intersection = set(vec_a.keys()) & set(vec_b.keys())
    numerator = sum(vec_a[t] * vec_b[t] for t in intersection)

    sum_a = sum(val**2 for val in vec_a.values())
    sum_b = sum(val**2 for val in vec_b.values())

    denominator = math.sqrt(sum_a) * math.sqrt(sum_b)
    if not denominator:
        return 0.0
    return numerator / denominator
