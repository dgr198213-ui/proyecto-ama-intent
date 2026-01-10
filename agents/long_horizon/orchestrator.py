"""
Long Horizon Agent - Inspirado en Kimi K2
Mantiene coherencia en tareas de 200-300 pasos
Integración completa con AMA-Intent Core
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
from collections import deque
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
    
    def __init__(self, max_tokens: int = 256000, compression_ratio: float = 0.5):
        self.max_tokens = max_tokens
        self.compression_ratio = compression_ratio
        self.context_window = deque(maxlen=max_tokens)
        self.compressed_archive = []
    
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
            self.context_window.append({
                "token": token,
                "importance": importance,
                "timestamp": datetime.now()
            })
    
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
        
        # Crear resumen comprimido (simulado)
        if to_compress:
            summary = self._create_summary(to_compress)
            self.compressed_archive.append(summary)
    
    def _create_summary(self, items: List[Dict]) -> str:
        """Crea resumen de contexto comprimido"""
        # En implementación real, usar LLM para resumir
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
    
    def detect_drift(self, original_goal: str, 
                     current_context: str,
                     action_history: List) -> Tuple[bool, float]:
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
        
        # Calcular similitud simple (en producción, usar embeddings)
        drift_score = self._compute_semantic_distance(original_goal, recent_text)
        
        is_drifting = drift_score > self.threshold
        
        return is_drifting, drift_score
    
    def _compute_semantic_distance(self, text1: str, text2: str) -> float:
        """
        Distancia semántica (0=similar, 1=muy diferente)
        Implementación simplificada
        """
        # En producción: usar embeddings de LLM
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        if union == 0:
            return 1.0
        
        jaccard = intersection / union
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
        self.context_manager = ContextManager(max_tokens=256000)
        self.drift_detector = GoalDriftDetector()
        
        # Estado
        self.state: Optional[AgentState] = None
        self.execution_log: List[Dict] = []
    
    async def execute_long_task(self, user_goal: str, 
                               max_steps: int = 300,
                               checkpoint_interval: int = 50) -> Dict[str, Any]:
        """
        Ejecuta tarea de largo horizonte
        
        Args:
            user_goal: Objetivo del usuario (I₀ inmutable)
            max_steps: Máximo de pasos
            checkpoint_interval: Guardar checkpoint cada N pasos
            
        Returns:
            Resultado final con metadata
        """
        print(f"🚀 Iniciando ejecución de largo horizonte")
        print(f"Objetivo: {user_goal}")
        print(f"Max pasos: {max_steps}")
        
        # Inicializar estado
        self.state = AgentState(
            step=0,
            goal_stack=[GoalState(
                original_goal=user_goal,
                current_subgoal=user_goal,
                progress=0.0,
                depth=0
            )],
            context_window=deque(maxlen=256000),
            action_history=[],
            accumulated_knowledge={},
            last_checkpoint=0
        )
        
        # Añadir objetivo inicial al contexto
        self.context_manager.add_to_context(
            f"OBJETIVO ORIGINAL (I₀): {user_goal}",
            importance=2.0  # Alta importancia
        )
        
        # Ciclo principal: Think → Act → Observe → Refine
        while self.state.step < max_steps:
            self.state.step += 1
            
            # Checkpoint periódico
            if self.state.step % checkpoint_interval == 0:
                self._save_checkpoint()
            
            # Verificar si el objetivo ya se cumplió
            if await self._is_goal_achieved():
                print(f"✅ Objetivo alcanzado en paso {self.state.step}")
                break
            
            try:
                # 1. THINK: Razonar sobre próxima acción
                thought = await self._think_next_step()
                
                # 2. ACT: Seleccionar y ejecutar acción
                action = await self._select_action(thought)
                observation = await self._execute_action(action)
                
                # 3. OBSERVE: Procesar resultado
                self._process_observation(observation)
                
                # 4. REFINE: Ajustar plan si es necesario
                needs_replanning = await self._should_replan(observation)
                
                if needs_replanning:
                    await self._replan(observation)
                
                # 5. Detectar goal drift
                is_drifting, drift_score = self.drift_detector.detect_drift(
                    self.state.get_original_goal(),
                    self.context_manager.get_context_string(max_length=1000),
                    self.state.action_history
                )
                
                if is_drifting:
                    print(f"⚠️  Goal drift detectado (score={drift_score:.2f})")
                    await self._recover_from_drift()
                
                # 6. Validar con AMAGAuditor si está disponible
                if self.auditor:
                    validation = self._validate_with_auditor(action, observation)
                    if not validation["passed"]:
                        print(f"❌ Validación falló: {validation['reason']}")
                        break
                
                # Log de progreso
                if self.state.step % 10 == 0:
                    self._log_progress()
                
            except Exception as e:
                print(f"❌ Error en paso {self.state.step}: {e}")
                # Intentar recuperación
                if not await self._attempt_recovery(e):
                    break
        
        # Sintetizar resultado final
        final_result = await self._synthesize_final_result()
        
        return final_result
    
    async def _think_next_step(self) -> str:
        """
        THINK: Razonamiento interno sobre qué hacer
        Usa LLM con contexto completo
        """
        current_goal = self.state.get_current_goal()
        
        # Construir prompt con contexto
        prompt = f"""Eres un agente autónomo ejecutando una tarea compleja.

OBJETIVO ORIGINAL (I₀): {self.state.get_original_goal()}
SUBOBJETIVO ACTUAL: {current_goal.current_subgoal}
PASO: {self.state.step}
PROGRESO: {current_goal.progress*100:.1f}%

CONTEXTO RECIENTE:
{self.context_manager.get_context_string(max_length=5000)}

ÚLTIMAS 3 ACCIONES:
{self._format_recent_actions(3)}

Razona sobre cuál debe ser el siguiente paso. Considera:
1. ¿Estoy progresando hacia el objetivo?
2. ¿Necesito información adicional?
3. ¿Debo validar resultados previos?
4. ¿Es momento de sintetizar la respuesta final?

Responde con tu razonamiento en formato JSON:
{{
  "thought": "tu razonamiento aquí",
  "next_action_type": "tipo de acción",
  "confidence": 0.0-1.0
}}
"""
        
        # Query al LLM
        from llm_connector import AnalysisRequest
        
        request = AnalysisRequest(
            code="",
            file_path="agent_reasoning",
            task="explain",
            context=prompt,
            max_tokens=1000
        )
        
        response = await self.llm.analyze(request)
        
        if response.success:
            # Añadir pensamiento al contexto
            self.context_manager.add_to_context(
                f"PENSAMIENTO: {response.content}",
                importance=1.5
            )
            return response.content
        else:
            return "Error en razonamiento"
    
    async def _select_action(self, thought: str) -> Action:
        """
        Selecciona acción usando DMD si está disponible
        """
        # Parsear pensamiento para extraer acciones candidatas
        # (simplificado - en producción parsear JSON del LLM)
        
        # Acciones candidatas basadas en el contexto
        candidates = [
            Action(
                type=ActionType.TOOL_USE,
                description="Usar herramienta para obtener información",
                parameters={},
                expected_outcome="Información relevante obtenida"
            ),
            Action(
                type=ActionType.CODE_EXECUTE,
                description="Ejecutar código para procesar datos",
                parameters={},
                expected_outcome="Datos procesados correctamente"
            ),
            Action(
                type=ActionType.VALIDATE,
                description="Validar resultados obtenidos",
                parameters={},
                expected_outcome="Validación exitosa"
            )
        ]
        
        # Si hay DMD, usarlo para seleccionar
        if self.dmd:
            # Convertir a formato DMD
            action_candidates_dmd = [
                {
                    'action': f"action_{i}",
                    'type': a.type.value,
                    'confidence': 0.8,
                    'metadata': a.__dict__
                }
                for i, a in enumerate(candidates)
            ]
            
            # DMD decide (simplificado)
            # decision = self.dmd.decide(action_candidates_dmd)
            # return decision.chosen_action['metadata']
        
        # Por defecto, retornar primera acción
        return candidates[0]
    
    async def _execute_action(self, action: Action) -> Observation:
        """
        Ejecuta la acción y retorna observación
        """
        start_time = datetime.now()
        
        try:
            # Ejecutar según tipo
            if action.type == ActionType.TOOL_USE:
                result = await self._execute_tool(action)
            elif action.type == ActionType.CODE_EXECUTE:
                result = await self._execute_code(action)
            elif action.type == ActionType.WEB_SEARCH:
                result = await self._execute_web_search(action)
            elif action.type == ActionType.KG_QUERY:
                result = await self._execute_kg_query(action)
            else:
                result = f"Acción {action.type.value} ejecutada (simulada)"
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            observation = Observation(
                action=action,
                status=StepStatus.SUCCESS,
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            observation = Observation(
                action=action,
                status=StepStatus.FAILED,
                result=None,
                error=str(e),
                execution_time=execution_time,
                requires_replanning=True
            )
        
        # Guardar en historial
        self.state.action_history.append((action, observation))
        
        return observation
    
    async def _execute_tool(self, action: Action) -> Any:
        """Ejecuta herramienta externa"""
        # Simulado - en producción llamar a herramienta real
        return {"tool_result": "datos obtenidos"}
    
    async def _execute_code(self, action: Action) -> Any:
        """Ejecuta código"""
        # Simulado - en producción usar sandbox
        return {"code_result": "ejecución exitosa"}
    
    async def _execute_web_search(self, action: Action) -> Any:
        """Ejecuta búsqueda web"""
        # Integrar con web_search tool
        return {"search_results": []}
    
    async def _execute_kg_query(self, action: Action) -> Any:
        """Query al Knowledge Graph"""
        if self.kg:
            # Usar GraphRAG
            query = action.parameters.get("query", "")
            # result = await self.kg.query(query)
            return {"kg_result": "información del grafo"}
        return None
    
    def _process_observation(self, observation: Observation):
        """
        Procesa resultado y actualiza estado
        """
        # Añadir observación al contexto
        context_entry = f"ACCIÓN: {observation.action.description}\n"
        context_entry += f"RESULTADO: {observation.result}\n"
        
        if observation.status == StepStatus.SUCCESS:
            context_entry += "STATUS: ✅ Exitoso\n"
            importance = 1.0
        else:
            context_entry += f"STATUS: ❌ Falló - {observation.error}\n"
            importance = 1.5  # Mayor importancia a fallos
        
        self.context_manager.add_to_context(context_entry, importance=importance)
        
        # Actualizar progreso
        current_goal = self.state.get_current_goal()
        if observation.status == StepStatus.SUCCESS:
            current_goal.progress += 0.01  # Incremento pequeño por acción exitosa
            current_goal.progress = min(1.0, current_goal.progress)
    
    async def _should_replan(self, observation: Observation) -> bool:
        """Decide si necesita re-planificar"""
        # Re-planificar si:
        # 1. Acción falló
        # 2. Resultado inesperado
        # 3. Objetivo drift detectado
        
        if observation.requires_replanning:
            return True
        
        if observation.status == StepStatus.FAILED:
            return True
        
        return False
    
    async def _replan(self, observation: Observation):
        """
        Re-planifica estrategia
        """
        print(f"🔄 Re-planificando en paso {self.state.step}")
        
        # Solicitar nuevo plan al LLM
        replan_prompt = f"""La acción anterior falló. Necesito re-planificar.

OBJETIVO: {self.state.get_original_goal()}
ERROR: {observation.error}
INTENTOS: {observation.action.retries}/{observation.action.max_retries}

Sugiere una estrategia alternativa.
"""
        
        # Actualizar subobjetivo
        current_goal = self.state.get_current_goal()
        current_goal.current_subgoal = "Estrategia alternativa necesaria"
    
    async def _recover_from_drift(self):
        """
        Recupera el foco cuando hay goal drift
        """
        print(f"🎯 Recuperando foco en objetivo original")
        
        # Re-inyectar I₀ en el contexto con alta importancia
        original_goal = self.state.get_original_goal()
        self.context_manager.add_to_context(
            f"⚠️  RECORDATORIO - OBJETIVO ORIGINAL: {original_goal}",
            importance=3.0
        )
    
    async def _is_goal_achieved(self) -> bool:
       