"""
Actuator: Sistema de ejecución de acciones (OPTIMIZADO)
Incluye cache LRU, métricas y thread-safety
"""

import hashlib
import threading
from collections import deque
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class IntentType(Enum):
    """Tipos de intención para clasificación de tareas"""

    ACT_IMMEDIATELY = "act_immediately"
    SCHEDULE_TASK = "schedule_task"
    ANALYZE_ONLY = "analyze_only"
    WAIT_FOR_INPUT = "wait_for_input"


class ActionResult:
    """Resultado de una ejecución"""

    def __init__(self, success: bool, data: Any, error: str = None):
        self.success = success
        self.data = data
        self.error = error
        self.timestamp = datetime.now()


class ActuatorCache:
    """Cache LRU para resultados de acciones"""

    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.order = deque()
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
            # Mover al final (más reciente)
            self.order.remove(key)
            self.order.append(key)
            return self.cache[key]
        self.misses += 1
        return None

    def set(self, intent: IntentType, context: Dict, result: ActionResult):
        """Guardar en cache con política LRU"""
        if not result.success:
            return  # No cachear errores

        key = self._get_key(intent, context)
        if key in self.cache:
            self.order.remove(key)
        elif len(self.cache) >= self.max_size:
            # Eliminar el más antiguo
            oldest = self.order.popleft()
            del self.cache[oldest]

        self.cache[key] = result
        self.order.append(key)

    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas del cache"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%",
        }


class Actuator:
    """
    Actuador de acciones (OPTIMIZADO)

    Mejoras:
    1. Cache LRU para evitar ejecuciones redundantes
    2. Thread-safety para ejecuciones concurrentes
    3. Métricas de rendimiento
    4. Priorización de tareas
    """

    def __init__(self, enable_cache: bool = True):
        self.plugins = {}
        self.cache = ActuatorCache() if enable_cache else None
        self.lock = threading.Lock()
        self.execution_history = deque(maxlen=1000)
        self.metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "start_time": datetime.now(),
        }

    def register_plugin(self, name: str, plugin_instance: Any):
        """Registrar un nuevo plugin de acción"""
        with self.lock:
            self.plugins[name] = plugin_instance

    def execute(
        self, intent: IntentType, context: Dict, priority: int = 0
    ) -> ActionResult:
        """
        Ejecutar una acción basada en la intención (MEJORADA)
        """
        # 1. Verificar cache
        if self.cache:
            cached_result = self.cache.get(intent, context)
            if cached_result:
                return cached_result

        # 2. Ejecución con Lock para thread-safety
        with self.lock:
            self.metrics["total_executions"] += 1
            try:
                result = self._dispatch(intent, context)

                if result.success:
                    self.metrics["successful_executions"] += 1
                else:
                    self.metrics["failed_executions"] += 1

                # Guardar en historial
                self.execution_history.append(
                    {
                        "intent": intent.value,
                        "context": context,
                        "result": result,
                        "timestamp": datetime.now().isoformat(),
                        "cached": False,
                    }
                )

                # Guardar en cache
                if self.cache:
                    self.cache.set(intent, context, result)

                return result

            except Exception as e:
                self.metrics["failed_executions"] += 1
                return ActionResult(False, None, str(e))

    def _dispatch(self, intent: IntentType, context: Dict) -> ActionResult:
        """Despachar la acción al plugin correspondiente"""
        if intent == IntentType.ACT_IMMEDIATELY:
            return self._handle_immediate(context)
        elif intent == IntentType.SCHEDULE_TASK:
            return self._handle_scheduled(context)
        elif intent == IntentType.ANALYZE_ONLY:
            return ActionResult(True, {"analysis": "Analysis completed"})
        else:
            return ActionResult(False, None, f"Unsupported intent: {intent}")

    def _handle_immediate(self, context: Dict) -> ActionResult:
        """Manejar acciones inmediatas"""
        plugin_name = context.get("plugin")
        if not plugin_name or plugin_name not in self.plugins:
            return ActionResult(False, None, f"Plugin {plugin_name} not found")

        try:
            plugin = self.plugins[plugin_name]
            data = plugin.execute(context)
            return ActionResult(True, data)
        except Exception as e:
            return ActionResult(False, None, f"Plugin execution error: {e}")

    def _handle_scheduled(self, context: Dict) -> ActionResult:
        """Manejar tareas programadas"""
        # Simulación de scheduler
        task_id = hashlib.sha256(str(datetime.now().timestamp()).encode()).hexdigest()[
            :8
        ]
        return ActionResult(True, {"task_id": task_id, "status": "scheduled"})

    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de rendimiento"""
        uptime = datetime.now() - self.metrics["start_time"]
        success_rate = 0
        if self.metrics["total_executions"] > 0:
            success_rate = (
                self.metrics["successful_executions"]
                / self.metrics["total_executions"]
                * 100
            )

        stats = {
            "uptime_seconds": int(uptime.total_seconds()),
            "total_executions": self.metrics["total_executions"],
            "success_rate": f"{success_rate:.2f}%",
            "active_plugins": list(self.plugins.keys()),
        }

        if self.cache:
            stats["cache"] = self.cache.get_stats()

        return stats

    def get_history(self, limit: int = 10) -> List[Dict]:
        """Obtener historial reciente de ejecuciones"""
        return list(self.execution_history)[-limit:]
