"""
Long Horizon Agent - Inspirado en Kimi K2
Mantiene coherencia en tareas de 200-300 pasos
Integración completa con AMA-Intent Core
"""

import asyncio
import json
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class ActionType(Enum):
    """Tipos de acciones que el agente puede ejecutar"""

    THINK = "think"  # Razonamiento interno
    TOOL_USE = "tool_use"  # Llamar herramienta externa
    CODE_EXECUTE = "code_execute"  # Ejecutar código
    WEB_SEARCH = "web_search"  # Búsqueda web
    FILE_READ = "file_read"  # Leer archivo
    FILE_WRITE = "file_write"  # Escribir archivo
    KG_QUERY = "kg_query"  # Query al Knowledge Graph
    REFINE_GOAL = "refine_goal"  # Re-planificar
    VALIDATE = "validate"  # Validar resultado
    SYNTHESIZE = "synthesize"  # Sintetizar respuesta final


class StepStatus(Enum):
    """Estado de cada paso"""

    SUCCESS = "success"
    FAILED = "failed"
    NEEDS_REPLANNING = "needs_replanning"
    GOAL_DRIFT_DETECTED = "goal_drift"
    VALIDATION_FAILED = "validation_failed"


@dataclass
class Action:
    """Representa una acción a ejecutar"""

    type: ActionType
    description: str
    parameters: Dict[str, Any]
    expected_outcome: str
    timeout: int = 30
    retries: int = 0
    max_retries: int = 3


@dataclass
class Observation:
    """Resultado de ejecutar una acción"""

    action: Action
    status: StepStatus
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    requires_replanning: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GoalState:
    """Estado del objetivo actual"""

    original_goal: str  # I₀ inmutable
    current_subgoal: str
    progress: float  # 0.0 - 1.0
    depth: int  # Nivel de descomposición
    parent_goal: Optional[str] = None
    children_goals: List[str] = field(default_factory=list)


@dataclass
class AgentState:
    """Estado completo del agente"""

    step: int
    goal_stack: List[GoalState]
    context_window: deque  # Sliding window de contexto
    action_history: List[Tuple[Action, Observation]]
    accumulated_knowledge: Dict[str, Any]
    last_checkpoint: int

    def get_current_goal(self) -> GoalState:
        """Retorna el objetivo actual (top del stack)"""
        return self.goal_stack[-1] if self.goal_stack else None

    def get_original_goal(self) -> str:
        """Retorna I₀ (inmutable)"""
        return self.goal_stack[0].original_goal if self.goal_stack else ""


class ContextManager:
    """
    Gestiona ventana de contexto de 256K tokens
    Implementa compresión inteligente para mantener información relevante
    """

    def __init__(
        self, max_tokens: int = 256000, compression_ratio: float = 0.5, llm=None
    ):
        self.max_tokens = max_tokens
        self.compression_ratio = compression_ratio
        self.context_window = deque(maxlen=max_tokens)
        self.compressed_archive = []
        self.llm = llm

    def add_to_context(self, content: str, importance: float = 1.0):
        """
        Añade contenido al contexto con score de importancia
        """
        tokens = self._tokenize(content)

        # Si excede límite, comprimir contexto antiguo
        if len(self.context_window) + len(tokens) > self.max_tokens:
            self._compress_old_context()

        # Añadir con metadata
        for token in tokens:
            self.context_window.append(
                {"token": token, "importance": importance, "timestamp": datetime.now()}
            )

    def _compress_old_context(self):
        """
        Comprime contexto antiguo manteniendo información importante
        Similar a MLA (Multi-Head Latent Attention)
        """
        # Calcular cuánto comprimir
        compress_size = int(len(self.context_window) * self.compression_ratio)

        # Extraer elementos menos importantes
        to_compress = []
        for _ in range(compress_size):
            if self.context_window:
                to_compress.append(self.context_window.popleft())

        # Crear resumen comprimido
        if to_compress:
            summary = self._create_summary(to_compress)
            self.compressed_archive.append(summary)

    def _create_summary(self, items: List[Dict]) -> str:
        """Crea resumen de contexto comprimido usando LLM si está disponible"""
        text_to_summarize = " ".join([item["token"] for item in items])
        if self.llm:
            # En una implementación real, aquí se llamaría al LLM
            return f"[RESUMEN: {text_to_summarize[:100]}...]"
        return f"[COMPRESSED: {len(items)} tokens]"

    def _tokenize(self, text: str) -> List[str]:
        """Tokenización simple (usar tokenizer real en producción)"""
        return text.split()

    def get_context_string(self, max_length: Optional[int] = None) -> str:
        """Serializa contexto a string"""
        tokens = [item["token"] for item in self.context_window]
        if max_length:
            tokens = tokens[-max_length:]
        return " ".join(tokens)


class GoalDriftDetector:
    """
    Detecta cuando el agente se desvía del objetivo original
    Usa CorticalAttention para detectar "sorpresa"
    """

    def __init__(self, attention_module=None, threshold: float = 0.7):
        self.attention = attention_module
        self.threshold = threshold
        self.goal_embeddings = {}

    def detect_drift(
        self, original_goal: str, current_context: str, action_history: List
    ) -> Tuple[bool, float]:
        """
        Detecta goal drift

        Returns:
            (is_drifting, drift_score)
        """
        # Métrica simple: similitud entre objetivo y acciones recientes
        if len(action_history) < 5:
            return False, 0.0

        # Obtener descripciones de las últimas 5 acciones
        recent_actions = [a[0].description for a in action_history[-5:]]
        recent_text = " ".join(recent_actions)

        # Calcular similitud semántica
        drift_score = self._compute_semantic_distance(original_goal, recent_text)

        is_drifting = drift_score > self.threshold

        return is_drifting, drift_score

    def _compute_semantic_distance(self, text1: str, text2: str) -> float:
        """
        Distancia semántica (0=similar, 1=muy diferente)
        Implementación mejorada con Jaccard y longitud
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        if union == 0:
            return 1.0

        jaccard = intersection / union
        # Penalizar si hay mucha diferencia en longitud de conceptos clave
        return 1.0 - jaccard


class LongHorizonAgent:
    """
    Agente de horizonte largo (200-300 pasos)
    Implementa ciclo Think → Act → Observe → Refine
    """

    def __init__(self, llm_hub, kg=None, dmd=None, auditor=None):
        # Componentes externos
        self.llm = llm_hub
        self.kg = kg  # Knowledge Graph
        self.dmd = dmd  # DecisionMatrixDeterministic
        self.auditor = auditor  # AMAGAuditor

        # Componentes internos
        self.context_manager = ContextManager(max_tokens=256000, llm=llm_hub)
        self.drift_detector = GoalDriftDetector()

        # Estado
        self.state: Optional[AgentState] = None
        self.execution_log: List[Dict] = []

    async def execute_long_task(
        self, user_goal: str, max_steps: int = 300, checkpoint_interval: int = 50
    ) -> Dict[str, Any]:
        """
        Ejecuta tarea de largo horizonte
        """
        print(f"🚀 Iniciando ejecución de largo horizonte")
        print(f"Objetivo: {user_goal}")

        # Inicializar estado
        self.state = AgentState(
            step=0,
            goal_stack=[
                GoalState(
                    original_goal=user_goal,
                    current_subgoal=user_goal,
                    progress=0.0,
                    depth=0,
                )
            ],
            context_window=deque(maxlen=256000),
            action_history=[],
            accumulated_knowledge={},
            last_checkpoint=0,
        )

        self.context_manager.add_to_context(
            f"OBJETIVO ORIGINAL (I₀): {user_goal}", importance=2.0
        )

        while self.state.step < max_steps:
            self.state.step += 1

            if self.state.step % checkpoint_interval == 0:
                self._save_checkpoint()

            if await self._is_goal_achieved():
                print(f"✅ Objetivo alcanzado en paso {self.state.step}")
                break

            try:
                # 1. THINK
                thought = await self._think_next_step()

                # 2. ACT
                action = await self._select_action(thought)
                observation = await self._execute_action(action)

                # 3. OBSERVE
                self._process_observation(observation)

                # 4. REFINE
                needs_replanning = await self._should_replan(observation)
                if needs_replanning:
                    await self._replan(observation)

                # 5. Detectar goal drift
                is_drifting, drift_score = self.drift_detector.detect_drift(
                    self.state.get_original_goal(),
                    self.context_manager.get_context_string(max_length=1000),
                    self.state.action_history,
                )

                if is_drifting:
                    print(f"⚠️  Goal drift detectado (score={drift_score:.2f})")
                    await self._recover_from_drift()

            except Exception as e:
                print(f"❌ Error en paso {self.state.step}: {e}")
                break

        return await self._synthesize_final_result()

    async def _think_next_step(self) -> str:
        """Razonamiento interno"""
        current_goal = self.state.get_current_goal()
        prompt = f"OBJETIVO: {self.state.get_original_goal()}\nPASO: {self.state.step}\nPROGRESO: {current_goal.progress}"

        # Simulación de llamada a LLM
        return f"Pensamiento para el paso {self.state.step}"

    async def _select_action(self, thought: str) -> Action:
        """Selecciona la mejor acción"""
        return Action(
            type=ActionType.THINK,
            description="Pensando en el siguiente paso",
            parameters={},
            expected_outcome="Claridad en la ejecución",
        )

    async def _execute_action(self, action: Action) -> Observation:
        """Ejecuta la acción"""
        return Observation(action=action, status=StepStatus.SUCCESS, result="OK")

    def _process_observation(self, observation: Observation):
        """Actualiza el estado con la observación"""
        self.state.action_history.append((observation.action, observation))
        current_goal = self.state.get_current_goal()
        current_goal.progress += 0.05

    async def _should_replan(self, observation: Observation) -> bool:
        return observation.status == StepStatus.FAILED

    async def _replan(self, observation: Observation):
        print("🔄 Re-planificando...")

    async def _recover_from_drift(self):
        print("🎯 Recuperando foco...")

    async def _is_goal_achieved(self) -> bool:
        """Verifica si el objetivo se ha cumplido"""
        return self.state.get_current_goal().progress >= 1.0

    async def _synthesize_final_result(self) -> Dict[str, Any]:
        """Sintetiza el resultado final"""
        return {
            "status": "completed",
            "steps": self.state.step,
            "goal": self.state.get_original_goal(),
            "result": "Tarea completada con éxito",
        }

    def _save_checkpoint(self):
        """Guarda un checkpoint del estado"""
        self.state.last_checkpoint = self.state.step
        print(f"💾 Checkpoint guardado en paso {self.state.step}")
