"""
Sistema de Memoria Cognitiva (OPTIMIZADO)
Integración completa con búsqueda mejorada y caché
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class MemoryCache:
    """Cache en memoria para búsquedas frecuentes"""

    def __init__(self, max_size: int = 50):
        self.cache = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[List[Dict]]:
        """Obtener del cache"""
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None

    def set(self, key: str, value: List[Dict]):
        """Guardar en cache con LRU"""
        if len(self.cache) >= self.max_size:
            # Eliminar el más antiguo
            oldest = next(iter(self.cache))
            del self.cache[oldest]

        self.cache[key] = value

    def clear(self):
        """Limpiar cache"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas del cache"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2),
        }


class CognitiveMemory:
    """
    Sistema de memoria persistente (OPTIMIZADO)

    Mejoras:
    1. Cache LRU para búsquedas frecuentes
    2. Búsqueda mejorada con ranking
    3. Índices optimizados
    4. Estadísticas detalladas
    """

    def __init__(
        self, db_path: str = "memory/cognitive.db", enable_cache: bool = True
    ):
        self.db_path = db_path
        self._ensure_db_exists()
        self.working_memory = {}
        self.consolidation_threshold = 5
        self.cache = MemoryCache() if enable_cache else None

    def _ensure_db_exists(self):
        """Crear base de datos si no existe (OPTIMIZADA)"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabla de memoria a corto plazo
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS short_term_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                intent TEXT,
                context TEXT,
                result TEXT,
                confidence REAL,
                access_count INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                relevance_score REAL DEFAULT 1.0
            )
        """
        )

        # Tabla de memoria a largo plazo
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS long_term_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_key TEXT UNIQUE NOT NULL,
                pattern_data TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                last_accessed TEXT,
                consolidated_at TEXT NOT NULL,
                importance REAL DEFAULT 1.0
            )
        """
        )

        # Índices optimizados
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_intent
            ON short_term_memory(intent)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON short_term_memory(timestamp DESC)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_confidence
            ON short_term_memory(confidence DESC)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_access_count
            ON short_term_memory(access_count DESC)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_pattern_key
            ON long_term_memory(pattern_key)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_frequency
            ON long_term_memory(frequency DESC)
        """
        )

        conn.commit()
        conn.close()

    def store(self, state, result) -> int:
        """Almacenar estado y resultado en memoria"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calcular relevance score
        relevance = self._calculate_relevance(state, result)

        cursor.execute(
            """
            INSERT INTO short_term_memory
            (timestamp, intent, context, result, confidence, created_at,
             relevance_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                state.timestamp.isoformat(),
                state.intent,
                json.dumps(state.context),
                str(result),
                state.confidence,
                datetime.now().isoformat(),
                relevance,
            ),
        )

        memory_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Limpiar cache ya que hay datos nuevos
        if self.cache:
            self.cache.clear()

        # Verificar consolidación
        self._check_consolidation(state.intent)

        return memory_id

    def _calculate_relevance(self, state, result) -> float:
        """Calcular score de relevancia (NUEVO)"""
        score = 1.0

        # Mayor relevancia si alta confianza
        score += state.confidence * 0.5

        # Mayor relevancia si fue exitoso
        if hasattr(result, "success") and result.success:
            score += 0.3

        return min(score, 2.0)

    def retrieve(
        self, query: str, limit: int = 10, min_relevance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Recuperar memorias relevantes (MEJORADA)

        Mejoras:
        - Cache de búsquedas frecuentes
        - Ranking por relevancia
        - Filtro por score mínimo
        - Actualización de access_count
        """
        # Verificar cache
        cache_key = f"{query}:{limit}:{min_relevance}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if query:
            # Búsqueda con ranking
            cursor.execute(
                """
                SELECT * FROM short_term_memory
                WHERE
                    (intent LIKE ? OR context LIKE ?)
                    AND relevance_score >= ?
                ORDER BY
                    relevance_score DESC,
                    access_count DESC,
                    timestamp DESC
                LIMIT ?
            """,
                (f"%{query}%", f"%{query}%", min_relevance, limit),
            )
        else:
            # Sin query, traer las más relevantes
            cursor.execute(
                """
                SELECT * FROM short_term_memory
                WHERE relevance_score >= ?
                ORDER BY
                    relevance_score DESC,
                    timestamp DESC
                LIMIT ?
            """,
                (min_relevance, limit),
            )

        columns = [desc[0] for desc in cursor.description]
        results = []

        for row in cursor.fetchall():
            memory = dict(zip(columns, row))

            # Incrementar contador de acceso
            cursor.execute(
                """
                UPDATE short_term_memory
                SET access_count = access_count + 1
                WHERE id = ?
            """,
                (memory["id"],),
            )

            results.append(memory)

        conn.commit()
        conn.close()

        # Guardar en cache
        if self.cache:
            self.cache.set(cache_key, results)

        return results

    def search_by_intent(
        self, intent: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Búsqueda específica por intent (NUEVA)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM short_term_memory
            WHERE intent = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (intent, limit),
        )

        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results

    def get_most_relevant(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtener las memorias más relevantes (NUEVA)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM short_term_memory
            ORDER BY
                relevance_score DESC,
                access_count DESC,
                confidence DESC
            LIMIT ?
        """,
            (limit,),
        )

        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results

    def _check_consolidation(self, intent: str):
        """Verificar si un patrón debe consolidarse a largo plazo"""
        if not intent:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*), AVG(confidence), AVG(relevance_score)
            FROM short_term_memory
            WHERE intent = ?
        """,
            (intent,),
        )

        result = cursor.fetchone()
        count, avg_confidence, avg_relevance = result

        if count >= self.consolidation_threshold:
            # Calcular importancia
            importance = (avg_confidence or 0.5) * (avg_relevance or 1.0)

            # Consolidar a largo plazo
            cursor.execute(
                """
                INSERT OR REPLACE INTO long_term_memory
                (pattern_key, pattern_data, frequency, last_accessed,
                 consolidated_at, importance)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    intent,
                    json.dumps(
                        {
                            "intent": intent,
                            "occurrences": count,
                            "avg_confidence": avg_confidence,
                            "avg_relevance": avg_relevance,
                        }
                    ),
                    count,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    importance,
                ),
            )

        conn.commit()
        conn.close()

    def get_long_term_patterns(
        self, min_frequency: int = 1
    ) -> List[Dict[str, Any]]:
        """Obtener patrones consolidados (MEJORADA)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM long_term_memory
            WHERE frequency >= ?
            ORDER BY importance DESC, frequency DESC
        """,
            (min_frequency,),
        )

        columns = [desc[0] for desc in cursor.description]
        patterns = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return patterns

    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas de memoria (MEJORADAS)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*), AVG(confidence), AVG(relevance_score)
            FROM short_term_memory
        """
        )
        short_count, avg_conf, avg_rel = cursor.fetchone()

        cursor.execute(
            "SELECT COUNT(*), AVG(importance) FROM long_term_memory"
        )
        long_count, avg_imp = cursor.fetchone()

        cursor.execute("SELECT MAX(access_count) FROM short_term_memory")
        max_access = cursor.fetchone()[0] or 0

        conn.close()

        stats = {
            "short_term_count": short_count or 0,
            "long_term_count": long_count or 0,
            "average_confidence": round(avg_conf or 0.0, 3),
            "average_relevance": round(avg_rel or 0.0, 3),
            "average_importance": round(avg_imp or 0.0, 3),
            "max_access_count": max_access,
            "total_memories": (short_count or 0) + (long_count or 0),
        }

        if self.cache:
            stats["cache_stats"] = self.cache.get_stats()

        return stats

    def clear_short_term(self, older_than_days: int = 30) -> int:
        """Limpiar memoria a corto plazo antigua"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM short_term_memory
            WHERE datetime(created_at) < datetime('now', '-' || ? || ' days')
        """,
            (older_than_days,),
        )

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        # Limpiar cache
        if self.cache:
            self.cache.clear()

        return deleted

    def optimize(self):
        """Optimizar base de datos (NUEVO)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # VACUUM para compactar
        cursor.execute("VACUUM")

        # ANALYZE para optimizar índices
        cursor.execute("ANALYZE")

        conn.close()

        # Limpiar cache
        if self.cache:
            self.cache.clear()
