# memory/semantic_matrix.py - Memoria Semántica (Neocorteza)
"""
Implementa memoria semántica como matriz Mₜ con consolidación.
Mₜ ← Update(Mₜ₋₁, zₜ; η)

Este módulo simula la neocorteza: almacena conocimiento abstracto
y estructuras aprendidas a largo plazo.
"""

import pickle
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.decomposition import IncrementalPCA


@dataclass
class SemanticConcept:
    """Concepto semántico"""

    id: str
    prototype: np.ndarray  # Vector prototipo del concepto
    instances: int  # Número de instancias vistas
    variance: float  # Varianza del concepto
    tags: List[str]


class SemanticMemoryMatrix:
    """
    Memoria Semántica basada en Matriz.

    Funcionalidades:
    1. Consolidación: abstracta patrones de episodios
    2. Prototipado: encuentra centros de clusters
    3. Generalización: comprime información redundante
    4. Recuperación: accede a conocimiento estructurado
    5. Actualización incremental: aprende continuamente
    """

    def __init__(
        self,
        dim_state: int,
        max_concepts: int = 1000,
        learning_rate: float = 0.01,
        compression_dim: Optional[int] = None,
    ):
        """
        Args:
            dim_state: dimensión del estado z
            max_concepts: número máximo de conceptos
            learning_rate: η para actualización
            compression_dim: dimensión comprimida (None = sin compresión)
        """
        self.dim_state = dim_state
        self.max_concepts = max_concepts
        self.learning_rate = learning_rate
        self.compression_dim = compression_dim or dim_state

        # Matriz de conceptos [n_concepts × dim_state]
        self.M = np.zeros((max_concepts, dim_state))
        self.n_concepts = 0

        # Metadata de conceptos
        self.concepts: Dict[int, SemanticConcept] = {}

        # Compresión (PCA incremental)
        if compression_dim < dim_state:
            self.pca = IncrementalPCA(n_components=compression_dim)
            self.pca_fitted = False
        else:
            self.pca = None
            self.pca_fitted = False

        # Estadísticas
        self.total_updates = 0
        self.total_consolidations = 0

    def consolidate(
        self,
        state: np.ndarray,
        tags: Optional[List[str]] = None,
        threshold: float = 0.8,
    ) -> Tuple[int, bool]:
        """
        Consolida un estado en la memoria semántica.

        Estrategia:
        1. Si existe concepto similar → actualizar prototipo
        2. Si no existe → crear nuevo concepto

        Args:
            state: estado cortical zₜ a consolidar
            tags: etiquetas semánticas
            threshold: umbral de similaridad para merge

        Returns:
            (concept_id, is_new): ID del concepto y si es nuevo
        """
        self.total_updates += 1

        # Comprimir si es necesario
        if self.pca is not None:
            state_compressed = self._compress_state(state)
        else:
            state_compressed = state

        # Buscar concepto similar
        if self.n_concepts > 0:
            similarities = self._compute_similarities(state_compressed)
            best_idx = np.argmax(similarities)
            best_sim = similarities[best_idx]

            # Si hay match, actualizar
            if best_sim > threshold:
                self._update_concept(best_idx, state_compressed, tags)
                return best_idx, False

        # Crear nuevo concepto
        if self.n_concepts < self.max_concepts:
            concept_id = self._create_concept(state_compressed, tags)
            self.total_consolidations += 1
            return concept_id, True
        else:
            # Memoria llena, reemplazar el menos usado
            concept_id = self._replace_least_used(state_compressed, tags)
            return concept_id, False

    def _compress_state(self, state: np.ndarray) -> np.ndarray:
        """Comprime estado usando PCA incremental"""
        if not self.pca_fitted:
            # Primera vez: fit con batch inicial
            self.pca.partial_fit(state.reshape(1, -1))
            self.pca_fitted = True

        # Transform
        compressed = self.pca.transform(state.reshape(1, -1))
        return compressed.flatten()

    def _compute_similarities(self, state: np.ndarray) -> np.ndarray:
        """Calcula similaridad con todos los conceptos"""
        active_concepts = self.M[: self.n_concepts]

        # Similaridad coseno
        norms = np.linalg.norm(active_concepts, axis=1, keepdims=True) + 1e-9
        state_norm = np.linalg.norm(state) + 1e-9

        similarities = (active_concepts @ state) / (norms.flatten() * state_norm)

        return similarities

    def _create_concept(self, state: np.ndarray, tags: Optional[List[str]]) -> int:
        """Crea nuevo concepto"""
        concept_id = self.n_concepts

        # Almacenar en matriz
        self.M[concept_id] = state

        # Crear metadata
        self.concepts[concept_id] = SemanticConcept(
            id=f"concept_{concept_id}",
            prototype=state.copy(),
            instances=1,
            variance=0.0,
            tags=tags or [],
        )

        self.n_concepts += 1
        return concept_id

    def _update_concept(
        self, concept_id: int, state: np.ndarray, tags: Optional[List[str]]
    ):
        """Actualiza concepto existente con nueva instancia"""
        concept = self.concepts[concept_id]

        # Media móvil exponencial del prototipo
        alpha = self.learning_rate
        old_prototype = self.M[concept_id]
        new_prototype = (1 - alpha) * old_prototype + alpha * state

        # Actualizar matriz
        self.M[concept_id] = new_prototype

        # Actualizar variance (aproximación)
        diff = np.linalg.norm(state - old_prototype)
        concept.variance = (1 - alpha) * concept.variance + alpha * diff**2

        # Actualizar metadata
        concept.instances += 1
        concept.prototype = new_prototype

        if tags:
            concept.tags = list(set(concept.tags + tags))

    def _replace_least_used(self, state: np.ndarray, tags: Optional[List[str]]) -> int:
        """Reemplaza el concepto menos usado"""
        # Encontrar concepto con menos instancias
        least_used_id = min(
            self.concepts.keys(), key=lambda k: self.concepts[k].instances
        )

        # Reemplazar
        self.M[least_used_id] = state
        self.concepts[least_used_id] = SemanticConcept(
            id=f"concept_{least_used_id}",
            prototype=state.copy(),
            instances=1,
            variance=0.0,
            tags=tags or [],
        )

        return least_used_id

    def retrieve(
        self, query: np.ndarray, top_k: int = 5, min_similarity: float = 0.5
    ) -> List[Tuple[int, float, SemanticConcept]]:
        """
        Recupera conceptos semánticos relevantes.

        Args:
            query: estado de consulta
            top_k: número de conceptos a recuperar
            min_similarity: similaridad mínima

        Returns:
            List de (concept_id, similarity, concept)
        """
        if self.n_concepts == 0:
            return []

        # Comprimir query si es necesario
        if self.pca is not None and self.pca_fitted:
            query_compressed = self._compress_state(query)
        else:
            query_compressed = query

        # Calcular similaridades
        similarities = self._compute_similarities(query_compressed)

        # Filtrar por umbral y ordenar
        results = []
        for i in range(self.n_concepts):
            if similarities[i] >= min_similarity:
                results.append((i, similarities[i], self.concepts[i]))

        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def get_concept_by_tag(self, tag: str) -> List[Tuple[int, SemanticConcept]]:
        """Recupera conceptos por tag"""
        results = []
        for cid, concept in self.concepts.items():
            if tag in concept.tags:
                results.append((cid, concept))
        return results

    def merge_similar_concepts(self, threshold: float = 0.95):
        """
        Fusiona conceptos muy similares para reducir redundancia.

        Args:
            threshold: umbral de similaridad para merge
        """
        if self.n_concepts < 2:
            return

        merged = []

        for i in range(self.n_concepts):
            if i in merged:
                continue

            for j in range(i + 1, self.n_concepts):
                if j in merged:
                    continue

                # Calcular similaridad
                sim = np.dot(self.M[i], self.M[j]) / (
                    np.linalg.norm(self.M[i]) * np.linalg.norm(self.M[j]) + 1e-9
                )

                if sim > threshold:
                    # Fusionar j en i
                    concept_i = self.concepts[i]
                    concept_j = self.concepts[j]

                    total_instances = concept_i.instances + concept_j.instances
                    weight_i = concept_i.instances / total_instances
                    weight_j = concept_j.instances / total_instances

                    # Nuevo prototipo ponderado
                    self.M[i] = weight_i * self.M[i] + weight_j * self.M[j]

                    # Actualizar metadata
                    concept_i.instances = total_instances
                    concept_i.tags = list(set(concept_i.tags + concept_j.tags))
                    concept_i.variance = max(concept_i.variance, concept_j.variance)

                    merged.append(j)

        # Compactar matriz eliminando conceptos fusionados
        if merged:
            self._compact_matrix(merged)

    def _compact_matrix(self, removed_ids: List[int]):
        """Compacta la matriz eliminando conceptos"""
        removed_ids = sorted(removed_ids, reverse=True)

        for rid in removed_ids:
            # Mover conceptos posteriores
            if rid < self.n_concepts - 1:
                self.M[rid : self.n_concepts - 1] = self.M[rid + 1 : self.n_concepts]

            # Eliminar del dict
            del self.concepts[rid]

            # Reindexar conceptos posteriores
            for cid in range(rid, self.n_concepts):
                if cid + 1 in self.concepts:
                    self.concepts[cid] = self.concepts[cid + 1]
                    del self.concepts[cid + 1]

            self.n_concepts -= 1

    def get_statistics(self) -> Dict:
        """Retorna estadísticas de la memoria"""
        if self.n_concepts == 0:
            return {
                "total_concepts": 0,
                "total_updates": self.total_updates,
                "total_consolidations": self.total_consolidations,
            }

        variances = [c.variance for c in self.concepts.values()]
        instances = [c.instances for c in self.concepts.values()]

        return {
            "total_concepts": self.n_concepts,
            "total_updates": self.total_updates,
            "total_consolidations": self.total_consolidations,
            "avg_variance": np.mean(variances),
            "avg_instances": np.mean(instances),
            "memory_usage_pct": self.n_concepts / self.max_concepts * 100,
            "compression_enabled": self.pca is not None,
        }

    def save(self, filepath: str):
        """Guarda la memoria en disco"""
        data = {
            "M": self.M,
            "n_concepts": self.n_concepts,
            "concepts": self.concepts,
            "config": {
                "dim_state": self.dim_state,
                "max_concepts": self.max_concepts,
                "learning_rate": self.learning_rate,
                "compression_dim": self.compression_dim,
            },
        }

        with open(filepath, "wb") as f:
            pickle.dump(data, f)

    def load(self, filepath: str):
        """Carga la memoria desde disco"""
        with open(filepath, "rb") as f:
            data = pickle.load(f)

        self.M = data["M"]
        self.n_concepts = data["n_concepts"]
        self.concepts = data["concepts"]


# =========================
# Testing
# =========================

if __name__ == "__main__":
    print("=== Test de Memoria Semántica (Consolidación) ===\n")

    np.random.seed(42)

    # Crear memoria
    memory = SemanticMemoryMatrix(
        dim_state=32, max_concepts=50, learning_rate=0.05, compression_dim=16
    )

    print("Configuración:")
    print(f"  Dim estado: {memory.dim_state}")
    print(f"  Dim comprimida: {memory.compression_dim}")
    print(f"  Capacidad: {memory.max_concepts} conceptos")
    print(f"  Learning rate: {memory.learning_rate}")

    # Consolidar estados simulados
    print("\n--- Consolidación de Estados ---")

    # Crear 3 clusters de estados similares
    cluster_centers = [
        np.random.randn(32) * 2,
        np.random.randn(32) * 2 + 5,
        np.random.randn(32) * 2 - 5,
    ]

    for i in range(30):
        cluster_id = i % 3
        state = cluster_centers[cluster_id] + np.random.randn(32) * 0.5
        tags = [f"cluster_{cluster_id}", f"tag_{i % 5}"]

        concept_id, is_new = memory.consolidate(state, tags=tags, threshold=0.8)

        if i < 5 or is_new:
            status = "NUEVO" if is_new else "actualizado"
            print(f"  Estado {i+1}: Concepto {concept_id} {status}")

    print(f"\nTotal de conceptos creados: {memory.n_concepts}")

    # Recuperar conceptos
    print("\n--- Recuperación de Conceptos ---")
    query = cluster_centers[0] + np.random.randn(32) * 0.3

    results = memory.retrieve(query, top_k=3, min_similarity=0.5)

    print(f"Query cerca del cluster 0")
    print(f"Conceptos recuperados:")
    for i, (cid, sim, concept) in enumerate(results):
        print(f"  {i+1}. Concepto {cid}: sim={sim:.3f}, instancias={concept.instances}")
        print(f"     Tags: {concept.tags[:3]}")

    # Merge de conceptos similares
    print("\n--- Merge de Conceptos Similares ---")
    print(f"Conceptos antes del merge: {memory.n_concepts}")
    memory.merge_similar_concepts(threshold=0.9)
    print(f"Conceptos después del merge: {memory.n_concepts}")

    # Estadísticas
    print("\n--- Estadísticas ---")
    stats = memory.get_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    print("\n✅ Memoria Semántica funcional - Neocorteza activa")
