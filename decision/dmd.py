# decision/dmd.py - Decisión Matricial Determinista
"""
Implementa DMD (Decisión Matricial Determinista) para selección de acciones.
aₜ = DMD({Qₜ(a)}, restricciones, 𝓥ₜ)

Selecciona la acción óptima considerando múltiples criterios ponderados
y restricciones hard/soft.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ConstraintType(Enum):
    """Tipos de restricciones"""
    HARD = "hard"      # Violación = acción inválida
    SOFT = "soft"      # Violación = penalización
    PREFERENCE = "pref"  # No vinculante

@dataclass
class Constraint:
    """Restricción sobre acciones"""
    name: str
    type: ConstraintType
    check_fn: callable  # Función que retorna bool o float [0,1]
    penalty_weight: float = 1.0
    
@dataclass
class DecisionCriteria:
    """Criterios de decisión ponderados"""
    Q_value: float = 1.0        # Valor Q
    efficiency: float = 0.3     # Eficiencia (MIEM)
    safety: float = 0.5         # Seguridad (1 - riesgo)
    modularity: float = 0.2     # Modularidad
    
@dataclass
class DMDResult:
    """Resultado de la decisión"""
    selected_action_id: str
    selected_action: np.ndarray
    score: float
    criteria_scores: Dict[str, float]
    constraint_violations: List[str]
    alternatives: List[Tuple[str, float]]  # Top-K alternativas

class DecisionMatrixDeterministic:
    """
    Motor de Decisión Matricial Determinista.
    
    Implementa selección multi-criterio con restricciones:
    1. Filtra acciones por restricciones HARD
    2. Construye matriz de criterios
    3. Aplica ponderaciones 𝓥ₜ
    4. Aplica penalizaciones por restricciones SOFT
    5. Selecciona acción con mayor score
    """
    
    def __init__(self, 
                 criteria: Optional[DecisionCriteria] = None):
        """
        Args:
            criteria: ponderaciones de criterios de decisión
        """
        self.criteria = criteria or DecisionCriteria()
        self.decision_history = []
        
    def decide(self,
               action_candidates: List[Dict],
               constraints: Optional[List[Constraint]] = None,
               criteria_override: Optional[DecisionCriteria] = None,
               return_top_k: int = 3) -> DMDResult:
        """
        Selecciona la mejor acción usando DMD.
        
        Args:
            action_candidates: lista de dicts con:
                - 'id': identificador
                - 'action': np.ndarray
                - 'Q_value': float
                - 'miem': Dict con efficiency, risk, modularity
            constraints: lista de restricciones
            criteria_override: ponderaciones alternativas
            return_top_k: número de alternativas a retornar
        
        Returns:
            DMDResult: decisión y análisis
        """
        if not action_candidates:
            raise ValueError("No hay acciones candidatas")
        
        # Usar criterios override si se proporcionan
        criteria = criteria_override or self.criteria
        
        # 1. FILTRADO HARD: Eliminar acciones que violan restricciones duras
        valid_candidates = self._filter_hard_constraints(
            action_candidates, 
            constraints or []
        )
        
        if not valid_candidates:
            raise ValueError("Ninguna acción cumple las restricciones HARD")
        
        # 2. CONSTRUCCIÓN DE MATRIZ DE CRITERIOS
        # Cada fila = acción, cada columna = criterio
        decision_matrix = self._build_decision_matrix(valid_candidates, criteria)
        
        # 3. PENALIZACIONES SOFT
        penalties = self._compute_soft_penalties(
            valid_candidates,
            constraints or []
        )
        
        # 4. SCORE TOTAL
        # S(a) = Σ wᵢ·criterioᵢ(a) - penalizaciones
        scores = decision_matrix @ self._criteria_to_weights(criteria) - penalties
        
        # 5. SELECCIÓN
        best_idx = np.argmax(scores)
        best_candidate = valid_candidates[best_idx]
        
        # 6. ANÁLISIS
        top_k_indices = np.argsort(scores)[::-1][:return_top_k]
        alternatives = [
            (valid_candidates[i]['id'], float(scores[i])) 
            for i in top_k_indices[1:]  # Excluir la mejor
        ]
        
        # Desglose de scores por criterio
        criteria_scores = {
            'Q_value': float(decision_matrix[best_idx, 0]),
            'efficiency': float(decision_matrix[best_idx, 1]),
            'safety': float(decision_matrix[best_idx, 2]),
            'modularity': float(decision_matrix[best_idx, 3]),
            'penalty': float(penalties[best_idx])
        }
        
        # Violaciones de restricciones soft
        violations = self._get_violations(best_candidate, constraints or [])
        
        result = DMDResult(
            selected_action_id=best_candidate['id'],
            selected_action=best_candidate['action'],
            score=float(scores[best_idx]),
            criteria_scores=criteria_scores,
            constraint_violations=violations,
            alternatives=alternatives
        )
        
        # Guardar en historial
        self.decision_history.append({
            'result': result,
            'n_candidates': len(action_candidates),
            'n_valid': len(valid_candidates)
        })
        
        return result
    
    def _filter_hard_constraints(self,
                                 candidates: List[Dict],
                                 constraints: List[Constraint]) -> List[Dict]:
        """Filtra acciones que violan restricciones HARD"""
        valid = []
        
        for candidate in candidates:
            is_valid = True
            
            for constraint in constraints:
                if constraint.type == ConstraintType.HARD:
                    if not constraint.check_fn(candidate):
                        is_valid = False
                        break
            
            if is_valid:
                valid.append(candidate)
        
        return valid
    
    def _build_decision_matrix(self,
                               candidates: List[Dict],
                               criteria: DecisionCriteria) -> np.ndarray:
        """
        Construye matriz de decisión.
        Filas = acciones, Columnas = [Q, efficiency, safety, modularity]
        """
        n = len(candidates)
        matrix = np.zeros((n, 4))
        
        for i, candidate in enumerate(candidates):
            # Criterio 1: Q-value
            matrix[i, 0] = candidate.get('Q_value', 0.0)
            
            # Criterio 2: Eficiencia (de MIEM)
            miem = candidate.get('miem', {})
            matrix[i, 1] = miem.get('efficiency', 0.0)
            
            # Criterio 3: Seguridad (1 - riesgo)
            matrix[i, 2] = 1.0 - miem.get('risk', 0.0)
            
            # Criterio 4: Modularidad
            matrix[i, 3] = miem.get('modularity', 0.0)
        
        # Normalizar cada columna a [0, 1]
        for j in range(4):
            col = matrix[:, j]
            col_min = np.min(col)
            col_max = np.max(col)
            if col_max - col_min > 1e-9:
                matrix[:, j] = (col - col_min) / (col_max - col_min)
        
        return matrix
    
    def _criteria_to_weights(self, criteria: DecisionCriteria) -> np.ndarray:
        """Convierte criterios a vector de pesos normalizado"""
        weights = np.array([
            criteria.Q_value,
            criteria.efficiency,
            criteria.safety,
            criteria.modularity
        ])
        
        # Normalizar
        weight_sum = np.sum(weights)
        if weight_sum > 1e-9:
            weights = weights / weight_sum
        else:
            weights = np.ones(4) / 4.0
        
        return weights
    
    def _compute_soft_penalties(self,
                               candidates: List[Dict],
                               constraints: List[Constraint]) -> np.ndarray:
        """Calcula penalizaciones por violación de restricciones SOFT"""
        n = len(candidates)
        penalties = np.zeros(n)
        
        for i, candidate in enumerate(candidates):
            for constraint in constraints:
                if constraint.type == ConstraintType.SOFT:
                    # check_fn retorna [0,1]: 0=cumple, 1=viola
                    violation = constraint.check_fn(candidate)
                    if isinstance(violation, bool):
                        violation = 1.0 if violation else 0.0
                    
                    penalties[i] += constraint.penalty_weight * violation
        
        return penalties
    
    def _get_violations(self,
                       candidate: Dict,
                       constraints: List[Constraint]) -> List[str]:
        """Lista las restricciones violadas por una acción"""
        violations = []
        
        for constraint in constraints:
            if constraint.type == ConstraintType.SOFT:
                check = constraint.check_fn(candidate)
                violated = check > 0.5 if isinstance(check, float) else check
                
                if violated:
                    violations.append(constraint.name)
        
        return violations
    
    def adapt_criteria(self, 
                      performance_feedback: float,
                      learning_rate: float = 0.1):
        """
        Adapta ponderaciones de criterios basándose en feedback.
        
        Args:
            performance_feedback: [0,1] - qué tan bien fue la decisión
            learning_rate: tasa de adaptación
        """
        # Adaptación simple: si performance bajo, aumentar peso en seguridad
        if performance_feedback < 0.5:
            # Decisión no fue buena → priorizar seguridad
            delta_safety = learning_rate * (0.7 - self.criteria.safety)
            self.criteria.safety = min(1.0, self.criteria.safety + delta_safety)
            
            # Redistribuir otros pesos
            total = (self.criteria.Q_value + self.criteria.efficiency + 
                    self.criteria.safety + self.criteria.modularity)
            
            if total > 0:
                factor = (1.0 - self.criteria.safety) / (total - self.criteria.safety)
                self.criteria.Q_value *= factor
                self.criteria.efficiency *= factor
                self.criteria.modularity *= factor


# =========================
# Funciones de utilidad
# =========================

def create_safety_constraint(max_magnitude: float = 2.0) -> Constraint:
    """Crea restricción de seguridad basada en magnitud de acción"""
    def check(candidate: Dict) -> bool:
        action = candidate['action']
        return np.linalg.norm(action) <= max_magnitude
    
    return Constraint(
        name="max_magnitude",
        type=ConstraintType.HARD,
        check_fn=check
    )

def create_risk_constraint(max_risk: float = 0.8) -> Constraint:
    """Crea restricción de riesgo máximo"""
    def check(candidate: Dict) -> float:
        miem = candidate.get('miem', {})
        risk = miem.get('risk', 0.0)
        # Retorna violación [0,1]
        return max(0.0, risk - max_risk) / max_risk
    
    return Constraint(
        name="max_risk",
        type=ConstraintType.SOFT,
        check_fn=check,
        penalty_weight=2.0
    )


# =========================
# Testing
# =========================

if __name__ == "__main__":
    print("=== Test de DMD (Decisión Matricial Determinista) ===\n")
    
    np.random.seed(42)
    
    # Crear motor DMD
    dmd = DecisionMatrixDeterministic(
        criteria=DecisionCriteria(
            Q_value=1.0,
            efficiency=0.4,
            safety=0.6,
            modularity=0.2
        )
    )
    
    print("Criterios de decisión:")
    print(f"  Q-value: {dmd.criteria.Q_value}")
    print(f"  Efficiency: {dmd.criteria.efficiency}")
    print(f"  Safety: {dmd.criteria.safety}")
    print(f"  Modularity: {dmd.criteria.modularity}")
    
    # Candidatos de acción
    candidates = [
        {
            'id': 'conservative',
            'action': np.random.randn(16) * 0.3,
            'Q_value': 0.6,
            'miem': {
                'efficiency': 0.7,
                'risk': 0.2,
                'modularity': 0.8
            }
        },
        {
            'id': 'aggressive',
            'action': np.random.randn(16) * 2.5,
            'Q_value': 0.9,
            'miem': {
                'efficiency': 0.9,
                'risk': 0.85,
                'modularity': 0.4
            }
        },
        {
            'id': 'balanced',
            'action': np.random.randn(16) * 0.8,
            'Q_value': 0.75,
            'miem': {
                'efficiency': 0.75,
                'risk': 0.4,
                'modularity': 0.7
            }
        }
    ]
    
    # Restricciones
    constraints = [
        create_safety_constraint(max_magnitude=2.0),
        create_risk_constraint(max_risk=0.7)
    ]
    
    print("\n--- Restricciones ---")
    for c in constraints:
        print(f"  {c.name} ({c.type.value})")
    
    # Decisión
    print("\n--- Proceso de Decisión ---")
    result = dmd.decide(candidates, constraints, return_top_k=3)
    
    print(f"\n✓ Acción seleccionada: {result.selected_action_id}")
    print(f"  Score total: {result.score:.4f}")
    print(f"\nDesglose de criterios:")
    for criterion, value in result.criteria_scores.items():
        print(f"  {criterion}: {value:.4f}")
    
    if result.constraint_violations:
        print(f"\n⚠ Violaciones SOFT: {result.constraint_violations}")
    else:
        print(f"\n✓ Sin violaciones de restricciones")
    
    print(f"\nAlternativas consideradas:")
    for alt_id, alt_score in result.alternatives:
        print(f"  {alt_id}: {alt_score:.4f}")
    
    print("\n✅ Motor DMD funcional - Decisor de Ganglios Basales activo")
