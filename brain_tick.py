# memory/working_memory.py - Memoria de Trabajo (PFC)
"""
Implementa memoria de trabajo con mecanismo de gating (PFC).
wₜ = σ(Γ[zₜ, Rₜ])⊙wₜ₋₁ + (1-σ(Γ))⊙ψ(zₜ, Rₜ)

Este módulo simula la corteza prefrontal: mantiene información
activa y relevante para la tarea actual.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class WorkingMemoryConfig:
    """Configuración de memoria de trabajo"""
    capacity: int = 7            # Capacidad (7±2 items, Miller)
    decay_rate: float = 0.1      # Tasa de decaimiento
    gate_threshold: float = 0.5  # Umbral de gating
    update_strength: float = 0.8 # Fuerza de actualización

class WorkingMemory:
    """
    Memoria de Trabajo con Gating (PFC).
    
    Funcionalidades:
    1. Mantener información activa (buffer limitado)
    2. Gating: decidir qué actualizar y qué mantener
    3. Decaimiento: información antigua se desvanece
    4. Priorización: elementos más relevantes persisten
    5. Interferencia: nueva info puede desplazar la vieja
    """
    
    def __init__(self, 
                 dim: int,
                 config: Optional[WorkingMemoryConfig] = None):
        """
        Args:
            dim: dimensión del vector de memoria de trabajo
            config: configuración de WM
        """
        self.dim = dim
        self.config = config or WorkingMemoryConfig()
        
        # Estado de la memoria de trabajo
        self.w = np.zeros(dim)
        
        # Slots de memoria (lista de vectores activos)
        self.slots: List[Dict] = []
        
        # Mecanismo de gating
        self.gate_weights = self._initialize_gate_weights()
        
        # Historial
        self.update_history = []
    
    def _initialize_gate_weights(self) -> Dict[str, np.ndarray]:
        """Inicializa pesos del mecanismo de gating"""
        # Red simple para decidir gate
        return {
            'W_state': np.random.randn(self.dim, self.dim) * 0.1,
            'W_memory': np.random.randn(self.dim, self.dim) * 0.1,
            'W_gate': np.random.randn(self.dim, self.dim * 2) * 0.1,
            'b_gate': np.zeros(self.dim)
        }
    
    def update(self,
               z: np.ndarray,
               retrieved_episodes: Optional[List] = None,
               task_relevance: Optional[np.ndarray] = None) -> Tuple[np.ndarray, Dict]:
        """
        Actualiza memoria de trabajo con gating.
        
        wₜ = gate⊙wₜ₋₁ + (1-gate)⊙new_content
        
        Args:
            z: estado cortical actual
            retrieved_episodes: episodios recuperados de memoria episódica
            task_relevance: vector de relevancia para tarea actual
        
        Returns:
            w_new: nueva memoria de trabajo
            metrics: métricas del update
        """
        # 1. Construir nuevo contenido propuesto
        new_content = self._construct_new_content(z, retrieved_episodes)
        
        # 2. Calcular gate (qué mantener vs qué actualizar)
        gate = self._compute_gate(z, self.w, task_relevance)
        
        # 3. Actualización con gating
        w_new = gate * self.w + (1 - gate) * new_content
        
        # 4. Aplicar decaimiento a elementos no usados
        w_new = self._apply_decay(w_new, gate)
        
        # 5. Normalización (evitar explosión)
        w_norm = np.linalg.norm(w_new)
        if w_norm > 10.0:
            w_new = w_new / w_norm * 10.0
        
        # Actualizar estado
        old_w = self.w.copy()
        self.w = w_new
        
        # Métricas
        metrics = {
            'wm_norm': np.linalg.norm(w_new),
            'wm_change': np.linalg.norm(w_new - old_w),
            'gate_mean': np.mean(gate),
            'gate_std': np.std(gate),
            'content_strength': np.linalg.norm(new_content),
            'active_slots': self._count_active_slots(w_new)
        }
        
        # Historial
        self.update_history.append(metrics)
        if len(self.update_history) > 1000:
            self.update_history.pop(0)
        
        return w_new, metrics
    
    def _construct_new_content(self,
                              z: np.ndarray,
                              retrieved_episodes: Optional[List]) -> np.ndarray:
        """
        Construye nuevo contenido a partir de estado y episodios.
        ψ(zₜ, Rₜ)
        """
        # Proyectar estado cortical
        content = z.copy()
        
        # Si hay dimensiones diferentes, ajustar
        if len(content) != self.dim:
            if len(content) > self.dim:
                content = content[:self.dim]
            else:
                content = np.pad(content, (0, self.dim - len(content)))
        
        # Integrar información de episodios recuperados
        if retrieved_episodes:
            for i, (ep_id, score, episode) in enumerate(retrieved_episodes[:3]):
                # Ponderar por relevancia (score)
                ep_contribution = episode.state[:self.dim] * score * 0.3
                
                # Ajustar dimensiones si es necesario
                if len(ep_contribution) < self.dim:
                    ep_contribution = np.pad(ep_contribution, 
                                           (0, self.dim - len(ep_contribution)))
                elif len(ep_contribution) > self.dim:
                    ep_contribution = ep_contribution[:self.dim]
                
                content = content + ep_contribution / (i + 1)
        
        return content
    
    def _compute_gate(self,
                     z: np.ndarray,
                     w_prev: np.ndarray,
                     task_relevance: Optional[np.ndarray]) -> np.ndarray:
        """
        Calcula señal de gating σ(Γ[zₜ, wₜ₋₁]).
        
        Gate alto (→1) = mantener memoria anterior
        Gate bajo (→0) = actualizar con nuevo contenido
        """
        gw = self.gate_weights
        
        # Ajustar dimensiones
        z_adjusted = z[:self.dim] if len(z) > self.dim else np.pad(z, (0, self.dim - len(z)))
        
        # Combinación de estado y memoria previa
        combined = np.concatenate([z_adjusted, w_prev])
        
        # Forward pass (red simple)
        gate_pre = gw['W_gate'] @ combined + gw['b_gate']
        
        # Modular por relevancia si existe
        if task_relevance is not None:
            task_rel = task_relevance[:self.dim] if len(task_relevance) > self.dim else \
                      np.pad(task_relevance, (0, self.dim - len(task_relevance)))
            gate_pre = gate_pre * task_rel
        
        # Sigmoid: [0, 1]
        gate = 1.0 / (1.0 + np.exp(-gate_pre))
        
        return gate
    
    def _apply_decay(self, w: np.ndarray, gate: np.ndarray) -> np.ndarray:
        """
        Aplica decaimiento a elementos con gate bajo.
        Elementos no actualizados se desvanecen gradualmente.
        """
        decay_factor = 1.0 - self.config.decay_rate * (1.0 - gate)
        return w * decay_factor
    
    def _count_active_slots(self, w: np.ndarray) -> int:
        """Cuenta cuántos slots están activos (por encima de umbral)"""
        threshold = 0.1
        return int(np.sum(np.abs(w) > threshold))
    
    def clear_slot(self, slot_idx: int):
        """Limpia un slot específico (reset selectivo)"""
        slot_size = self.dim // self.config.capacity
        start = slot_idx * slot_size
        end = min(start + slot_size, self.dim)
        self.w[start:end] = 0.0
    
    def clear_all(self):
        """Limpia toda la memoria de trabajo"""
        self.w = np.zeros(self.dim)
    
    def get_active_content(self, threshold: float = 0.1) -> np.ndarray:
        """Retorna solo el contenido activo (por encima de umbral)"""
        mask = np.abs(self.w) > threshold
        return self.w * mask
    
    def prioritize_slot(self, slot_idx: int, boost: float = 1.5):
        """Aumenta la activación de un slot específico"""
        slot_size = self.dim // self.config.capacity
        start = slot_idx * slot_size
        end = min(start + slot_size, self.dim)
        self.w[start:end] *= boost
    
    def get_statistics(self) -> Dict:
        """Retorna estadísticas de la memoria de trabajo"""
        if not self.update_history:
            return {}
        
        recent = self.update_history[-100:]
        
        return {
            'current_norm': np.linalg.norm(self.w),
            'active_slots': self._count_active_slots(self.w),
            'capacity': self.config.capacity,
            'avg_gate': np.mean([h['gate_mean'] for h in recent]),
            'avg_change': np.mean([h['wm_change'] for h in recent]),
            'stability': 1.0 - np.mean([h['wm_change'] for h in recent]) / (np.mean([h['wm_norm'] for h in recent]) + 1e-9)
        }
    
    def rehearse(self, iterations: int = 5, strength: float = 0.9):
        """
        Rehearsal: refuerza contenido actual (simula ensayo mental).
        Útil para mantener información importante.
        """
        for _ in range(iterations):
            # Auto-refuerzo
            self.w = strength * self.w / (np.linalg.norm(self.w) + 1e-9)


# =========================
# Testing
# =========================

if __name__ == "__main__":
    print("=== Test de Working Memory (PFC Gating) ===\n")
    
    np.random.seed(42)
    
    # Crear WM
    wm = WorkingMemory(
        dim=64,
        config=WorkingMemoryConfig(
            capacity=7,
            decay_rate=0.1,
            gate_threshold=0.5
        )
    )
    
    print("Configuración:")
    print(f"  Dimensión: {wm.dim}")
    print(f"  Capacidad: {wm.config.capacity} slots")
    print(f"  Decay rate: {wm.config.decay_rate}")
    
    # Simular secuencia de updates
    print("\n--- Secuencia de Actualizaciones ---")
    
    for t in range(10):
        # Estado cortical simulado
        z = np.random.randn(64) * 0.5
        
        # Episodios simulados (opcional)
        episodes = None
        if t % 3 == 0:
            # Simular recuperación episódica
            class FakeEpisode:
                def __init__(self):
                    self.state = np.random.randn(64) * 0.3
            
            episodes = [
                (f"ep_{t}", 0.8, FakeEpisode()),
                (f"ep_{t-1}", 0.5, FakeEpisode())
            ]
        
        # Update
        w_new, metrics = wm.update(z, retrieved_episodes=episodes)
        
        if t < 5 or t % 3 == 0:
            print(f"\nTick {t}:")
            print(f"  WM norm: {metrics['wm_norm']:.3f}")
            print(f"  Change: {metrics['wm_change']:.3f}")
            print(f"  Gate (mean): {metrics['gate_mean']:.3f}")
            print(f"  Active slots: {metrics['active_slots']}")
    
    # Test de rehearsal
    print("\n--- Rehearsal (Ensayo) ---")
    print(f"Norm antes: {np.linalg.norm(wm.w):.3f}")
    wm.rehearse(iterations=5)
    print(f"Norm después: {np.linalg.norm(wm.w):.3f}")
    
    # Clear selectivo
    print("\n--- Clear Selectivo ---")
    print(f"Active slots antes: {wm._count_active_slots(wm.w)}")
    wm.clear_slot(0)
    wm.clear_slot(1)
    print(f"Active slots después de clear 2 slots: {wm._count_active_slots(wm.w)}")
    
    # Estadísticas
    print("\n--- Estadísticas ---")
    stats = wm.get_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")
    
    print("\n✅ Working Memory funcional - PFC activa")