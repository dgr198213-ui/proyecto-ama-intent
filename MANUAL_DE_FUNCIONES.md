# 📘 Manual Completo de Funciones

## Cerebro Artificial - Documentación Técnica Detallada

---

## Índice

1. [Módulo AMA-Intent](#ama-intent)
2. [FASE 1: Sistema Perceptivo-Decisional](#fase-1)
3. [FASE 2: Sistema de Memoria](#fase-2)
4. [FASE 3: Sistema de Aprendizaje](#fase-3)
5. [Integración y Interfaces](#integracion)
6. [Ejemplos de Uso](#ejemplos)

---

## 1. AMA-Intent - Detector de Intención {#ama-intent}

### 📄 Archivo: `ama_intent.py`

### Clases

#### `Intent`
**Propósito**: Representación inmutable de la intención del usuario (I₀)

**Atributos**:
- `raw_text: str` - Texto original
- `intent_hash: str` - Hash SHA-256 de la intención
- `request_type: RequestType` - Tipo de solicitud
- `core_goal: str` - Objetivo central extraído
- `key_entities: List[str]` - Entidades clave
- `ambiguity_score: float` - Nivel de ambigüedad [0,1]
- `complexity_score: float` - Nivel de complejidad [0,1]
- `timestamp: str` - Marca temporal

**Métodos**:
```python
def __eq__(self, other: Intent) -> bool
    """Compara dos intenciones por hash"""
```

---

### Funciones Principales

#### `extract_intent(prompt: str, timestamp: Optional[str] = None) -> Intent`

**Propósito**: Extrae y cristaliza la intención original I₀

**Parámetros**:
- `prompt`: Texto del usuario
- `timestamp`: Marca temporal (opcional)

**Retorna**: Objeto `Intent` inmutable

**Ejemplo**:
```python
from ama_intent import extract_intent

text = "Explícame cómo funciona la fotosíntesis"
I0 = extract_intent(text)

print(I0.request_type)      # RequestType.INFORMATIONAL
print(I0.ambiguity_score)   # 0.15 (bajo)
print(I0.complexity_score)  # 0.45 (medio)
```

---

#### `validate_intent_immutability(I0: Intent, I_current: Intent) -> bool`

**Propósito**: Verifica que la intención no haya sido alterada

**Parámetros**:
- `I0`: Intención original
- `I_current`: Intención actual a validar

**Retorna**: `True` si I_current ≡ I₀

**Ejemplo**:
```python
I0 = extract_intent("Explica la gravedad")
I_response = extract_intent("La gravedad es una fuerza...")

is_preserved = validate_intent_immutability(I0, I_response)
# True si la respuesta mantiene la intención
```

---

#### `classify_request_type(prompt: str) -> RequestType`

**Propósito**: Clasifica el tipo de solicitud

**Tipos**:
- `INFORMATIONAL`: Preguntas sobre hechos
- `ANALYTICAL`: Comparaciones, análisis
- `CREATIVE`: Generación de contenido
- `TECHNICAL`: Código, implementaciones
- `CONVERSATIONAL`: Chat casual
- `INSTRUCTIONAL`: Cómo hacer algo
- `SENSITIVE`: Temas médicos, legales

**Ejemplo**:
```python
type1 = classify_request_type("¿Qué es Python?")
# RequestType.INFORMATIONAL

type2 = classify_request_type("Escribe un poema")
# RequestType.CREATIVE

type3 = classify_request_type("Cómo hacer pan")
# RequestType.INSTRUCTIONAL
```

---

#### `detect_ambiguity(prompt: str) -> float`

**Propósito**: Calcula score de ambigüedad

**Factores evaluados**:
1. Longitud del prompt
2. Pronombres vagos ("esto", "eso")
3. Falta de verbos de acción
4. Preguntas sin contexto

**Retorna**: Score [0,1] donde 0=claro, 1=muy ambiguo

**Ejemplo**:
```python
ambiguity1 = detect_ambiguity("Explica la teoría de la relatividad de Einstein")
# ~0.15 (bajo)

ambiguity2 = detect_ambiguity("Dime sobre eso")
# ~0.85 (alto)
```

---

#### `calculate_complexity(prompt: str) -> float`

**Propósito**: Calcula complejidad de la solicitud

**Factores evaluados**:
1. Longitud del texto
2. Múltiples requisitos
3. Términos técnicos
4. Condiciones y restricciones

**Retorna**: Score [0,1] donde 0=simple, 1=muy complejo

**Ejemplo**:
```python
complexity1 = calculate_complexity("¿Qué hora es?")
# ~0.05 (muy simple)

complexity2 = calculate_complexity(
    "Implementa un algoritmo de ML que optimice X bajo restricción Y, 
     considerando Z y validando con métricas A, B y C"
)
# ~0.95 (muy complejo)
```

---

## 2. FASE 1: Sistema Perceptivo-Decisional {#fase-1}

### 2.1 Sensing - Filtro Kalman

#### 📄 Archivo: `sensing/kalman.py`

#### Clase `ThalamicFilter`

**Propósito**: Filtro de Kalman para estabilizar observaciones (simula tálamo)

**Constructor**:
```python
def __init__(self, 
             dim_state: int, 
             dim_obs: int,
             process_noise: float = 0.01,
             measurement_noise: float = 0.1)
```

**Parámetros**:
- `dim_state`: Dimensión del estado latente
- `dim_obs`: Dimensión de la observación
- `process_noise`: Ruido del proceso (Q)
- `measurement_noise`: Ruido de medición (R)

---

#### `filter(y: np.ndarray) -> Tuple[np.ndarray, Dict]`

**Propósito**: Filtra observación ruidosa

**Ecuaciones**:
```
Predicción:
  x̂⁻ₜ = F·x̂ₜ₋₁
  P⁻ₜ = F·Pₜ₋₁·Fᵀ + Q

Actualización:
  Kₜ = P⁻ₜ·Hᵀ·(H·P⁻ₜ·Hᵀ + R)⁻¹
  x̂ₜ = x̂⁻ₜ + Kₜ·(yₜ - H·x̂⁻ₜ)
  Pₜ = (I - Kₜ·H)·P⁻ₜ
```

**Retorna**: 
- `y_filtered`: Observación filtrada
- `metrics`: Métricas del filtro

**Ejemplo**:
```python
from sensing.kalman import ThalamicFilter

thalamus = ThalamicFilter(dim_state=64, dim_obs=384)

# Observación ruidosa (embedding)
observation = np.random.randn(384) * 0.5

# Filtrar
y_filtered, metrics = thalamus.filter(observation)

print(metrics['uncertainty'])    # Incertidumbre
print(metrics['innovation_norm'])  # Innovación
```

---

### 2.2 Cortex - Atención

#### 📄 Archivo: `cortex/attention.py`

#### Clase `CorticalAttention`

**Propósito**: Mecanismo de atención basado en LSI (Índice de Sensibilidad Local)

**Constructor**:
```python
def __init__(self, 
             dim: int,
             lambda_init: float = 1.0,
             history_size: int = 100)
```

---

#### `compute_attention(delta: np.ndarray, modulation: Optional[np.ndarray] = None) -> Tuple[np.ndarray, Dict]`

**Propósito**: Calcula vector de atención basado en sorpresa

**Ecuación**:
```
LSI(δₜ) = |δₜ| / max(|δₜ|)  (normalizado)
αₜ = softmax(λ·LSI(δₜ))
```

**Parámetros**:
- `delta`: Error de predicción (sorpresa)
- `modulation`: Modulación externa opcional

**Retorna**:
- `alpha`: Vector de atención [0,1]
- `metrics`: Métricas de atención

**Ejemplo**:
```python
from cortex.attention import CorticalAttention

attention = CorticalAttention(dim=384)

# Error de predicción
delta = y_filtered - y_predicted

# Calcular atención
alpha, metrics = attention.compute_attention(delta)

print(metrics['attention_entropy'])  # Entropía del foco
print(metrics['focus_index'])        # Índice de concentración
```

---

#### `apply_attention(x: np.ndarray, mode: str = 'modulate') -> np.ndarray`

**Propósito**: Aplica atención a una entrada

**Modos**:
- `'modulate'`: α ⊙ x
- `'gate'`: mask · x
- `'soft'`: α^γ ⊙ x

**Ejemplo**:
```python
# Modular entrada por atención
x_attended = attention.apply_attention(x_input, mode='modulate')
```

---

### 2.3 Cortex - Estado Latente

#### 📄 Archivo: `cortex/state.py`

#### Clase `CorticalState`

**Propósito**: Mantiene y actualiza estado latente cortical z

**Constructor**:
```python
def __init__(self, config: CorticalStateConfig)
```

---

#### `update(y_hat: np.ndarray, alpha: np.ndarray, w: Optional[np.ndarray] = None) -> Tuple[np.ndarray, Dict]`

**Propósito**: Actualiza estado cortical

**Ecuación**:
```
eₜ = φ(ŷₜ)                    # Codificación
zₜ = f(zₜ₋₁, αₜ⊙eₜ, wₜ₋₁)    # Actualización recurrente
```

**Parámetros**:
- `y_hat`: Observación filtrada
- `alpha`: Vector de atención
- `w`: Memoria de trabajo (opcional)

**Retorna**:
- `z_new`: Nuevo estado latente
- `metrics`: Métricas de actualización

**Ejemplo**:
```python
from cortex.state import create_cortical_state

cortex = create_cortical_state(
    dim_latent=128,
    dim_input=384,
    dim_wm=64
)

z_new, metrics = cortex.update(y_filtered, alpha, w)

print(metrics['z_norm'])      # Norma del estado
print(metrics['z_change'])    # Cambio respecto anterior
print(metrics['sparsity'])    # Sparsity del estado
```

---

#### `predict_next_observation(a: Optional[np.ndarray] = None) -> np.ndarray`

**Propósito**: Predice siguiente observación (modelo del mundo)

**Ecuación**:
```
ỹₜ = g(zₜ₋₁, aₜ₋₁)
```

**Ejemplo**:
```python
y_predicted = cortex.predict_next_observation()

# Calcular sorpresa
delta, surprise = cortex.compute_surprise(y_actual, y_predicted)
```

---

### 2.4 Decision - Q-Value

#### 📄 Archivo: `decision/q_value.py`

#### Clase `QValueEstimator`

**Propósito**: Estima valor Q de acciones con MIEM integrado

**Constructor**:
```python
def __init__(self,
             dim_state: int,
             dim_action: int,
             gamma: float = 0.95,
             risk_aversion: float = 0.5)
```

---

#### `compute_Q(z: np.ndarray, a: np.ndarray, metadata: Optional[Dict] = None, ...) -> Tuple[float, Dict]`

**Propósito**: Calcula valor Q con MIEM

**Ecuación**:
```
Q(z,a) = 𝔼[R|z,a] - Coste(a) - ρ·Riesgo(MIEM)

MIEM = (eficiencia, impacto, modularidad, riesgo)
```

**Parámetros**:
- `z`: Estado actual
- `a`: Acción candidata
- `metadata`: Metadatos (complejidad, recursos)
- `environment`: Info del entorno
- `reward_model`: Modelo de recompensa externo

**Retorna**:
- `Q_value`: Valor Q total
- `components`: Desglose de componentes

**Ejemplo**:
```python
from decision.q_value import QValueEstimator

q_est = QValueEstimator(dim_state=128, dim_action=32)

# Evaluar acción
Q_val, components = q_est.compute_Q(
    z=current_state,
    a=action_candidate,
    metadata={'complexity': 0.5}
)

print(f"Q-value: {Q_val:.3f}")
print(f"Reward: {components['reward']:.3f}")
print(f"Cost: {components['cost']:.3f}")
print(f"Risk: {components['miem_risk']:.3f}")
```

---

### 2.5 Decision - DMD

#### 📄 Archivo: `decision/dmd.py`

#### Clase `DecisionMatrixDeterministic`

**Propósito**: Selector de acciones multi-criterio

**Constructor**:
```python
def __init__(self, criteria: Optional[DecisionCriteria] = None)
```

---

#### `decide(action_candidates: List[Dict], constraints: Optional[List[Constraint]] = None, ...) -> DMDResult`

**Propósito**: Selecciona mejor acción

**Algoritmo**:
```
1. Filtrar por restricciones HARD
2. Construir matriz de criterios
3. Aplicar ponderaciones
4. Aplicar penalizaciones SOFT
5. Seleccionar máximo score
```

**Parámetros**:
- `action_candidates`: Lista de candidatos
- `constraints`: Restricciones
- `criteria_override`: Criterios alternativos

**Retorna**: `DMDResult` con acción seleccionada

**Ejemplo**:
```python
from decision.dmd import DecisionMatrixDeterministic, DecisionCriteria

dmd = DecisionMatrixDeterministic(
    criteria=DecisionCriteria(
        Q_value=1.0,
        efficiency=0.4,
        safety=0.6,
        modularity=0.2
    )
)

result = dmd.decide(
    action_candidates=candidates,
    constraints=[safety_constraint]
)

print(f"Selected: {result.selected_action_id}")
print(f"Score: {result.score:.3f}")
```

---

### 2.6 Governance - AMA-G

#### 📄 Archivo: `governance/amag_audit.py`

#### Clase `AMAGAuditor`

**Propósito**: Auditoría y gobernanza (PFC metacognitivo)

**Constructor**:
```python
def __init__(self, thresholds: Optional[GovernanceThresholds] = None)
```

---

#### `audit(z: np.ndarray, w: Optional[np.ndarray], R: Optional[List], action_candidate: Dict, surprise: float, ...) -> AuditReport`

**Propósito**: Audita sistema completo

**Verificaciones**:
1. Sorpresa excesiva
2. Incertidumbre alta
3. Riesgo elevado
4. Consistencia interna
5. Magnitud de acción

**Ecuación de confianza**:
```
confidence = 0.3·(1-surprise_norm) + 0.3·safety + 
             0.3·consistency + 0.1·magnitude_ok
```

**Retorna**: `AuditReport` con resultado y recomendaciones

**Ejemplo**:
```python
from governance.amag_audit import AMAGAuditor, GovernanceThresholds

auditor = AMAGAuditor(
    thresholds=GovernanceThresholds(
        min_confidence=0.5,
        max_surprise=3.0,
        max_risk=0.7
    )
)

report = auditor.audit(
    z=state,
    w=working_memory,
    R=episodes,
    action_candidate=selected_action,
    surprise=surprise_value
)

if report.result == AuditResult.PASS:
    execute(report.selected_action)
elif report.result == AuditResult.REVISED:
    execute(report.revised_action)
else:
    execute(report.safe_action)
```

---

## 3. FASE 2: Sistema de Memoria {#fase-2}

### 3.1 Memoria Episódica

#### 📄 Archivo: `memory/episodic_graph.py`

#### Clase `EpisodicMemoryGraph`

**Propósito**: Memoria episódica como grafo con PageRank

**Constructor**:
```python
def __init__(self, 
             max_episodes: int = 10000,
             similarity_threshold: float = 0.7)
```

---

#### `add_episode(state: np.ndarray, context: Dict, tags: Optional[Set[str]] = None, ...) -> str`

**Propósito**: Añade episodio a memoria

**Conexiones creadas**:
- Temporal (episodios consecutivos)
- Similaridad (estados similares)
- Causal (mismo tag/contexto)

**Retorna**: ID del episodio

**Ejemplo**:
```python
from memory.episodic_graph import EpisodicMemoryGraph

memory = EpisodicMemoryGraph(max_episodes=5000)

episode_id = memory.add_episode(
    state=z_current,
    context={'action': 'explore', 'reward': 0.8},
    tags={'navigation', 'success'},
    importance=0.9
)
```

---

#### `retrieve(query_state: np.ndarray, top_k: int = 5, use_pagerank: bool = True, ...) -> List[Tuple]`

**Propósito**: Recupera episodios relevantes

**Score compuesto**:
```
Score(v) = w_sim·sim(z,v) + w_pr·PageRank(v) + 
           w_lfpi·LFPI(v) + w_lsi·LSI(v)
```

**Retorna**: Lista de (episode_id, score, episode)

**Ejemplo**:
```python
# Recuperar 5 episodios más relevantes
results = memory.retrieve(
    query_state=current_state,
    top_k=5,
    use_pagerank=True
)

for ep_id, score, episode in results:
    print(f"{ep_id}: score={score:.3f}")
    print(f"  Context: {episode.context}")
```

---

#### `compute_pagerank(damping: float = 0.85, ...) -> Dict[str, float]`

**Propósito**: Calcula PageRank para episodios

**Ecuación**:
```
PR(v) = (1-d)/N + d·Σ PR(u)/|Out(u)|
```

**Retorna**: Dict de scores por episodio

---

### 3.2 Memoria Semántica

#### 📄 Archivo: `memory/semantic_matrix.py`

#### Clase `SemanticMemoryMatrix`

**Propósito**: Memoria semántica (conceptos abstractos)

**Constructor**:
```python
def __init__(self,
             dim_state: int,
             max_concepts: int = 1000,
             learning_rate: float = 0.01,
             compression_dim: Optional[int] = None)
```

---

#### `consolidate(state: np.ndarray, tags: Optional[List[str]] = None, threshold: float = 0.8) -> Tuple[int, bool]`

**Propósito**: Consolida estado en memoria

**Estrategia**:
```
Si existe concepto similar → actualizar prototipo
Si no existe → crear nuevo concepto
```

**Actualización**:
```
nuevo_prototipo = (1-α)·viejo + α·nuevo
```

**Retorna**: (concept_id, is_new)

**Ejemplo**:
```python
from memory.semantic_matrix import SemanticMemoryMatrix

semantic = SemanticMemoryMatrix(
    dim_state=128,
    max_concepts=500,
    learning_rate=0.05
)

concept_id, is_new = semantic.consolidate(
    state=z_current,
    tags=['mathematics', 'algebra'],
    threshold=0.8
)

if is_new:
    print(f"Nuevo concepto creado: {concept_id}")
else:
    print(f"Concepto actualizado: {concept_id}")
```

---

#### `retrieve(query: np.ndarray, top_k: int = 5, min_similarity: float = 0.5) -> List[Tuple]`

**Propósito**: Recupera conceptos relevantes

**Retorna**: Lista de (concept_id, similarity, concept)

---

#### `merge_similar_concepts(threshold: float = 0.95)`

**Propósito**: Fusiona conceptos muy similares

**Ejemplo**:
```python
# Fusionar conceptos con similaridad > 0.95
semantic.merge_similar_concepts(threshold=0.95)
```

---

### 3.3 Working Memory

#### 📄 Archivo: `memory/working_memory.py`

#### Clase `WorkingMemory`

**Propósito**: Memoria de trabajo con gating (PFC)

**Constructor**:
```python
def __init__(self, 
             dim: int,
             config: Optional[WorkingMemoryConfig] = None)
```

---

#### `update(z: np.ndarray, retrieved_episodes: Optional[List] = None, ...) -> Tuple[np.ndarray, Dict]`

**Propósito**: Actualiza working memory con gating

**Ecuación**:
```
gate = σ(Γ[zₜ, wₜ₋₁])
wₜ = gate⊙wₜ₋₁ + (1-gate)⊙new_content
```

**Parámetros**:
- `z`: Estado cortical
- `retrieved_episodes`: Episodios recuperados
- `task_relevance`: Relevancia de tarea

**Retorna**: (w_new, metrics)

**Ejemplo**:
```python
from memory.working_memory import WorkingMemory

wm = WorkingMemory(dim=64)

w_new, metrics = wm.update(
    z=current_state,
    retrieved_episodes=episodes
)

print(f"Active slots: {metrics['active_slots']}")
print(f"Gate mean: {metrics['gate_mean']:.3f}")
```

---

#### `rehearse(iterations: int = 5, strength: float = 0.9)`

**Propósito**: Rehearsal para mantener información

**Ejemplo**:
```python
# Reforzar contenido actual
wm.rehearse(iterations=5)
```

---

### 3.4 Sistema de Poda

#### 📄 Archivo: `memory/pruning.py`

#### Clase `AdaptivePruningSystem`

**Propósito**: Olvido selectivo adaptativo

**Constructor**:
```python
def __init__(self, config: Optional[PruningConfig] = None)
```

---

#### `select_candidates(items: List[MemoryItem], n_to_prune: Optional[int] = None) -> List[str]`

**Propósito**: Selecciona items a podar

**Criterios**:
```
Score = w_recency·(1-recency) + 
        w_frequency·frequency + 
        w_impact·impact
```

**Poda si**:
```
uso(x) < u_min ∧ impacto(x) < ι_min
```

**Retorna**: Lista de IDs a podar

**Ejemplo**:
```python
from memory.pruning import AdaptivePruningSystem

pruner = AdaptivePruningSystem()

# Ejecutar poda
prune_stats = pruner.execute_pruning(
    episodic_memory,
    semantic_memory,
    force=False
)

print(f"Items podados: {prune_stats['pruned_count']}")
```

---

## 4. FASE 3: Sistema de Aprendizaje {#fase-3}

### 4.1 Control PID Homeostático

#### 📄 Archivo: `control/pid_homeostasis.py`

#### Clase `HomeostaticSystem`

**Propósito**: Control homeostático multi-PID (cerebelo)

**Constructor**:
```python
def __init__(self)
```

**Controladores**:
1. **Exploración τ**: Balance exploración-explotación
2. **Learning rate η**: Velocidad de aprendizaje
3. **Atención λ**: Concentración del foco
4. **Gating**: Umbral de actualización WM
5. **Risk aversion ρ**: Tolerancia al riesgo

---

#### `update_all(surprise: float, stability: float, attention_focus: float, wm_load: float, performance: float) -> Dict`

**Propósito**: Actualiza todos los controladores

**Ecuación PID**:
```
u(t) = Kp·e(t) + Ki·∫e(τ)dτ + Kd·de(t)/dt
```

**Retorna**: Dict con parámetros actualizados

**Ejemplo**:
```python
from control.pid_homeostasis import HomeostaticSystem

homeostasis = HomeostaticSystem()

params = homeostasis.update_all(
    surprise=1.2,
    stability=0.7,
    attention_focus=0.6,
    wm_load=0.5,
    performance=0.75
)

# Aplicar parámetros
exploration_tau = params[ControlledParameter.EXPLORATION]
learning_rate = params[ControlledParameter.LEARNING_RATE]
```

---

#### `adapt_to_context(context: str)`

**Propósito**: Adapta setpoints según contexto

**Contextos**:
- `'learning'`: Alta exploración, alta LR
- `'exploitation'`: Baja exploración, baja LR
- `'exploration'`: Máxima exploración
- `'emergency'`: Modo seguro

**Ejemplo**:
```python
# Cambiar a modo aprendizaje
homeostasis.adapt_to_context('learning')
```

---

### 4.2 Función de Pérdida

#### 📄 Archivo: `learning/loss.py`

#### Clase `CompositeLoss`

**Propósito**: Función de pérdida compuesta

**Constructor**:
```python
def __init__(self, weights: Optional[LossWeights] = None)
```

---

#### `compute_total_loss(prediction_metrics: Dict, memory_metrics: Dict, policy_metrics: Dict, governance_metrics: Dict) -> Tuple[float, Dict]`

**Propósito**: Calcula pérdida total

**Ecuación**:
```
ℒₜ = w₁·ℒpred + w₂·ℒmem + w₃·ℒpol + w₄·ℒgov
```

**Componentes**:
- **ℒpred**: Error de predicción
- **ℒmem**: Pérdida de memoria
- **ℒpol**: Pérdida de política
- **ℒgov**: Pérdida de gobernanza

**Retorna**: (total_loss, components)

**Ejemplo**:
```python
from learning.loss import CompositeLoss

loss_fn = CompositeLoss()

total_loss, components = loss_fn.compute_total_loss(
    prediction_metrics={'y_predicted': y_pred, 'y_actual': y_act},
    memory_metrics={'retrieval_accuracy': 0.8, 'consolidation_rate': 0.95}
)
```

---

## 7. Conclusión Técnica

El sistema **AMA-Intent** representa una arquitectura de vanguardia en el campo de la IA biomimética. A través de la integración de componentes como el **Long Horizon Agent** y el optimizador **MuonClip**, el sistema no solo emula el razonamiento humano, sino que lo potencia con una estabilidad y eficiencia computacional superiores.

La modularidad del sistema, dividida en fases perceptivas, de memoria y de aprendizaje, permite una evolución continua del conocimiento (I₀) sin comprometer la integridad de la intención original del usuario. Esta documentación sirve como guía base para desarrolladores que deseen extender las capacidades del cerebro artificial o integrar nuevos motores de decisión.

---
**Fin del Manual de Funciones**
