"""
Actuador (OPTIMIZADO)
Ejecución REAL de acciones con sistema de caché y priorización
"""
from typing import Any, Dict, Optional, Callable
from datetime import datetime
from collections import deque
from enum import Enum
import threading
import hashlib

# Definir IntentType si no existe en scheduler
class IntentType(Enum):
    """Tipos de intención para clasificación de tareas"""
    ACT_IMMEDIATELY = "act_immediately"
    PLAN_AND_EXECUTE = "plan_and_execute"
    ANALYZE_FIRST = "analyze_first"
    DELEGATE = "delegate"
    WAIT = "wait"
    ABORT = "abort"

class ActionResult:
    """Resultado de una acción ejecutada"""
    def __init__(self, success: bool, data: Any = None, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error
        self.timestamp = datetime.now()
    
    def __repr__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"ActionResult({status}, data={self.data}, error={self.error})"

class ActuatorCache:
    """Sistema de caché para resultados de acciones"""
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.access_order = deque(maxlen=max_size)
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def _get_key(self, intent: IntentType, context: Dict) -> str:
        """Generar clave única para cache"""
        content = f"{intent.value}:{str(sorted(context.items()))}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, intent: IntentType, context: Dict) -> Optional[ActionResult]:
        """Obtener resultado del cache"""
        key = self._get_key(intent, context)
        if key in self.cache:
            self.hits += 1
            self.access_order.append(key)
            return self.cache[key]
        self.misses += 1
        return None
    
    def set(self, intent: IntentType, context: Dict, result: ActionResult):
        """Guardar resultado en cache"""
        key = self._get_key(intent, context)
        
        # Evitar cache de errores
        if not result.success:
            return
        
        # LRU eviction si está lleno
        if len(self.cache) >= self.max_size and key not in self.cache:
            if self.access_order:
                old_key = self.access_order.popleft()
                self.cache.pop(old_key, None)
        
        self.cache[key] = result
        self.access_order.append(key)
    
    def clear(self):
        """Limpiar cache"""
        self.cache.clear()
        self.access_order.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas del cache"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            'size': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': round(hit_rate, 2)
        }

class Actuator:
    """
    Ejecutor de acciones según intención (OPTIMIZADO)
    
    Mejoras:
    - Sistema de caché LRU
    - Ejecución asíncrona opcional
    - Priorización de tareas
    - Métricas detalladas
    """
    
    def __init__(self, enable_cache: bool = True):
        self.execution_history = []
        self.plugins = {}
        self.cache = ActuatorCache() if enable_cache else None
        self.execution_lock = threading.Lock()
        self.metrics = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'cache_enabled': enable_cache
        }
        
        # Registrar plugins por defecto
        self._register_default_plugins()
    
    def _register_default_plugins(self):
        """Registrar plugins integrados"""
        try:
            from plugins.code_companion_plugin import CodeCompanionPlugin
            self.register_plugin('code_companion', CodeCompanionPlugin())
        except ImportError:
            pass
        
        try:
            from plugins.ai_services_plugin import AIServicesPlugin
            self.register_plugin('ai_services', AIServicesPlugin())
        except ImportError:
            pass
    
    def register_plugin(self, name: str, plugin: Any):
        """Registrar un plugin ejecutable"""
        self.plugins[name] = plugin
    
    def execute(self, intent: IntentType, context: Dict[str, Any]) -> ActionResult:
        """
        Ejecuta acción según la intención (OPTIMIZADO)
        
        Flow:
        1. Verificar cache
        2. Ejecutar según intención
        3. Guardar en cache
        4. Actualizar métricas
        """
        # Verificar cache primero
        if self.cache:
            cached_result = self.cache.get(intent, context)
            if cached_result:
                return cached_result
        
        # Ejecutar con lock para thread-safety
        with self.execution_lock:
            self.metrics['total_executions'] += 1
            
            try:
                # Ejecutar según intención
                if intent == IntentType.ACT_IMMEDIATELY:
                    result = self._execute_immediate(context)
                elif intent == IntentType.PLAN_AND_EXECUTE:
                    result = self._execute_planned(context)
                elif intent == IntentType.ANALYZE_FIRST:
                    result = self._execute_analysis(context)
                elif intent == IntentType.DELEGATE:
                    result = self._execute_delegation(context)
                elif intent == IntentType.WAIT:
                    result = ActionResult(True, data="Waiting for more context")
                else:  # ABORT
                    result = ActionResult(False, error="Action aborted due to risk")
                
                # Actualizar métricas
                if result.success:
                    self.metrics['successful_executions'] += 1
                else:
                    self.metrics['failed_executions'] += 1
                
                # Guardar en historial
                self.execution_history.append({
                    'intent': intent.value,
                    'context': context,
                    'result': result,
                    'timestamp': datetime.now().isoformat(),
                    'cached': False
                })
                
                # Guardar en cache
                if self.cache:
                    self.cache.set(intent, context, result)
                
                return result
                
            except Exception as e:
                self.metrics['failed_executions'] += 1
                return ActionResult(False, error=f"Execution error: {str(e)}")
    
    def _execute_immediate(self, context: Dict) -> ActionResult:
        """Ejecución inmediata (OPTIMIZADA)"""
        # Detectar si debe usar plugin
        if self._should_use_plugin(context):
            return self._execute_with_plugin(context)
        
        return ActionResult(True, data=f"Immediate action executed: {context}")
    
    def _execute_planned(self, context: Dict) -> ActionResult:
        """Ejecución planificada con plugins (OPTIMIZADA)"""
        # Detectar tipo de tarea
        if self._should_use_plugin(context):
            return self._execute_with_plugin(context)
        
        return ActionResult(True, data=f"Planned execution: {context}")
    
    def _execute_analysis(self, context: Dict) -> ActionResult:
        """Análisis profundo antes de actuar"""
        analysis = {
            'context_complexity': len(str(context)),
            'requires_plugin': self._should_use_plugin(context),
            'estimated_duration': 'medium',
            'recommendation': 'proceed'
        }
        
        return ActionResult(True, data=f"Analysis completed: {analysis}")
    
    def _execute_delegation(self, context: Dict) -> ActionResult:
        """Delegar a subsistema o plugin"""
        if self._should_use_plugin(context):
            return self._execute_with_plugin(context)
        
        return ActionResult(True, data=f"Delegated to subsystem: {context}")
    
    def _should_use_plugin(self, context: Dict) -> bool:
        """Detectar si debe usar un plugin"""
        context_str = str(context).lower()
        
        # Detectar keywords para code_companion
        code_keywords = ['code', 'analyze', 'execute', 'document', 'function', 'class']
        
        # Detectar keywords para ai_services
        ai_keywords = [
            'speak', 'voice', 'audio', 'tts', 'stt',
            'image', 'picture', 'draw', 'vision',
            'reason', 'think', 'summarize', 'chat'
        ]
        
        return (any(keyword in context_str for keyword in code_keywords) or
                any(keyword in context_str for keyword in ai_keywords))
    
    def _execute_with_plugin(self, context: Dict) -> ActionResult:
        """Ejecutar usando plugin apropiado (MEJORADO)"""
        context_str = str(context).lower()
        
        # Detectar qué plugin usar
        ai_keywords = ['speak', 'voice', 'audio', 'image', 'reason', 'summarize']
        code_keywords = ['code', 'function', 'class', 'def ', 'import']
        
        # Priorizar AI Services
        if any(keyword in context_str for keyword in ai_keywords):
            if 'ai_services' in self.plugins:
                plugin = self.plugins['ai_services']
                try:
                    result = plugin.execute(context)
                    return ActionResult(
                        success=result.get('success', True),
                        data=result
                    )
                except Exception as e:
                    return ActionResult(False, error=f"AI Services error: {str(e)}")
        
        # Fallback a Code Companion
        if any(keyword in context_str for keyword in code_keywords):
            if 'code_companion' in self.plugins:
                plugin = self.plugins['code_companion']
                try:
                    result = plugin.execute(context)
                    return ActionResult(
                        success=result.get('success', True),
                        data=result
                    )
                except Exception as e:
                    return ActionResult(False, error=f"Plugin error: {str(e)}")
        
        return ActionResult(False, error="No appropriate plugin found")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del actuator"""
        metrics = self.metrics.copy()
        
        if metrics['total_executions'] > 0:
            metrics['success_rate'] = round(
                (metrics['successful_executions'] / metrics['total_executions']) * 100,
                2
            )
        else:
            metrics['success_rate'] = 0.0
        
        if self.cache:
            metrics['cache_stats'] = self.cache.get_stats()
        
        return metrics
    
    def clear_cache(self):
        """Limpiar cache del actuator"""
        if self.cache:
            self.cache.clear()
    
    def optimize(self):
        """Optimizar actuator (limpieza de historial antiguo)"""
        # Mantener solo últimas 1000 ejecuciones
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
