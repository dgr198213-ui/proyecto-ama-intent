"""
MuonClip Optimizer - Inspirado en Kimi K2
Previene loss spikes en entrenamiento de modelos grandes
Implementación para AMA-Intent Reward Models y RLHF
"""

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn


@dataclass
class MuonClipConfig:
    """Configuración del optimizador MuonClip"""

    learning_rate: float = 1e-4
    betas: Tuple[float, float] = (0.9, 0.999)
    eps: float = 1e-8
    weight_decay: float = 0.01

    # QK-Clip específico
    qk_clip_enabled: bool = True
    tau: float = 100.0  # Umbral de saturación de logits
    eta: float = 0.95  # Factor de atenuación
    clip_frequency: int = 10  # Cada cuántos steps revisar

    # Muon específico
    momentum_orthogonalization: bool = True
    token_efficiency_target: float = 0.85

    # Monitoreo
    log_attention_stats: bool = True
    early_stop_on_spike: bool = True
    spike_threshold: float = 5.0  # Múltiplo de pérdida promedio


@dataclass
class TrainingStats:
    """Estadísticas de entrenamiento"""

    step: int
    loss: float
    max_attention_logit: float
    gradient_norm: float
    lr: float
    qk_clips_triggered: int
    attention_saturation: float


class AttentionMonitor:
    """
    Monitorea logits de atención para detectar saturación
    """

    def __init__(self, tau: float = 100.0):
        self.tau = tau
        self.history = []
        self.max_logit_per_layer = {}

    def compute_max_logit(
        self, attention_scores: torch.Tensor, layer_idx: int
    ) -> float:
        """
        Calcula el logit máximo de atención antes de softmax

        Args:
            attention_scores: [batch, heads, seq_len, seq_len]
            layer_idx: Índice de la capa
        """
        max_logit = attention_scores.abs().max().item()
        self.max_logit_per_layer[layer_idx] = max_logit

        return max_logit

    def get_global_max_logit(self) -> float:
        """Retorna el máximo logit entre todas las capas"""
        if not self.max_logit_per_layer:
            return 0.0
        return max(self.max_logit_per_layer.values())

    def compute_saturation_level(self) -> float:
        """
        Calcula nivel de saturación (0-1)
        1.0 = completamente saturado
        """
        max_logit = self.get_global_max_logit()
        saturation = min(1.0, max_logit / self.tau)
        return saturation

    def is_saturated(self) -> bool:
        """Verifica si la atención está saturada"""
        return self.get_global_max_logit() > self.tau

    def reset(self):
        """Resetea el monitor para el siguiente step"""
        self.max_logit_per_layer = {}


class QKClipper:
    """
    Implementa QK-Clip para prevenir explosión de logits de atención
    """

    def __init__(self, tau: float = 100.0, eta: float = 0.95):
        self.tau = tau
        self.eta = eta
        self.clips_triggered = 0

    def clip_weights(self, model: nn.Module, max_logit: float) -> bool:
        """
        Reescala matrices Q y K si el logit excede el umbral

        Args:
            model: Modelo con capas de atención
            max_logit: Máximo logit detectado

        Returns:
            True si se aplicó clipping
        """
        if max_logit <= self.tau:
            return False

        # Calcular factor de reescalado
        clip_factor = (self.tau / max_logit) ** self.eta

        # Aplicar a todas las capas de atención
        clipped = False
        for name, param in model.named_parameters():
            # Buscar matrices Q y K
            if any(x in name.lower() for x in ["query", "key", "q_proj", "k_proj"]):
                with torch.no_grad():
                    param.data *= clip_factor
                clipped = True

        if clipped:
            self.clips_triggered += 1

        return clipped


class MuonMomentum:
    """
    Componente Muon para actualización eficiente de parámetros
    Inspirado en métodos de momentum con ortogonalización
    """

    def __init__(self, beta1: float = 0.9, ortho_enabled: bool = True):
        self.beta1 = beta1
        self.ortho_enabled = ortho_enabled
        self.momentum_buffers = {}

    def update(
        self, param_name: str, gradient: torch.Tensor, step: int
    ) -> torch.Tensor:
        """
        Actualización Muon con momentum ortogonalizado
        """
        if param_name not in self.momentum_buffers:
            self.momentum_buffers[param_name] = torch.zeros_like(gradient)

        momentum = self.momentum_buffers[param_name]

        # Actualizar momentum
        momentum = self.beta1 * momentum + (1 - self.beta1) * gradient

        # Ortogonalización (si está habilitada)
        if self.ortho_enabled and gradient.dim() >= 2:
            momentum = self._orthogonalize(momentum)

        self.momentum_buffers[param_name] = momentum

        return momentum

    def _orthogonalize(self, tensor: torch.Tensor) -> torch.Tensor:
        """
        Ortogonalización de Gram-Schmidt para estabilizar actualizaciones
        """
        if tensor.dim() < 2:
            return tensor

        # Aplanar dimensiones extra
        original_shape = tensor.shape
        if tensor.dim() > 2:
            tensor = tensor.view(tensor.size(0), -1)

        # QR decomposition para ortogonalización
        try:
            q, r = torch.linalg.qr(tensor.T)
            result = q.T

            # Restaurar forma original
            if len(original_shape) > 2:
                result = result.view(original_shape)

            return result
        except:
            # Si falla, retornar original
            return tensor.view(original_shape)


class MuonClipOptimizer:
    """
    Optimizador MuonClip completo
    Combina eficiencia de Muon con estabilidad de QK-Clip
    """

    def __init__(self, model: nn.Module, config: MuonClipConfig):
        self.model = model
        self.config = config

        # Componentes
        self.attention_monitor = AttentionMonitor(tau=config.tau)
        self.qk_clipper = QKClipper(tau=config.tau, eta=config.eta)
        self.muon = MuonMomentum(
            beta1=config.betas[0], ortho_enabled=config.momentum_orthogonalization
        )

        # Estado
        self.step = 0
        self.loss_history = []
        self.stats_history = []

        # Optimizador base (AdamW para componentes que no son Q/K)
        self.base_optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=config.learning_rate,
            betas=config.betas,
            eps=config.eps,
            weight_decay=config.weight_decay,
        )

    def zero_grad(self):
        """Limpia gradientes"""
        self.base_optimizer.zero_grad()
        self.attention_monitor.reset()

    def step_with_monitoring(
        self,
        loss: torch.Tensor,
        attention_scores: Optional[Dict[int, torch.Tensor]] = None,
    ) -> TrainingStats:
        """
        Step de optimización con monitoreo de atención

        Args:
            loss: Pérdida del batch actual
            attention_scores: Dict {layer_idx: attention_scores_tensor}
        """
        self.step += 1
        current_loss = loss.item()
        self.loss_history.append(current_loss)

        # 1. Monitorear atención si está disponible
        max_logit = 0.0
        if attention_scores and self.config.qk_clip_enabled:
            for layer_idx, scores in attention_scores.items():
                logit = self.attention_monitor.compute_max_logit(scores, layer_idx)
                max_logit = max(max_logit, logit)

        # 2. Detectar spikes de pérdida
        if self._detect_loss_spike(current_loss):
            print(f"⚠️  LOSS SPIKE detectado en step {self.step}: {current_loss:.4f}")
            if self.config.early_stop_on_spike:
                raise RuntimeError("Loss spike detectado - deteniendo entrenamiento")

        # 3. Aplicar QK-Clip si es necesario
        qk_clipped = False
        if self.config.qk_clip_enabled and self.step % self.config.clip_frequency == 0:
            if self.attention_monitor.is_saturated():
                qk_clipped = self.qk_clipper.clip_weights(self.model, max_logit)
                if qk_clipped:
                    print(
                        f"✂️  QK-Clip aplicado en step {self.step} (max_logit={max_logit:.2f})"
                    )

        # 4. Calcular gradientes
        loss.backward()

        # 5. Actualizar parámetros con Muon para Q/K, AdamW para el resto
        gradient_norm = 0.0
        for name, param in self.model.named_parameters():
            if param.grad is None:
                continue

            # Q/K usan Muon
            if any(x in name.lower() for x in ["query", "key", "q_proj", "k_proj"]):
                momentum = self.muon.update(name, param.grad, self.step)
                with torch.no_grad():
                    param.data -= self.config.learning_rate * momentum

            gradient_norm += param.grad.norm().item() ** 2

        gradient_norm = math.sqrt(gradient_norm)

        # 6. Actualizar el resto con AdamW
        self.base_optimizer.step()

        # 7. Recopilar estadísticas
        stats = TrainingStats(
            step=self.step,
            loss=current_loss,
            max_attention_logit=max_logit,
            gradient_norm=gradient_norm,
            lr=self.config.learning_rate,
            qk_clips_triggered=self.qk_clipper.clips_triggered,
            attention_saturation=self.attention_monitor.compute_saturation_level(),
        )

        self.stats_history.append(stats)

        if self.config.log_attention_stats and self.step % 100 == 0:
            self._log_stats(stats)

        return stats

    def _detect_loss_spike(self, current_loss: float) -> bool:
        """Detecta spikes anormales en la pérdida"""
        if len(self.loss_history) < 10:
            return False

        # Pérdida promedio de los últimos 10 steps
        recent_avg = np.mean(self.loss_history[-10:])

        # Spike si excede threshold
        is_spike = current_loss > recent_avg * self.config.spike_threshold

        return is_spike

    def _log_stats(self, stats: TrainingStats):
        """Log de estadísticas de entrenamiento"""
        print(f"\n📊 Step {stats.step}:")
        print(f"  Loss: {stats.loss:.4f}")
        print(f"  Max Attention Logit: {stats.max_attention_logit:.2f}")
        print(f"  Gradient Norm: {stats.gradient_norm:.4f}")
        print(f"  Attention Saturation: {stats.attention_saturation*100:.1f}%")
        print(f"  QK-Clips: {stats.qk_clips_triggered}")

    def get_training_summary(self) -> Dict[str, Any]:
        """Resumen del entrenamiento"""
        if not self.stats_history:
            return {}

        losses = [s.loss for s in self.stats_history]
        max_logits = [s.max_attention_logit for s in self.stats_history]

        return {
            "total_steps": self.step,
            "final_loss": losses[-1] if losses else 0,
            "avg_loss": np.mean(losses),
            "min_loss": min(losses),
            "max_loss": max(losses),
            "loss_spikes_detected": sum(1 for l in losses if l > np.mean(losses) * 3),
            "max_attention_logit_peak": max(max_logits) if max_logits else 0,
            "qk_clips_total": self.qk_clipper.clips_triggered,
            "avg_saturation": np.mean(
                [s.attention_saturation for s in self.stats_history]
            ),
        }


class RewardModelTrainer:
    """
    Entrenador de Reward Models usando MuonClip
    Integración con AMA-Intent
    """

    def __init__(self, model: nn.Module, train_dataloader, val_dataloader=None):
        self.model = model
        self.train_dataloader = train_dataloader
        self.val_dataloader = val_dataloader

        # Configuración MuonClip
        self.config = MuonClipConfig(
            learning_rate=1e-4,
            tau=100.0,
            eta=0.95,
            qk_clip_enabled=True,
            early_stop_on_spike=True,
        )

        self.optimizer = MuonClipOptimizer(model, self.config)

    def train_epoch(self) -> Dict[str, float]:
        """Entrena una época completa"""
        self.model.train()
        epoch_losses = []

        for batch_idx, batch in enumerate(self.train_dataloader):
            self.optimizer.zero_grad()

            # Forward pass
            chosen_ids = batch["chosen_input_ids"]
            rejected_ids = batch["rejected_input_ids"]

            # Reward Model calcula scores
            chosen_reward = self.model(chosen_ids)
            rejected_reward = self.model(rejected_ids)

            # Bradley-Terry loss
            loss = -torch.log(torch.sigmoid(chosen_reward - rejected_reward)).mean()

            # Extraer attention scores si el modelo los expone
            attention_scores = self._extract_attention_scores()

            # Optimización con MuonClip
            stats = self.optimizer.step_with_monitoring(loss, attention_scores)

            epoch_losses.append(stats.loss)

            if batch_idx % 50 == 0:
                print(
                    f"Batch {batch_idx}, Loss: {stats.loss:.4f}, "
                    f"Saturation: {stats.attention_saturation*100:.1f}%"
                )

        return {"avg_loss": np.mean(epoch_losses), "final_loss": epoch_losses[-1]}

    def _extract_attention_scores(self) -> Optional[Dict[int, torch.Tensor]]:
        """
        Extrae attention scores del modelo
        Requiere que el modelo exponga estos valores
        """
        # Implementación específica según arquitectura
        # Por ahora retorna None
        return None

    def train(self, num_epochs: int = 3):
        """Entrenamiento completo"""
        print(f"🎯 Iniciando entrenamiento con MuonClip")
        print(f"Configuración: tau={self.config.tau}, eta={self.config.eta}")

        for epoch in range(num_epochs):
            print(f"\n{'='*60}")
            print(f"Época {epoch + 1}/{num_epochs}")
            print(f"{'='*60}")

            epoch_metrics = self.train_epoch()

            print(f"\n✅ Época {epoch + 1} completada")
            print(f"   Pérdida promedio: {epoch_metrics['avg_loss']:.4f}")

            # Validación si está disponible
            if self.val_dataloader:
                val_metrics = self.validate()
                print(f"   Pérdida validación: {val_metrics['avg_loss']:.4f}")

        # Resumen final
        summary = self.optimizer.get_training_summary()
        print(f"\n{'='*60}")
        print("📊 RESUMEN DEL ENTRENAMIENTO")
        print(f"{'='*60}")
        print(f"Total steps: {summary['total_steps']}")
        print(f"Pérdida final: {summary['final_loss']:.4f}")
        print(f"Loss spikes detectados: {summary['loss_spikes_detected']}")
        print(f"QK-Clips aplicados: {summary['qk_clips_total']}")
        print(
            f"✅ ZERO LOSS SPIKES FATALES"
            if summary["loss_spikes_detected"] == 0
            else "⚠️  Spikes detectados"
        )

    def validate(self) -> Dict[str, float]:
        """Validación del modelo"""
        self.model.eval()
        val_losses = []

        with torch.no_grad():
            for batch in self.val_dataloader:
                chosen_reward = self.model(batch["chosen_input_ids"])
                rejected_reward = self.model(batch["rejected_input_ids"])

                loss = -torch.log(torch.sigmoid(chosen_reward - rejected_reward)).mean()
                val_losses.append(loss.item())

        return {"avg_loss": np.mean(val_losses)}


# Ejemplo de uso
if __name__ == "__main__":
    # Modelo dummy para demostración
    class DummyRewardModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.transformer = nn.TransformerEncoder(
                nn.TransformerEncoderLayer(d_model=512, nhead=8), num_layers=6
            )
            self.value_head = nn.Linear(512, 1)

        def forward(self, input_ids):
            # Dummy forward
            x = torch.randn(input_ids.size(0), 128, 512)
            x = self.transformer(x)
            return self.value_head(x[:, 0, :]).squeeze()

    # Crear modelo y entrenador
    model = DummyRewardModel()

    # Dataset dummy
    class DummyDataset:
        def __iter__(self):
            for _ in range(100):
                yield {
                    "chosen_input_ids": torch.randint(0, 1000, (8, 128)),
                    "rejected_input_ids": torch.randint(0, 1000, (8, 128)),
                }

        def __len__(self):
            return 100

    train_loader = DummyDataset()

    # Entrenar con MuonClip
    trainer = RewardModelTrainer(model, train_loader)
    trainer.train(num_epochs=2)
