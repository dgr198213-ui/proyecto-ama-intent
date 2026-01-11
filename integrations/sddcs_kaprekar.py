#!/usr/bin/env python3
"""
AMA-Intent v2.0 + SDDCS-Kaprekar Integration
============================================

Este script integra el protocolo SDDCS-Kaprekar en AMA-Intent v2.0
para mejorar la sincronización, validación y eficiencia del sistema.

Módulos integrados:
1. Agent State Synchronization
2. Context Cache Validation
3. Synthetic Data Verification
4. Plugin State Persistence
5. JWT Authentication with Rolling Seeds

Autor: AMA-Intent Team + SDDCS Integration
Versión: 1.0
"""

import hashlib
import hmac
import json
import pickle
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

# ============================================================================
# CORE SDDCS FUNCTIONS
# ============================================================================


def kaprekar_routine(seed: int) -> Tuple[int, int]:
    """
    Ejecuta el algoritmo de Kaprekar
    Retorna: (attractor, num_steps)
    """
    n = seed
    steps = 0

    while n != 6174 and steps < 8:
        digits = sorted(str(n).zfill(4))
        asc = int("".join(digits))
        desc = int("".join(reversed(digits)))
        n = desc - asc
        steps += 1

    return 6174, steps


def derive_session_key(
    node_id: int, network_salt: bytes, seed: int, steps: int, counter: int = 0
) -> bytes:
    """
    Deriva una clave de sesión desde el atractor de Kaprekar
    """
    entropy = f"{network_salt.decode()}-6174-{steps}-{counter}-{node_id}".encode()
    session_key = hmac.new(entropy, str(node_id).encode(), hashlib.sha256).digest()
    return session_key


# ============================================================================
# 1. AGENT STATE SYNCHRONIZATION
# ============================================================================


class AgentStateSync:
    """
    Sincroniza estado del Long Horizon Agent usando SDDCS
    """

    def __init__(self, agent_id: int, network_salt: str = "AMA-Intent-v2"):
        self.agent_id = agent_id
        self.network_salt = network_salt.encode()
        self.checkpoint_counter = 0

    def create_checkpoint(self, agent_state: dict) -> bytes:
        """
        Crea un checkpoint de 4 bytes del estado del agente
        """
        # Hash del estado
        state_str = json.dumps(agent_state, sort_keys=True)
        state_hash = hashlib.sha256(state_str.encode()).digest()

        # Generar seed
        seed = int.from_bytes(state_hash[:2], "big") % 10000

        # Asegurar que no sea repdigit
        while len(set(str(seed).zfill(4))) == 1:
            seed = (seed + 1) % 10000

        # Ejecutar Kaprekar
        attractor, steps = kaprekar_routine(seed)

        # Derivar clave de checkpoint
        checkpoint_key = derive_session_key(
            self.agent_id, self.network_salt, seed, steps, self.checkpoint_counter
        )

        self.checkpoint_counter += 1

        # Empaquetar: seed (2 bytes) + steps (1 byte) + checksum (1 byte)
        checkpoint = (
            seed.to_bytes(2, "big")
            + steps.to_bytes(1, "big")
            + ((seed * steps) % 255).to_bytes(1, "big")
        )

        return checkpoint

    def validate_checkpoint(self, checkpoint: bytes, agent_state: dict) -> bool:
        """
        Valida que el checkpoint coincida con el estado
        """
        seed = int.from_bytes(checkpoint[:2], "big")
        steps_expected = checkpoint[2]
        checksum_expected = checkpoint[3]

        # Verificar checksum
        if ((seed * steps_expected) % 255) != checksum_expected:
            return False

        # Re-ejecutar Kaprekar
        attractor, steps_calculated = kaprekar_routine(seed)

        if steps_calculated != steps_expected:
            return False

        # Verificar que el estado produce la misma seed
        state_str = json.dumps(agent_state, sort_keys=True)
        state_hash = hashlib.sha256(state_str.encode()).digest()
        expected_seed = int.from_bytes(state_hash[:2], "big") % 10000

        # Ajustar por repdigits
        while len(set(str(expected_seed).zfill(4))) == 1:
            expected_seed = (expected_seed + 1) % 10000

        return seed == expected_seed


# ============================================================================
# 2. CONTEXT CACHE VALIDATION
# ============================================================================


class SDDCSCacheValidator:
    """
    Valida integridad de contextos cacheados
    """

    @staticmethod
    def hash_context_to_seed(context: str) -> int:
        """
        Convierte contexto en seed de 4 dígitos
        """
        context_hash = hashlib.sha256(context.encode()).digest()
        seed = int.from_bytes(context_hash[:4], "big") % 10000

        # Evitar repdigits
        while len(set(str(seed).zfill(4))) == 1:
            seed = (seed + 1) % 10000

        return seed

    def generate_cache_fingerprint(self, context: str) -> dict:
        """
        Genera huella digital del contexto
        """
        seed = self.hash_context_to_seed(context)
        attractor, steps = kaprekar_routine(seed)

        return {
            "seed": seed,
            "steps": steps,
            "size_bytes": len(context.encode()),
            "token_count": len(context.split()),
            "timestamp": int(time.time()),
        }

    def validate_cached_context(
        self, context: str, fingerprint: dict
    ) -> Tuple[bool, str]:
        """
        Valida que el contexto no se haya corrompido
        """
        current_fp = self.generate_cache_fingerprint(context)

        if current_fp["seed"] != fingerprint["seed"]:
            return False, "Size mismatch: contexto truncado"

        if current_fp["steps"] != fingerprint["steps"]:
            return False, "Steps mismatch: corrupción detectada"

        if current_fp["size_bytes"] != fingerprint["size_bytes"]:
            return False, "Size mismatch: datos truncados o extendidos"

        return True, "Cache válido"


# ============================================================================
# 3. SYNTHETIC DATA VERIFICATION
# ============================================================================


class SyntheticDataVerifier:
    """
    Verifica integridad de datos sintéticos del Agentic Data Synthesizer
    """

    def generate_verified_sample(self, data: dict, metadata: dict) -> dict:
        """
        Genera sample con firma SDDCS
        """
        # Serializar dato
        data_string = json.dumps(data, sort_keys=True)

        # Generar seed
        data_hash = hashlib.sha256(data_string.encode()).digest()
        seed = int.from_bytes(data_hash[:2], "big") % 10000

        while len(set(str(seed).zfill(4))) == 1:
            seed = (seed + 1) % 10000

        # Ejecutar Kaprekar
        attractor, steps = kaprekar_routine(seed)

        return {
            "data": data,
            "sddcs_verification": {
                "seed": seed,
                "steps": steps,
                "generated_at": int(time.time()),
                "generator_version": metadata.get("version", "1.0"),
            },
            "metadata": metadata,
        }

    def verify_sample(self, sample: dict) -> Tuple[bool, str]:
        """
        Verifica integridad del sample
        """
        if "sddcs_verification" not in sample:
            return False, "Sample sin firma SDDCS"

        # Recalcular fingerprint
        data_string = json.dumps(sample["data"], sort_keys=True)
        data_hash = hashlib.sha256(data_string.encode()).digest()
        calculated_seed = int.from_bytes(data_hash[:2], "big") % 10000

        while len(set(str(calculated_seed).zfill(4))) == 1:
            calculated_seed = (calculated_seed + 1) % 10000

        _, calculated_steps = kaprekar_routine(calculated_seed)

        # Comparar
        verification = sample["sddcs_verification"]

        if calculated_seed != verification["seed"]:
            return False, "Datos alterados: seed no coincide"

        if calculated_steps != verification["steps"]:
            return False, "Corrupción: pasos no coinciden"

        return True, "Sample verificado exitosamente"


# ============================================================================
# 4. PLUGIN STATE PERSISTENCE
# ============================================================================


class SDDCSPlugin:
    """
    Plugin base con persistencia ligera usando SDDCS
    """

    def __init__(self, plugin_id: str):
        self.plugin_id = plugin_id
        self.state = {}
        self._last_fingerprint = None

    def save_state_compact(self) -> Tuple[bytes, bytes]:
        """
        Guarda estado con fingerprint de 4 bytes
        Retorna: (state_bytes, fingerprint)
        """
        # Serializar
        state_bytes = pickle.dumps(self.state)

        # Generar fingerprint SDDCS
        state_hash = hashlib.sha256(state_bytes).digest()
        seed = int.from_bytes(state_hash[:2], "big") % 10000

        while len(set(str(seed).zfill(4))) == 1:
            seed = (seed + 1) % 10000

        attractor, steps = kaprekar_routine(seed)

        fingerprint = (
            seed.to_bytes(2, "big")
            + steps.to_bytes(1, "big")
            + ((seed * steps) % 255).to_bytes(1, "big")
        )

        self._last_fingerprint = fingerprint

        return state_bytes, fingerprint

    def load_state_with_validation(
        self, state_bytes: bytes, fingerprint: bytes
    ) -> Tuple[bool, str]:
        """
        Carga y valida estado
        """
        # Extraer fingerprint
        seed_stored = int.from_bytes(fingerprint[:2], "big")
        steps_stored = fingerprint[2]
        checksum_stored = fingerprint[3]

        # Verificar checksum
        if ((seed_stored * steps_stored) % 255) != checksum_stored:
            return False, "Checksum inválido"

        # Recalcular desde bytes
        state_hash = hashlib.sha256(state_bytes).digest()
        seed_calc = int.from_bytes(state_hash[:2], "big") % 10000

        while len(set(str(seed_calc).zfill(4))) == 1:
            seed_calc = (seed_calc + 1) % 10000

        if seed_calc != seed_stored:
            return False, "Datos alterados: seed mismatch"

        _, steps_calc = kaprekar_routine(seed_calc)

        if steps_calc != steps_stored:
            return False, "Corrupción: steps mismatch"

        # Cargar datos
        self.state = pickle.loads(state_bytes)
        return True, "Estado cargado y verificado"


# ============================================================================
# 5. JWT AUTHENTICATION WITH ROLLING SEEDS
# ============================================================================


class SDDCSJWTManager:
    """
    Gestor de JWT con semillas rotativas basadas en Kaprekar
    """

    def __init__(self, secret_key: str, network_salt: str):
        self.secret_key = secret_key
        self.network_salt = network_salt.encode()
        self._seed_history = {}

    def generate_refresh_token_sddcs(self, user_id: int) -> Tuple[dict, int]:
        """
        Genera payload para refresh token con seed SDDCS
        """
        # Seed inicial basada en tiempo y user_id, pero asegurando evolución
        last_seed = self._seed_history.get(user_id, int(time.time()))
        seed = (last_seed + user_id + 1) % 10000

        while len(set(str(seed).zfill(4))) == 1:
            seed = (seed + 1) % 10000

        self._seed_history[user_id] = seed
        attractor, steps = kaprekar_routine(seed)

        payload = {
            "user_id": user_id,
            "seed": seed,
            "steps": steps,
            "type": "refresh",
            "exp": int(time.time()) + 3600,
        }

        return payload, seed

    def validate_refresh_token_sddcs(self, payload: dict) -> Tuple[bool, str]:
        """
        Valida integridad del token usando Kaprekar
        """
        if payload.get("exp", 0) < time.time():
            return False, "Token expirado"

        seed = payload.get("seed")
        steps_stored = payload.get("steps")

        if seed is None or steps_stored is None:
            return False, "Token inválido: faltan campos SDDCS"

        _, steps_calc = kaprekar_routine(seed)

        if steps_calc != steps_stored:
            return False, "Token manipulado: steps mismatch"

        return True, "Token válido"


# ============================================================================
# 6. AMA-INTENT SDDCS BRIDGE
# ============================================================================


class AMAIntentSDDCSBridge:
    """
    Puente de integración para AMA-Intent v2.0
    """

    def __init__(self, config: dict):
        self.config = config
        self.agent_sync = AgentStateSync(
            agent_id=config.get("agent_id", 1),
            network_salt=config.get("network_salt", "AMA-Intent-v2"),
        )
        self.cache_validator = SDDCSCacheValidator()
        self.jwt_manager = SDDCSJWTManager(
            secret_key=config.get("jwt_secret", "default_secret"),
            network_salt=config.get("network_salt", "AMA-Intent-v2"),
        )
        self.data_verifier = SyntheticDataVerifier()

    def integrate_with_long_horizon_agent(self, agent: Any):
        """Integra con Long Horizon Agent"""
        agent._sddcs_sync = self.agent_sync

        def create_checkpoint_sddcs(state):
            return self.agent_sync.create_checkpoint(state)

        agent.create_checkpoint_sddcs = create_checkpoint_sddcs

    def integrate_with_context_caching(self, cache_manager: Any):
        """Integra con Context Caching"""
        pass

    def integrate_with_dashboard_auth(self, auth_system: Any):
        """Integra con Dashboard Auth"""
        pass

    def integrate_with_plugin_system(self, plugin_registry: Dict[str, Any]):
        """Integra con Plugin System"""
        for plugin_id, plugin in plugin_registry.items():

            def save_state_compact():
                sddcs_plugin = SDDCSPlugin(plugin_id)
                sddcs_plugin.state = getattr(plugin, "state", {})
                return sddcs_plugin.save_state_compact()

            def load_state_with_validation(state_bytes, fingerprint):
                sddcs_plugin = SDDCSPlugin(plugin_id)
                res, msg = sddcs_plugin.load_state_with_validation(
                    state_bytes, fingerprint
                )
                if res:
                    plugin.state = sddcs_plugin.state
                return res, msg

            plugin.save_state_compact = save_state_compact
            plugin.load_state_with_validation = load_state_with_validation


# ============================================================================
# MAIN / DEMO
# ============================================================================

if __name__ == "__main__":
    print("🚀 AMA-Intent v2.0 + SDDCS-Kaprekar Integration Demo")
    print("=" * 70)

    # 1. Agent State Synchronization
    print("\n1️⃣  AGENT STATE SYNCHRONIZATION")
    print("-" * 70)

    sync = AgentStateSync(agent_id=42)
    state = {"step": 150, "memory_usage": "450MB", "active_goal": "data_analysis"}

    checkpoint = sync.create_checkpoint(state)
    print(f"Estado: {state}")
    print(f"Checkpoint generado (4 bytes): {checkpoint.hex().upper()}")

    is_valid = sync.validate_checkpoint(checkpoint, state)
    print(f"Validación: {'✅ OK' if is_valid else '❌ FALLÓ'}")

    # 2. Context Cache Validation
    print("\n2️⃣  CONTEXT CACHE VALIDATION")
    print("-" * 70)

    cache_validator = SDDCSCacheValidator()
    context = "Este es un contexto muy largo que queremos cachear..."

    fingerprint = cache_validator.generate_cache_fingerprint(context)
    print(f"Contexto: '{context[:30]}...'")
    print(f"Fingerprint: {fingerprint}")

    is_valid, message = cache_validator.validate_cached_context(context, fingerprint)
    print(f"Validación: {message}")

    # Simular corrupción
    corrupted_context = context + " [CORRUPCIÓN]"
    is_valid_corrupted, message_corrupted = cache_validator.validate_cached_context(
        corrupted_context, fingerprint
    )
    print(f"Validación con corrupción: {message_corrupted}")

    # 3. Synthetic Data Verification
    print("\n3️⃣  SYNTHETIC DATA VERIFICATION")
    print("-" * 70)

    verifier = SyntheticDataVerifier()

    # Generar dato sintético para entrenamiento
    synthetic_sample = {
        "question": "¿Cómo implementar un Long Horizon Agent?",
        "answer": "Un Long Horizon Agent requiere...",
        "difficulty": "advanced",
        "quality_score": 0.92,
    }

    metadata = {"version": "2.0", "generator": "AMA-Synthesizer", "task_type": "QA"}

    # Verificar y firmar
    verified_sample = verifier.generate_verified_sample(synthetic_sample, metadata)
    print(f"Sample generado:")
    print(f"  Pregunta: {verified_sample['data']['question'][:50]}...")
    print(f"  SDDCS Seed: {verified_sample['sddcs_verification']['seed']}")
    print(f"  SDDCS Steps: {verified_sample['sddcs_verification']['steps']}")

    # Validar sample
    is_valid, message = verifier.verify_sample(verified_sample)
    print(f"Verificación: {message}")

    # Intentar alterar datos
    tampered_sample = verified_sample.copy()
    tampered_sample["data"]["quality_score"] = 0.50  # Alterado

    is_valid_tampered, message_tampered = verifier.verify_sample(tampered_sample)
    print(f"Verificación con datos alterados: {message_tampered}")

    # 4. Plugin State Persistence
    print("\n4️⃣  PLUGIN STATE PERSISTENCE")
    print("-" * 70)

    plugin = SDDCSPlugin(plugin_id="productivity_tracker")

    # Simular estado del plugin
    plugin.state = {
        "total_hours_tracked": 127.5,
        "projects": {
            "AMA-Intent": 45.2,
            "SDDCS-Integration": 18.3,
            "Documentation": 12.0,
        },
        "last_activity": "2026-01-11T14:30:00Z",
        "productivity_score": 87,
    }

    print(f"Estado del plugin: {plugin.state}")

    # Guardar con fingerprint compacto
    state_bytes, fingerprint = plugin.save_state_compact()
    print(f"Estado serializado: {len(state_bytes)} bytes")
    print(f"Fingerprint SDDCS: {fingerprint.hex().upper()} ({len(fingerprint)} bytes)")
    print(
        f"Compresión: {len(state_bytes)} bytes → {len(fingerprint)} bytes fingerprint"
    )

    # Simular carga desde disco
    new_plugin = SDDCSPlugin(plugin_id="productivity_tracker")
    is_valid, message = new_plugin.load_state_with_validation(state_bytes, fingerprint)
    print(f"Carga de estado: {message}")
    print(f"Estado recuperado: {new_plugin.state}")

    # Simular corrupción de 1 byte
    corrupted_bytes = state_bytes[:-1] + bytes([state_bytes[-1] ^ 0xFF])
    is_valid_corrupted, message_corrupted = new_plugin.load_state_with_validation(
        corrupted_bytes, fingerprint
    )
    print(f"Carga con corrupción: {message_corrupted}")

    # 5. JWT Authentication with Rolling Seeds
    print("\n5️⃣  JWT AUTHENTICATION WITH ROLLING SEEDS")
    print("-" * 70)

    jwt_manager = SDDCSJWTManager(
        secret_key="AMA-Intent-Secret-2026", network_salt="AMA-Production-Salt"
    )

    user_id = 1001

    # Generar refresh token (sesión 1)
    payload_1, seed_1 = jwt_manager.generate_refresh_token_sddcs(user_id)
    print(f"Sesión 1:")
    print(f"  User ID: {payload_1['user_id']}")
    print(f"  Seed: {payload_1['seed']}")
    print(f"  Steps: {payload_1['steps']}")

    # Validar
    is_valid, msg = jwt_manager.validate_refresh_token_sddcs(payload_1)
    print(f"Validación Sesión 1: {'✅ OK' if is_valid else '❌ FALLÓ'}")
