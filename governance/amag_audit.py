# governance/amag_audit.py - AMA-G Auditor (Corteza Prefrontal Metacognitiva)
"""
Implementa AMA-G: Auditoría, Metacognición y Gobernanza.
Aₜ = Audit(zₜ, wₜ, Rₜ, aₜ, 𝓤ₜ, 𝓘ₜ)

Si Aₜ = FAIL → Revise(aₜ) o a_safe

Este módulo actúa como PFC: supervisa, verifica y corrige.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sys
import os

# Importar MUEDP v2 (asumiendo que está disponible)
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

class AuditResult(Enum):
    """Resultado de la auditoría"""
    PASS = "pass"           # Todo correcto, proceder
    WARNING = "warning"     # Alerta pero no bloqueo
    FAIL = "fail"          # Fallo crítico, no proceder
    REVISED = "revised"    # Acción revisada y corregida

@dataclass
class AuditReport:
    """Reporte de auditoría"""
    result: AuditResult
    confidence: float           # [0,1] Confianza en la decisión
    issues: List[str]           # Lista de problemas detectados
    metrics: Dict[str, float]   # Métricas de auditoría
    revised_action: Optional[np.ndarray]  # Acción corregida (si aplica)
    safe_action: Optional[np.ndarray]     # Acción segura de respaldo

@dataclass
class GovernanceThresholds:
    """Umbrales de gobernanza"""
    min_confidence: float = 0.4        # Confianza mínima para proceder
    max_surprise: float = 3.0          # Sorpresa máxima aceptable
    max_uncertainty: float = 2.0       # Incertidumbre máxima (KL)
    max_risk: float = 0.8              # Riesgo máximo (de MIEM)
    consistency_threshold: float = 0.7  # Consistencia mínima

class AMAGAuditor:
    """
    Auditor AMA-G: Corteza Prefrontal Metacognitiva.
    
    Funciones:
    1. Verificar consistencia interna
    2. Detectar contradicciones
    3. Evaluar confianza de la decisión
    4. Prevenir alucinaciones/errores
    5. Forzar modo seguro cuando sea necesario
    """
    
    def __init__(self, thresholds: Optional[GovernanceThresholds] = None):
        """
        Args:
            thresholds: umbrales de gobernanza
        """
        self.thresholds = thresholds or GovernanceThresholds()
        self.audit_history = []
        
        # Acción segura por defecto (no hacer nada)
        self.default_safe_action = None
        
        # Contadores
        self.total_audits = 0
        self.passes = 0
        self.warnings = 0
        self.fails = 0
        self.revisions = 0
    
    def audit(self,
              z: np.ndarray,                    # Estado cortical
              w: Optional[np.ndarray],          # Memoria de trabajo
              R: Optional[List],                # Memoria episódica recuperada
              action_candidate: Dict,           # Acción propuesta
              surprise: float,                  # 𝓤ₜ
              kl_divergence: Optional[float] = None  # 𝓘ₜ
              ) -> AuditReport:
        """
        Audita el sistema completo antes de ejecutar una acción.
        
        Args:
            z: estado latente
            w: memoria de trabajo
            R: episodios recuperados
            action_candidate: acción propuesta con metadata
            surprise: sorpresa actual (error predicción)
            kl_divergence: divergencia KL (cambio de creencias)
        
        Returns:
            AuditReport: resultado de la auditoría
        """
        self.total_audits += 1
        
        issues = []
        metrics = {}
        
        # === 1. VERIFICACIÓN DE SORPRESA ===
        metrics['surprise'] = surprise
        if surprise > self.thresholds.max_surprise:
            issues.append(f"Sorpresa excesiva: {surprise:.3f} > {self.thresholds.max_surprise}")
        
        # === 2. VERIFICACIÓN DE INCERTIDUMBRE ===
        if kl_divergence is not None:
            metrics['kl_divergence'] = kl_divergence
            if kl_divergence > self.thresholds.max_uncertainty:
                issues.append(f"Incertidumbre alta: KL={kl_divergence:.3f}")
        
        # === 3. VERIFICACIÓN DE RIESGO ===
        miem = action_candidate.get('miem', {})
        risk = miem.get('risk', 0.0)
        metrics['risk'] = risk
        
        if risk > self.thresholds.max_risk:
            issues.append(f"Riesgo excesivo: {risk:.3f} > {self.thresholds.max_risk}")
        
        # === 4. CONSISTENCIA INTERNA ===
        consistency = self._check_consistency(z, action_candidate)
        metrics['consistency'] = consistency
        
        if consistency < self.thresholds.consistency_threshold:
            issues.append(f"Inconsistencia detectada: {consistency:.3f}")
        
        # === 5. VERIFICACIÓN DE MAGNITUD ===
        action = action_candidate['action']
        action_magnitude = np.linalg.norm(action)
        metrics['action_magnitude'] = action_magnitude
        
        # Detectar acciones extremas
        if action_magnitude > 5.0:
            issues.append(f"Acción de magnitud extrema: {action_magnitude:.3f}")
        
        # === 6. CONFIANZA COMPUESTA ===
        confidence = self._compute_confidence(
            surprise=surprise,
            risk=risk,
            consistency=consistency,
            action_magnitude=action_magnitude
        )
        metrics['confidence'] = confidence
        
        # === 7. DECISIÓN DE AUDITORÍA ===
        result, revised_action = self._make_decision(
            issues=issues,
            confidence=confidence,
            action_candidate=action_candidate,
            metrics=metrics
        )
        
        # === 8. GENERAR REPORTE ===
        report = AuditReport(
            result=result,
            confidence=confidence,
            issues=issues,
            metrics=metrics,
            revised_action=revised_action,
            safe_action=self._get_safe_action(z)
        )
        
        # Actualizar contadores
        if result == AuditResult.PASS:
            self.passes += 1
        elif result == AuditResult.WARNING:
            self.warnings += 1
        elif result == AuditResult.FAIL:
            self.fails += 1
        elif result == AuditResult.REVISED:
            self.revisions += 1
        
        # Guardar en historial
        self.audit_history.append(report)
        if len(self.audit_history) > 1000:
            self.audit_history.pop(0)
        
        return report
    
    def _check_consistency(self, z: np.ndarray, action_candidate: Dict) -> float:
        """
        Verifica consistencia entre estado y acción propuesta.
        
        Consistencia alta = acción alineada con estado actual
        Consistencia baja = acción contradice el estado
        """
        action = action_candidate['action']
        
        # Proyección del estado en espacio de acciones (simplificado)
        # En producción: usar modelo forward
        
        # Heurística: magnitud relativa
        z_norm = np.linalg.norm(z) + 1e-9
        a_norm = np.linalg.norm(action) + 1e-9
        
        # Estados pequeños → acciones pequeñas
        # Estados grandes → acciones pueden ser grandes
        ratio = min(a_norm / z_norm, z_norm / a_norm)
        
        # Normalizar a [0, 1]
        consistency = np.exp(-abs(np.log(ratio + 1e-9)))
        
        return float(np.clip(consistency, 0.0, 1.0))
    
    def _compute_confidence(self,
                           surprise: float,
                           risk: float,
                           consistency: float,
                           action_magnitude: float) -> float:
        """
        Calcula confianza compuesta de la decisión.
        
        Alta confianza = baja sorpresa + bajo riesgo + alta consistencia + magnitud razonable
        """
        # Normalizar surprise [0, inf) -> [0, 1]
        surprise_norm = 1.0 - np.tanh(surprise / self.thresholds.max_surprise)
        
        # Risk ya está en [0, 1]
        safety = 1.0 - risk
        
        # Magnitude penalty
        magnitude_ok = 1.0 - np.tanh(action_magnitude / 5.0)
        
        # Combinación ponderada
        confidence = (
            0.3 * surprise_norm +
            0.3 * safety +
            0.3 * consistency +
            0.1 * magnitude_ok
        )
        
        return float(np.clip(confidence, 0.0, 1.0))
    
    def _make_decision(self,
                      issues: List[str],
                      confidence: float,
                      action_candidate: Dict,
                      metrics: Dict) -> Tuple[AuditResult, Optional[np.ndarray]]:
        """
        Toma decisión de auditoría basada en issues y confianza.
        
        Returns:
            (result, revised_action)
        """
        n_issues = len(issues)
        
        # Caso 1: Sin problemas y alta confianza → PASS
        if n_issues == 0 and confidence >= self.thresholds.min_confidence:
            return AuditResult.PASS, None
        
        # Caso 2: Pocos problemas y confianza aceptable → WARNING
        if n_issues <= 1 and confidence >= self.thresholds.min_confidence * 0.8:
            return AuditResult.WARNING, None
        
        # Caso 3: Problemas moderados → REVISED (intentar corregir)
        if n_issues <= 2 and confidence >= self.thresholds.min_confidence * 0.5:
            revised = self._revise_action(action_candidate, issues, metrics)
            return AuditResult.REVISED, revised
        
        # Caso 4: Problemas críticos → FAIL
        return AuditResult.FAIL, None
    
    def _revise_action(self,
                      action_candidate: Dict,
                      issues: List[str],
                      metrics: Dict) -> np.ndarray:
        """
        Revisa y corrige la acción propuesta.
        
        Estrategias:
        - Si riesgo alto → reducir magnitud
        - Si sorpresa alta → acción más conservadora
        - Si inconsistencia → ajustar dirección
        """
        action = action_candidate['action'].copy()
        
        # Estrategia 1: Reducir magnitud si hay riesgo
        if metrics.get('risk', 0) > self.thresholds.max_risk:
            scale = self.thresholds.max_risk / (metrics['risk'] + 1e-9)
            action = action * scale
        
        # Estrategia 2: Suavizar si alta sorpresa
        if metrics.get('surprise', 0) > self.thresholds.max_surprise:
            damping = 0.5
            action = action * damping
        
        # Estrategia 3: Clip extremos
        action = np.clip(action, -3.0, 3.0)
        
        return action
    
    def _get_safe_action(self, z: np.ndarray) -> np.ndarray:
        """
        Genera acción segura de respaldo.
        
        Por defecto: acción nula o mínima
        """
        if self.default_safe_action is not None:
            return self.default_safe_action
        
        # Acción conservadora: pequeño movimiento hacia estado nominal
        safe = -0.1 * z / (np.linalg.norm(z) + 1e-9)
        
        # Límite de magnitud
        return np.clip(safe, -0.5, 0.5)
    
    def get_statistics(self) -> Dict:
        """Retorna estadísticas de auditoría"""
        if self.total_audits == 0:
            return {}
        
        return {
            'total_audits': self.total_audits,
            'pass_rate': self.passes / self.total_audits,
            'warning_rate': self.warnings / self.total_audits,
            'fail_rate': self.fails / self.total_audits,
            'revision_rate': self.revisions / self.total_audits,
            'avg_confidence': np.mean([r.confidence for r in self.audit_history[-100:]])
        }
    
    def adapt_thresholds(self, performance_feedback: float):
        """
        Adapta umbrales basándose en feedback de rendimiento.
        
        Args:
            performance_feedback: [0,1] - qué tan bien funcionó el sistema
        """
        # Si el sistema está funcionando mal, ser más estrictos
        if performance_feedback < 0.5:
            self.thresholds.min_confidence = min(0.8, self.thresholds.min_confidence * 1.1)
            self.thresholds.max_risk = max(0.5, self.thresholds.max_risk * 0.9)
        
        # Si funciona bien, podemos relajar un poco
        elif performance_feedback > 0.8:
            self.thresholds.min_confidence = max(0.3, self.thresholds.min_confidence * 0.95)
            self.thresholds.max_risk = min(0.9, self.thresholds.max_risk * 1.05)


# =========================
# Testing
# =========================

if __name__ == "__main__":
    print("=== Test de AMA-G Auditor (Metacognición) ===\n")
    
    np.random.seed(42)
    
    # Crear auditor
    auditor = AMAGAuditor(
        thresholds=GovernanceThresholds(
            min_confidence=0.5,
            max_surprise=2.5,
            max_risk=0.7
        )
    )
    
    print("Umbrales de gobernanza:")
    print(f"  Confianza mínima: {auditor.thresholds.min_confidence}")
    print(f"  Sorpresa máxima: {auditor.thresholds.max_surprise}")
    print(f"  Riesgo máximo: {auditor.thresholds.max_risk}")
    
    # Estado simulado
    z = np.random.randn(32) * 0.5
    w = np.random.randn(16) * 0.3
    
    # Casos de prueba
    test_cases = [
        {
            'name': 'Acción segura',
            'action': np.random.randn(16) * 0.5,
            'miem': {'risk': 0.3, 'efficiency': 0.8},
            'surprise': 0.5
        },
        {
            'name': 'Acción arriesgada',
            'action': np.random.randn(16) * 2.0,
            'miem': {'risk': 0.85, 'efficiency': 0.9},
            'surprise': 1.5
        },
        {
            'name': 'Sorpresa alta',
            'action': np.random.randn(16) * 0.8,
            'miem': {'risk': 0.5, 'efficiency': 0.7},
            'surprise': 3.5
        }
    ]
    
    print("\n--- Auditorías ---")
    
    for test in test_cases:
        action_candidate = {
            'id': test['name'],
            'action': test['action'],
            'miem': test['miem']
        }
        
        report = auditor.audit(
            z=z,
            w=w,
            R=None,
            action_candidate=action_candidate,
            surprise=test['surprise'],
            kl_divergence=0.5
        )
        
        print(f"\n{test['name']}:")
        print(f"  Resultado: {report.result.value}")
        print(f"  Confianza: {report.confidence:.3f}")
        
        if report.issues:
            print(f"  Issues detectados:")
            for issue in report.issues:
                print(f"    - {issue}")
        
        if report.result == AuditResult.REVISED:
            print(f"  ✓ Acción revisada (magnitud: {np.linalg.norm(report.revised_action):.3f})")
        elif report.result == AuditResult.FAIL:
            print(f"  ✗ Acción bloqueada - usar acción segura")
    
    # Estadísticas
    print("\n--- Estadísticas de Auditoría ---")
    stats = auditor.get_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2%}" if 'rate' in key else f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")
    
    print("\n✅ Auditor AMA-G funcional - Corteza Prefrontal Metacognitiva activa")