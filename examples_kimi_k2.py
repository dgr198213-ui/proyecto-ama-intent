"""
Ejemplos de Uso - Integración Kimi K2 en AMA-Intent

Este archivo contiene ejemplos prácticos de cómo usar cada componente
de la integración Kimi K2 en el sistema AMA-Intent.
"""

import asyncio
import torch
import torch.nn as nn
from pathlib import Path


# ============================================================================
# Ejemplo 1: MuonClip Optimizer - Entrenamiento Estable
# ============================================================================

def example_muonclip_training():
    """
    Ejemplo de entrenamiento de un Reward Model usando MuonClip
    para prevenir loss spikes
    """
    print("\n" + "="*60)
    print("Ejemplo 1: MuonClip Optimizer")
    print("="*60)
    
    from training.optimizers import MuonClipOptimizer, MuonClipConfig
    
    # Modelo simple de ejemplo
    class SimpleRewardModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc1 = nn.Linear(512, 256)
            self.fc2 = nn.Linear(256, 1)
        
        def forward(self, x):
            x = torch.relu(self.fc1(x))
            return self.fc2(x)
    
    # Configuración del optimizador
    config = MuonClipConfig(
        learning_rate=1e-4,
        tau=100.0,              # Umbral de saturación de logits
        eta=0.95,               # Factor de atenuación
        qk_clip_enabled=True,   # Habilitar QK-Clip
        early_stop_on_spike=True,
        spike_threshold=5.0
    )
    
    # Crear modelo y optimizador
    model = SimpleRewardModel()
    optimizer = MuonClipOptimizer(model, config)
    
    # Simular entrenamiento
    print("\n🚀 Iniciando entrenamiento con MuonClip...")
    for step in range(10):
        # Datos sintéticos
        x = torch.randn(8, 512)
        target = torch.randn(8, 1)
        
        # Forward pass
        output = model(x)
        loss = nn.MSELoss()(output, target)
        
        # Backward y step con monitoreo
        optimizer.zero_grad()
        stats = optimizer.step_with_monitoring(loss)
        
        if step % 5 == 0:
            print(f"Step {stats.step}: Loss={stats.loss:.4f}, "
                  f"GradNorm={stats.gradient_norm:.4f}, "
                  f"QK Clips={stats.qk_clips_triggered}")
    
    print("✅ Entrenamiento completado sin loss spikes")


# ============================================================================
# Ejemplo 2: Long Horizon Agent - Tarea de 300 Pasos
# ============================================================================

async def example_long_horizon_agent():
    """
    Ejemplo de uso del Long Horizon Agent para una tarea compleja
    """
    print("\n" + "="*60)
    print("Ejemplo 2: Long Horizon Agent")
    print("="*60)
    
    from agents.long_horizon import LongHorizonAgent
    
    # Nota: En producción, usar LLMHub real
    class MockLLMHub:
        async def generate(self, prompt):
            return "Análisis completado"
    
    # Inicializar agente
    llm_hub = MockLLMHub()
    agent = LongHorizonAgent(
        llm_hub=llm_hub,
        kg=None,  # Knowledge Graph opcional
        dmd=None,  # Decision Matrix opcional
        auditor=None  # Auditor opcional
    )
    
    # Ejecutar tarea de largo horizonte
    print("\n🚀 Ejecutando tarea compleja de 50 pasos...")
    result = await agent.execute_long_task(
        user_goal="Analizar proyecto completo y generar informe de calidad",
        max_steps=50,
        checkpoint_interval=10
    )
    
    print(f"\n✅ Tarea completada:")
    print(f"  • Pasos totales: {result.get('total_steps', 'N/A')}")
    print(f"  • Tasa de éxito: {result.get('success_rate', 0)*100:.1f}%")
    print(f"  • Goal drift detectado: {result.get('goal_drift_detected', False)}")


# ============================================================================
# Ejemplo 3: Agentic Data Synthesizer - Generación de Trayectorias
# ============================================================================

async def example_data_synthesizer():
    """
    Ejemplo de generación de trayectorias sintéticas para entrenar
    Reward Models usando RLVR
    """
    print("\n" + "="*60)
    print("Ejemplo 3: Agentic Data Synthesizer")
    print("="*60)
    
    from ama_data.synthesis import AgenticDataSynthesizer, BugType
    
    # Nota: En producción, usar LLMHub real
    class MockLLMHub:
        async def generate(self, prompt):
            return "def fixed_function(): pass"
    
    # Inicializar synthesizer
    llm_hub = MockLLMHub()
    synthesizer = AgenticDataSynthesizer(llm_hub=llm_hub, kg=None)
    
    # Generar trayectorias sintéticas
    print("\n🚀 Generando trayectorias sintéticas...")
    trajectories = await synthesizer.generate_trajectories(
        num_trajectories=10,
        variants_per_bug=3
    )
    
    print(f"\n✅ Generadas {len(trajectories)} trayectorias")
    
    # Convertir a pares de preferencias
    pairs = synthesizer.convert_to_preference_pairs(trajectories)
    print(f"✅ Creados {len(pairs)} pares de preferencias")
    
    # Guardar dataset
    output_path = Path("/tmp/preference_dataset.json")
    synthesizer.save_dataset(pairs, output_path)
    print(f"✅ Dataset guardado en: {output_path}")


# ============================================================================
# Ejemplo 4: Context Caching + MLA - Reducción de Costos
# ============================================================================

def example_context_caching():
    """
    Ejemplo de uso de Context Caching para reducir costos de LLM
    """
    print("\n" + "="*60)
    print("Ejemplo 4: Context Caching + MLA")
    print("="*60)
    
    from llm.connector import ContextCache, MultiHeadLatentAttention
    
    # Inicializar cache
    cache = ContextCache(max_cache_size=100, ttl_hours=24)
    
    # Prefijo común (system prompt + contexto estático)
    common_prefix = """
    Eres un asistente de código experto.
    Conoces Python, JavaScript y arquitecturas de software.
    Tu objetivo es ayudar a analizar y mejorar código.
    """
    
    print("\n🚀 Simulando queries con caching...")
    
    # Primera query (MISS)
    cached = cache.get(common_prefix)
    if cached is None:
        print("❌ Cache MISS - Procesando prefijo completo")
        cache.put(common_prefix, token_count=1000)
    
    # Segunda query (HIT)
    cached = cache.get(common_prefix)
    if cached is not None:
        print("✅ Cache HIT - Ahorro de 1000 tokens")
    
    # Estadísticas
    stats = cache.get_stats()
    print(f"\n📊 Estadísticas del cache:")
    print(f"  • Hit Rate: {stats['hit_rate']*100:.1f}%")
    print(f"  • Tokens ahorrados: {stats['tokens_saved']:,}")
    print(f"  • Costo ahorrado: ${stats['cost_saved_usd']:.4f}")
    
    # MLA Attention
    print("\n🧠 Multi-Head Latent Attention:")
    mla = MultiHeadLatentAttention(
        d_model=512,
        num_heads=8,
        latent_dim=128  # Compresión 4x
    )
    
    # Simular atención sobre contexto largo
    batch_size = 2
    seq_len = 1000  # 1000 tokens
    x = torch.randn(batch_size, seq_len, 512)
    
    output, metadata = mla(x, x, x)
    
    print(f"  • Compresión KV: {metadata['compression_ratio']:.1f}x")
    print(f"  • Memoria ahorrada: {metadata['memory_saved_elements']:,} elementos")
    print(f"  • Cache usado: {metadata['cache_used']}")


# ============================================================================
# Ejecutar Todos los Ejemplos
# ============================================================================

def main():
    """Ejecuta todos los ejemplos"""
    print("\n" + "="*60)
    print("AMA-Intent - Ejemplos de Integración Kimi K2")
    print("="*60)
    
    # Ejemplo 1: MuonClip (síncrono)
    example_muonclip_training()
    
    # Ejemplo 4: Context Caching (síncrono)
    example_context_caching()
    
    # Ejemplos asíncronos
    print("\n🔄 Ejecutando ejemplos asíncronos...")
    asyncio.run(example_long_horizon_agent())
    asyncio.run(example_data_synthesizer())
    
    print("\n" + "="*60)
    print("✅ Todos los ejemplos completados exitosamente")
    print("="*60)


if __name__ == "__main__":
    main()
