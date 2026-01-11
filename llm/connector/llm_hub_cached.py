"""
Context Caching + Multi-Head Latent Attention (MLA)
Inspirado en Kimi K2
- Cachea prefijos de contexto para ahorrar 90% de costos
- MLA reduce memoria KV para contextos largos (256K tokens)
"""

import hashlib
import asyncio
import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from pathlib import Path


@dataclass
class CachedContext:
    """Contexto cacheado"""
    prefix_hash: str
    prefix_text: str
    embedding: Optional[torch.Tensor]  # KV cache comprimido
    token_count: int
    created_at: datetime
    access_count: int
    last_accessed: datetime
    metadata: Dict[str, Any]


class ContextCache:
    """
    Sistema de cacheo de contexto estilo Kimi K2
    Cachea prefijos comunes (system prompts, KG context, etc.)
    """
    
    def __init__(self, max_cache_size: int = 100, ttl_hours: int = 24):
        self.cache: Dict[str, CachedContext] = {}
        self.max_cache_size = max_cache_size
        self.ttl = timedelta(hours=ttl_hours)
        
        # Estadísticas
        self.stats = {
            "hits": 0,
            "misses": 0,
            "total_tokens_saved": 0,
            "cost_saved_usd": 0.0
        }
    
    def get(self, prefix_text: str) -> Optional[CachedContext]:
        """
        Busca contexto en cache
        
        Returns:
            CachedContext si existe y es válido, None si no
        """
        prefix_hash = self._compute_hash(prefix_text)
        
        if prefix_hash in self.cache:
            cached = self.cache[prefix_hash]
            
            # Verificar TTL
            if datetime.now() - cached.created_at > self.ttl:
                # Expirado - eliminar
                del self.cache[prefix_hash]
                self.stats["misses"] += 1
                return None
            
            # Hit - actualizar estadísticas
            cached.access_count += 1
            cached.last_accessed = datetime.now()
            self.stats["hits"] += 1
            self.stats["total_tokens_saved"] += cached.token_count
            
            # Estimar ahorro de costo (Claude Sonnet 4: ~$3/M tokens input)
            cost_saved = (cached.token_count / 1_000_000) * 3.0
            self.stats["cost_saved_usd"] += cost_saved
            
            return cached
        
        self.stats["misses"] += 1
        return None
    
    def put(self, prefix_text: str, 
            embedding: Optional[torch.Tensor] = None,
            token_count: int = 0,
            metadata: Dict[str, Any] = None) -> str:
        """
        Guarda contexto en cache
        
        Returns:
            Hash del prefijo cacheado
        """
        prefix_hash = self._compute_hash(prefix_text)
        
        # Verificar límite de cache
        if len(self.cache) >= self.max_cache_size:
            self._evict_lru()
        
        # Guardar
        self.cache[prefix_hash] = CachedContext(
            prefix_hash=prefix_hash,
            prefix_text=prefix_text,
            embedding=embedding,
            token_count=token_count,
            created_at=datetime.now(),
            access_count=0,
            last_accessed=datetime.now(),
            metadata=metadata or {}
        )
        
        return prefix_hash
    
    def _compute_hash(self, text: str) -> str:
        """Calcula hash SHA256 del texto"""
        return hashlib.sha256(text.encode()).hexdigest()[:16]
    
    def _evict_lru(self):
        """Elimina entrada menos recientemente usada"""
        if not self.cache:
            return
        
        # Encontrar LRU
        lru_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].last_accessed
        )
        
        del self.cache[lru_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de uso"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0.0
        
        return {
            "hit_rate": hit_rate,
            "total_hits": self.stats["hits"],
            "total_misses": self.stats["misses"],
            "tokens_saved": self.stats["total_tokens_saved"],
            "cost_saved_usd": self.stats["cost_saved_usd"],
            "cache_size": len(self.cache),
            "cache_capacity": self.max_cache_size
        }
    
    def clear(self):
        """Limpia el cache completo"""
        self.cache.clear()
        print("🗑️  Cache limpiado")


class MultiHeadLatentAttention(nn.Module):
    """
    Multi-Head Latent Attention (MLA) estilo Kimi K2
    Comprime KV cache a espacio latente de baja dimensión
    Permite contextos de 256K tokens sin explotar VRAM
    """
    
    def __init__(self, 
                 d_model: int = 512,
                 num_heads: int = 8,
                 latent_dim: int = 128,
                 dropout: float = 0.1):
        super().__init__()
        
        self.d_model = d_model
        self.num_heads = num_heads
        self.latent_dim = latent_dim
        self.d_k = d_model // num_heads
        
        # Proyecciones estándar
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        
        # Proyecciones a/desde espacio latente
        self.k_compress = nn.Linear(d_model, latent_dim)
        self.v_compress = nn.Linear(d_model, latent_dim)
        self.k_decompress = nn.Linear(latent_dim, d_model)
        self.v_decompress = nn.Linear(latent_dim, d_model)
        
        self.dropout = nn.Dropout(dropout)
        self.out_proj = nn.Linear(d_model, d_model)
        
        # KV cache (latente)
        self.kv_cache_enabled = False
        self.cached_k_latent = None
        self.cached_v_latent = None
    
    def enable_kv_cache(self):
        """Habilita cacheo de K,V en espacio latente"""
        self.kv_cache_enabled = True
        self.cached_k_latent = None
        self.cached_v_latent = None
    
    def clear_kv_cache(self):
        """Limpia el cache KV"""
        self.cached_k_latent = None
        self.cached_v_latent = None
    
    def forward(self, 
                query: torch.Tensor,
                key: torch.Tensor,
                value: torch.Tensor,
                mask: Optional[torch.Tensor] = None,
                use_cache: bool = False) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass con atención latente
        
        Args:
            query: [batch, seq_len_q, d_model]
            key: [batch, seq_len_k, d_model]
            value: [batch, seq_len_v, d_model]
            mask: Máscara de atención
            use_cache: Si True, usa/actualiza KV cache
            
        Returns:
            (output, metadata)
        """
        batch_size = query.size(0)
        seq_len_q = query.size(1)
        seq_len_k = key.size(1)
        
        # 1. Proyectar Q, K, V
        Q = self.W_q(query)  # [batch, seq_q, d_model]
        K = self.W_k(key)    # [batch, seq_k, d_model]
        V = self.W_v(value)  # [batch, seq_v, d_model]
        
        # 2. Comprimir K y V a espacio latente
        if use_cache and self.kv_cache_enabled:
            # Si hay cache, solo comprimir nuevos tokens
            if self.cached_k_latent is not None:
                # Concatenar con cache existente
                k_latent_new = self.k_compress(K)
                v_latent_new = self.v_compress(V)
                
                K_latent = torch.cat([self.cached_k_latent, k_latent_new], dim=1)
                V_latent = torch.cat([self.cached_v_latent, v_latent_new], dim=1)
                
                # Actualizar cache
                self.cached_k_latent = K_latent
                self.cached_v_latent = V_latent
            else:
                # Primera vez - crear cache
                K_latent = self.k_compress(K)
                V_latent = self.v_compress(V)
                
                self.cached_k_latent = K_latent
                self.cached_v_latent = V_latent
        else:
            # Sin cache - comprimir normalmente
            K_latent = self.k_compress(K)
            V_latent = self.v_compress(V)
        
        # 3. Multi-head split
        Q = Q.view(batch_size, seq_len_q, self.num_heads, self.d_k).transpose(1, 2)
        # K,V están en espacio latente - necesitamos descomprimir
        K_full = self.k_decompress(K_latent)
        V_full = self.v_decompress(V_latent)
        
        seq_len_k_full = K_full.size(1)
        
        K_full = K_full.view(batch_size, seq_len_k_full, self.num_heads, self.d_k).transpose(1, 2)
        V_full = V_full.view(batch_size, seq_len_k_full, self.num_heads, self.d_k).transpose(1, 2)
        
        # 4. Scaled Dot-Product Attention
        scores = torch.matmul(Q, K_full.transpose(-2, -1)) / np.sqrt(self.d_k)
        
        if mask is not None:
            scores = scores.masked_fill(mask == 0, float('-inf'))
        
        attn_weights = torch.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        # 5. Apply attention to values
        attn_output = torch.matmul(attn_weights, V_full)
        
        # 6. Concatenate heads
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, seq_len_q, self.d_model)
        
        # 7. Output projection
        output = self.out_proj(attn_output)
        
        # Metadata
        compression_ratio = self.d_model / self.latent_dim
        memory_saved = (seq_len_k * self.d_model - seq_len_k * self.latent_dim) * batch_size
        
        metadata = {
            "compression_ratio": compression_ratio,
            "latent_dim": self.latent_dim,
            "original_kv_size": seq_len_k * self.d_model,
            "compressed_kv_size": seq_len_k * self.latent_dim,
            "memory_saved_elements": memory_saved,
            "cache_used": use_cache and self.cached_k_latent is not None
        }
        
        return output, metadata


class CorticalAttentionMLAIntegration:
    """
    Integración de MLA con CorticalAttention de AMA-Intent
    Mejora para manejar contextos muy largos (256K tokens)
    """
    
    def __init__(self, dim: int = 512, beta: float = 0.5, latent_dim: int = 128):
        self.dim = dim
        self.beta = beta
        
        # MLA para atención eficiente
        self.mla = MultiHeadLatentAttention(
            d_model=dim,
            num_heads=8,
            latent_dim=latent_dim
        )
        
        # Habilitar cache por defecto
        self.mla.enable_kv_cache()
    
    def compute_attention_long_context(self, 
                                      delta: np.ndarray,
                                      context: np.ndarray,
                                      modulation: Optional[np.ndarray] = None) -> Tuple[np.ndarray, Dict]:
        """
        Compute attention sobre contextos muy largos usando MLA
        
        Args:
            delta: Error de predicción (sorpresa)
            context: Contexto completo (puede ser 256K tokens)
            modulation: Modulación opcional
            
        Returns:
            (alpha, metadata)
        """
        # Convertir a tensors
        delta_tensor = torch.from_numpy(delta).float().unsqueeze(0).unsqueeze(0)
        context_tensor = torch.from_numpy(context).float().unsqueeze(0)
        
        # Aplicar MLA
        with torch.no_grad():
            attn_output, mla_meta = self.mla(
                query=delta_tensor,
                key=context_tensor,
                value=context_tensor,
                use_cache=True
            )
        
        # Convertir de vuelta a numpy
        alpha = attn_output.squeeze().numpy()
        
        # Aplicar modulación si está presente
        if modulation is not None:
            alpha = alpha * modulation
        
        # Normalizar
        alpha = np.abs(alpha) ** self.beta
        if alpha.max() > 0:
            alpha = alpha / alpha.max()
        
        metadata = {
            "beta": self.beta,
            "mla_compression_ratio": mla_meta["compression_ratio"],
            "memory_saved": mla_meta["memory_saved_elements"],
            "cache_used": mla_meta["cache_used"],
            "context_length": len(context)
        }
        
        return alpha, metadata


class LLMHubWithCaching:
    """
    Versión mejorada de LLMHub con Context Caching
    Ahorro de 90% en costos para queries repetitivas
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers = {}  # Inicializar proveedores como antes
        
        # Context Cache
        self.context_cache = ContextCache(
            max_cache_size=config.get("cache_size", 100),
            ttl_hours=config.get("cache_ttl_hours", 24)
        )
        
        # Tokenizer simple (usar real en producción)
        self.avg_chars_per_token = 4
    
    async def analyze_with_caching(self, request, cache_prefix: bool = True):
        """
        Analiza código con cacheo de contexto
        
        Args:
            request: AnalysisRequest
            cache_prefix: Si True, intenta cachear el prefijo
            
        Returns:
            LLMResponse con metadata de cache
        """
        
        # 1. Extraer prefijo cacheable (system prompt + contexto estático)
        prefix, suffix = self._split_request(request)
        
        # 2. Buscar en cache
        cached_prefix = None
        if cache_prefix and prefix:
            cached_prefix = self.context_cache.get(prefix)
        
        # 3. Construir prompt
        if cached_prefix:
            # Cache HIT - solo enviar sufijo nuevo
            print(f"💨 Cache HIT - Ahorrando {cached_prefix.token_count} tokens")
            
            prompt = suffix  # Solo la parte nueva
            metadata_cache = {
                "cache_hit": True,
                "tokens_saved": cached_prefix.token_count,
                "cost_saved_usd": (cached_prefix.token_count / 1_000_000) * 3.0
            }
        else:
            # Cache MISS - enviar completo y cachear
            print(f"🔍 Cache MISS - Procesando contexto completo")
            
            prompt = prefix + "\n\n" + suffix if prefix else suffix
            
            # Estimar tokens del prefijo
            prefix_tokens = len(prefix) // self.avg_chars_per_token if prefix else 0
            
            # Guardar en cache para próxima vez
            if cache_prefix and prefix:
                self.context_cache.put(
                    prefix_text=prefix,
                    token_count=prefix_tokens,
                    metadata={"request_type": request.task}
                )
            
            metadata_cache = {
                "cache_hit": False,
                "tokens_saved": 0,
                "cost_saved_usd": 0.0
            }
        
        # 4. Ejecutar query (simplificado - usar LLM real)
        # response = await self._call_llm(prompt, request)
        
        # Simulación
        response = {
            "success": True,
            "content": "Análisis completado",
            "tokens_used": len(suffix) // self.avg_chars_per_token,
            "cache_metadata": metadata_cache
        }
        
        return response
    
    def _split_request(self, request) -> Tuple[str, str]:
        """
        Divide request en prefijo cacheable y sufijo nuevo
        
        Prefijo: system prompt + contexto estático (KG, reglas, etc.)
        Sufijo: código específico + query específica
        """
        
        # Prefijo típico (cacheable)
        prefix_parts = []
        
        # 1. System prompt (siempre igual)
        system_prompt = """Eres un experto revisor de código.
Analiza código Python siguiendo mejores prácticas de:
- Seguridad (OWASP Top 10)
- Rendimiento (complejidad algorítmica)
- Mantenibilidad (Clean Code)
- Testing (cobertura, edge cases)
"""
        prefix_parts.append(system_prompt)
        
        # 2. Contexto estático (ej: reglas del proyecto)
        if hasattr(request, 'context') and request.context:
            # Si el contexto es del KG u otro contexto estático, va al prefijo
            if "KNOWLEDGE GRAPH" in request.context or "PROJECT RULES" in request.context:
                prefix_parts.append(request.context)
        
        # 3. Sufijo (query específica + código)
        suffix = f"Tarea: {request.task}\n"
        if hasattr(request, 'code'):
            suffix += f"\nCódigo a analizar:\n```python\n{request.code}\n```"
        
        prefix = "\n\n".join(prefix_parts)
        
        return prefix, suffix
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Estadísticas de cache"""
        return self.context_cache.get_stats()


# Ejemplo de uso completo
async def demo_caching_and_mla():
    """Demostración de Context Caching + MLA"""
    
    print("=" * 60)
    print("DEMO: Context Caching + MLA Attention")
    print("=" * 60)
    
    # 1. Inicializar LLMHub con caching
    config = {
        "cache_size": 50,
        "cache_ttl_hours": 24
    }
    
    llm_hub = LLMHubWithCaching(config)
    
    # 2. Simular múltiples queries con mismo prefijo
    print("\n📊 Simulando 10 queries con mismo prefijo...")
    
    class DummyRequest:
        def __init__(self, code, task="review"):
            self.code = code
            self.task = task
            self.context = "KNOWLEDGE GRAPH: [contexto estático grande aquí...]"
    
    for i in range(10):
        request = DummyRequest(
            code=f"def function_{i}():\n    return {i} * 2",
            task="review"
        )
        
        response = await llm_hub.analyze_with_caching(request, cache_prefix=True)
        
        print(f"\nQuery {i+1}:")
        print(f"  Cache HIT: {response['cache_metadata']['cache_hit']}")
        print(f"  Tokens ahorrados: {response['cache_metadata']['tokens_saved']}")
        print(f"  Costo ahorrado: ${response['cache_metadata']['cost_saved_usd']:.4f}")
    
    # 3. Estadísticas finales
    stats = llm_hub.get_cache_stats()
    
    print(f"\n{'='*60}")
    print("📈 ESTADÍSTICAS FINALES DE CACHE")
    print(f"{'='*60}")
    print(f"Hit Rate: {stats['hit_rate']*100:.1f}%")
    print(f"Total Hits: {stats['total_hits']}")
    print(f"Total Misses: {stats['total_misses']}")
    print(f"Tokens Totales Ahorrados: {stats['tokens_saved']:,}")
    print(f"Costo Total Ahorrado: ${stats['cost_saved_usd']:.2f}")
    print(f"Cache Ocupado: {stats['cache_size']}/{stats['cache_capacity']}")
    
    # 4. Demo MLA
    print(f"\n{'='*60}")
    print("🧠 DEMO: Multi-Head Latent Attention")
    print(f"{'='*60}")
    
    cortical_mla = CorticalAttentionMLAIntegration(dim=512, latent_dim=128)
    
    # Simular contexto largo
    delta = np.random.randn(512)
    long_context = np.random.randn(100000, 512)  # 100K tokens simulados
    
    print(f"\nProcesando contexto de {len(long_context):,} tokens...")
    
    alpha, mla_meta = cortical_mla.compute_attention_long_context(delta, long_context)
    
    print(f"\n📉 Compresión MLA:")
    print(f"  Ratio de compresión: {mla_meta['compression_ratio']:.1f}x")
    print(f"  Memoria ahorrada: {mla_meta['memory_saved']:,} elementos")
    print(f"  Cache usado: {mla_meta['cache_used']}")
    print(f"  Longitud de contexto: {mla_meta['context_length']:,}")


if __name__ == "__main__":
    asyncio.run(demo_caching_and_mla())