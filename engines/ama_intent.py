import re
import hashlib
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# =========================
# 1. TIPOS Y ESTRUCTURAS
# =========================

class RequestType(Enum):
    """Tipos de solicitud clasificados"""
    INFORMATIONAL = "informacional"
    ANALYTICAL = "analítica"
    CREATIVE = "creativa"
    TECHNICAL = "técnica"
    CONVERSATIONAL = "conversacional"
    INSTRUCTIONAL = "instruccional"
    SENSITIVE = "sensible"

@dataclass
class Intent:
    """Representación inmutable de la intención I₀"""
    raw_text: str
    intent_hash: str
    request_type: RequestType
    core_goal: str
    key_entities: List[str]
    ambiguity_score: float
    complexity_score: float
    timestamp: str
    
    def __eq__(self, other):
        """Compara intenciones por hash"""
        if not isinstance(other, Intent):
            return False
        return self.intent_hash == other.intent_hash

# =========================
# 2. EXTRACCIÓN DE INTENCIÓN
# =========================

def extract_intent(prompt: str, timestamp: Optional[str] = None) -> Intent:
    """
    Extrae y cristaliza la intención original I₀.
    Esta representación es INMUTABLE.
    """
    from datetime import datetime
    
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    
    # Normalizar texto
    normalized = _normalize_text(prompt)
    
    # Hash criptográfico de la intención
    intent_hash = hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]
    
    # Clasificar tipo de solicitud
    req_type = classify_request_type(prompt)
    
    # Extraer objetivo central
    core_goal = _extract_core_goal(prompt, req_type)
    
    # Extraer entidades clave
    entities = _extract_key_entities(prompt)
    
    # Calcular métricas
    ambiguity = detect_ambiguity(prompt)
    complexity = calculate_complexity(prompt)
    
    return Intent(
        raw_text=prompt,
        intent_hash=intent_hash,
        request_type=req_type,
        core_goal=core_goal,
        key_entities=entities,
        ambiguity_score=ambiguity,
        complexity_score=complexity,
        timestamp=timestamp
    )

# =========================
# 3. VALIDACIÓN DE INMUTABILIDAD
# =========================

def validate_intent_immutability(I0: Intent, I_current: Intent) -> bool:
    """Verifica que la intención no haya sido alterada."""
    if I0.intent_hash != I_current.intent_hash:
        return False
    if I0.request_type != I_current.request_type:
        return False
    similarity = _semantic_similarity(I0.core_goal, I_current.core_goal)
    if similarity < 0.85:
        return False
    return True

# =========================
# 4. CLASIFICACIÓN DE TIPO
# =========================

def classify_request_type(prompt: str) -> RequestType:
    prompt_lower = prompt.lower()
    patterns = {
        RequestType.INFORMATIONAL: [
            r'\b(qué es|cuál es|define|explica|información sobre)\b',
            r'\b(dime|cuéntame|háblame)\b.*\b(sobre|acerca de)\b'
        ],
        RequestType.ANALYTICAL: [
            r'\b(analiza|compara|evalúa|examina|estudia)\b',
            r'\b(diferencia|ventaja|desventaja|pros|contras)\b'
        ],
        RequestType.CREATIVE: [
            r'\b(crea|genera|escribe|diseña|imagina)\b',
            r'\b(historia|poema|artículo|contenido)\b'
        ],
        RequestType.TECHNICAL: [
            r'\b(código|programa|script|función|implementa)\b',
            r'\b(debugging|error|compilar|ejecutar)\b'
        ],
        RequestType.INSTRUCTIONAL: [
            r'\b(cómo|paso a paso|tutorial|guía|instrucciones)\b',
            r'\b(enseña|muestra cómo|ayúdame a)\b'
        ],
        RequestType.SENSITIVE: [
            r'\b(médico|legal|financiero|personal|confidencial)\b',
            r'\b(salud|enfermedad|síntoma|diagnóstico)\b'
        ]
    }
    scores = {}
    for req_type, patterns_list in patterns.items():
        score = 0
        for pattern in patterns_list:
            if re.search(pattern, prompt_lower):
                score += 1
        scores[req_type] = score
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return RequestType.CONVERSATIONAL

# =========================
# 5. DETECCIÓN DE AMBIGÜEDAD
# =========================

def detect_ambiguity(prompt: str) -> float:
    ambiguity_score = 0.0
    factors = 0
    words = prompt.split()
    if len(words) < 5:
        ambiguity_score += 0.3
    factors += 1
    vague_pronouns = ['esto', 'eso', 'aquello', 'algo', 'ello']
    vague_count = sum(1 for word in words if word.lower() in vague_pronouns)
    if vague_count > 0:
        ambiguity_score += min(0.2 * vague_count, 0.4)
    factors += 1
    action_verbs = ['crear', 'analizar', 'explicar', 'generar', 'calcular', 'mostrar']
    has_action = any(verb in prompt.lower() for verb in action_verbs)
    if not has_action:
        ambiguity_score += 0.2
    factors += 1
    if '?' in prompt and len(words) < 8:
        ambiguity_score += 0.15
    factors += 1
    return min(ambiguity_score / factors, 1.0)

# =========================
# 6. CÁLCULO DE COMPLEJIDAD
# =========================

def calculate_complexity(prompt: str) -> float:
    complexity_score = 0.0
    words = prompt.split()
    word_count = len(words)
    if word_count > 50:
        complexity_score += 0.3
    elif word_count > 20:
        complexity_score += 0.2
    elif word_count > 10:
        complexity_score += 0.1
    multi_req_indicators = [' y ', ', ', 'además', 'también', 'luego', 'después']
    req_count = sum(indicator in prompt.lower() for indicator in multi_req_indicators)
    complexity_score += min(req_count * 0.1, 0.3)
    technical_indicators = ['API', 'algoritmo', 'función', 'implementación', 'optimizar']
    tech_count = sum(1 for term in technical_indicators if term.lower() in prompt.lower())
    complexity_score += min(tech_count * 0.08, 0.2)
    conditional_words = ['si', 'cuando', 'solo si', 'excepto', 'salvo', 'pero']
    cond_count = sum(1 for word in conditional_words if word in prompt.lower())
    complexity_score += min(cond_count * 0.1, 0.2)
    return min(complexity_score, 1.0)

# =========================
# 7. FUNCIONES AUXILIARES
# =========================

def _normalize_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def _extract_core_goal(prompt: str, req_type: RequestType) -> str:
    words = prompt.split()
    action_verbs = ['crear', 'analizar', 'explicar', 'generar', 'calcular', 
                    'mostrar', 'diseñar', 'escribir', 'desarrollar', 'implementar']
    for i, word in enumerate(words):
        if any(verb in word.lower() for verb in action_verbs):
            goal_words = words[i:min(i+5, len(words))]
            return ' '.join(goal_words)
    return ' '.join(words[:min(7, len(words))])

def _extract_key_entities(prompt: str) -> List[str]:
    stopwords = {'el', 'la', 'los', 'las', 'un', 'una', 'de', 'en', 'y', 'a', 
                 'para', 'por', 'con', 'que', 'se', 'es', 'su', 'del'}
    words = re.findall(r'\b\w+\b', prompt.lower())
    entities = [w for w in words if w not in stopwords and len(w) > 3]
    from collections import Counter
    return [entity for entity, _ in Counter(entities).most_common(5)]

def _semantic_similarity(text1: str, text2: str) -> float:
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union) if union else 0.0
