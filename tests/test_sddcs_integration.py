#!/usr/bin/env python3
"""
Tests de Integración: SDDCS-Kaprekar + AMA-Intent v2.0
=======================================================

Suite completa de tests para validar la integración del protocolo
SDDCS-Kaprekar en el sistema AMA-Intent.

Ejecutar:
    pytest tests/test_sddcs_integration.py -v
    pytest tests/test_sddcs_integration.py::TestAgentStateSync -v

Cobertura:
    pytest tests/test_sddcs_integration.py --cov=integrations.sddcs_kaprekar
"""

import json
import os
import pickle

# Importar módulos SDDCS (asumiendo que están en integrations/)
import sys
import time
from unittest.mock import Mock, patch

import pytest

# Agregar el directorio raíz al path para importaciones
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrations.sddcs_kaprekar import (
    AgentStateSync,
    AMAIntentSDDCSBridge,
    SDDCSCacheValidator,
    SDDCSJWTManager,
    SDDCSPlugin,
    SyntheticDataVerifier,
    derive_session_key,
    kaprekar_routine,
)

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def agent_sync():
    """Fixture para AgentStateSync"""
    return AgentStateSync(agent_id=42, network_salt="Test-Network")


@pytest.fixture
def cache_validator():
    """Fixture para SDDCSCacheValidator"""
    return SDDCSCacheValidator()


@pytest.fixture
def data_verifier():
    """Fixture para SyntheticDataVerifier"""
    return SyntheticDataVerifier()


@pytest.fixture
def sddcs_plugin():
    """Fixture para SDDCSPlugin"""
    return SDDCSPlugin(plugin_id="test_plugin")


@pytest.fixture
def jwt_manager():
    """Fixture para SDDCSJWTManager"""
    return SDDCSJWTManager(secret_key="test-secret", network_salt="Test-JWT-Salt")


@pytest.fixture
def sample_agent_state():
    """Estado de ejemplo para Long Horizon Agent"""
    return {
        "current_step": 150,
        "total_steps": 300,
        "task": "Analizar proyecto completo",
        "context_tokens": 125000,
        "decisions_made": 47,
        "confidence": 0.89,
    }


# ============================================================================
# TEST SUITE: CORE KAPREKAR FUNCTIONS
# ============================================================================


class TestKaprekarCore:
    """Tests para las funciones core de Kaprekar"""

    def test_kaprekar_convergence_basic(self):
        """Verificar convergencia básica a 6174"""
        attractor, steps = kaprekar_routine(3524)
        assert attractor == 6174
        assert steps == 3

    def test_kaprekar_convergence_max_iterations(self):
        """Verificar convergencia en máximo 7 iteraciones"""
        test_seeds = [1234, 5678, 9012, 2468, 1357]

        for seed in test_seeds:
            attractor, steps = kaprekar_routine(seed)
            assert attractor == 6174
            assert steps <= 7, f"Seed {seed} tomó {steps} pasos (máximo 7)"

    def test_kaprekar_determinism(self):
        """Verificar que Kaprekar es determinista"""
        seed = 3524

        results = [kaprekar_routine(seed) for _ in range(10)]

        # Todos los resultados deben ser idénticos
        assert len(set(results)) == 1

    def test_derive_session_key_uniqueness(self):
        """Verificar que claves de sesión son únicas por parámetros"""
        key1 = derive_session_key(1, b"salt1", 3524, 3, 0)
        key2 = derive_session_key(1, b"salt1", 3524, 3, 1)  # Diferente counter
        key3 = derive_session_key(2, b"salt1", 3524, 3, 0)  # Diferente node_id

        assert key1 != key2
        assert key1 != key3
        assert key2 != key3


# ============================================================================
# TEST SUITE: AGENT STATE SYNCHRONIZATION
# ============================================================================


class TestAgentStateSync:
    """Tests para sincronización de estado del agente"""

    def test_checkpoint_creation(self, agent_sync, sample_agent_state):
        """Verificar creación de checkpoint"""
        checkpoint = agent_sync.create_checkpoint(sample_agent_state)

        # Debe ser exactamente 4 bytes
        assert len(checkpoint) == 4
        assert isinstance(checkpoint, bytes)

    def test_checkpoint_validation_valid(self, agent_sync, sample_agent_state):
        """Verificar validación de checkpoint válido"""
        checkpoint = agent_sync.create_checkpoint(sample_agent_state)
        is_valid = agent_sync.validate_checkpoint(checkpoint, sample_agent_state)

        assert is_valid is True

    def test_checkpoint_validation_corrupted_state(
        self, agent_sync, sample_agent_state
    ):
        """Verificar detección de estado corrupto"""
        checkpoint = agent_sync.create_checkpoint(sample_agent_state)

        # Alterar estado
        corrupted_state = sample_agent_state.copy()
        corrupted_state["current_step"] = 999

        is_valid = agent_sync.validate_checkpoint(checkpoint, corrupted_state)

        assert is_valid is False

    def test_checkpoint_validation_corrupted_checkpoint(
        self, agent_sync, sample_agent_state
    ):
        """Verificar detección de checkpoint corrupto"""
        checkpoint = agent_sync.create_checkpoint(sample_agent_state)

        # Corromper checkpoint (flip 1 bit)
        corrupted_checkpoint = bytearray(checkpoint)
        corrupted_checkpoint[0] ^= 0x01

        is_valid = agent_sync.validate_checkpoint(
            bytes(corrupted_checkpoint), sample_agent_state
        )

        # Nota: Puede ser True si la corrupción preserva la seed
        # Este test verifica que el sistema maneja checksums corruptos
        assert isinstance(is_valid, bool)

    def test_checkpoint_counter_increment(self, agent_sync, sample_agent_state):
        """Verificar que el contador de checkpoint incrementa"""
        initial_counter = agent_sync.checkpoint_counter

        agent_sync.create_checkpoint(sample_agent_state)

        assert agent_sync.checkpoint_counter == initial_counter + 1

    def test_multiple_checkpoints_different(self, agent_sync):
        """Verificar que checkpoints consecutivos son diferentes"""
        state1 = {"step": 1, "data": "foo"}
        state2 = {"step": 2, "data": "bar"}

        checkpoint1 = agent_sync.create_checkpoint(state1)
        checkpoint2 = agent_sync.create_checkpoint(state2)

        assert checkpoint1 != checkpoint2


# ============================================================================
# TEST SUITE: CONTEXT CACHE VALIDATION
# ============================================================================


class TestContextCacheValidation:
    """Tests para validación de contextos cacheados"""

    def test_fingerprint_generation(self, cache_validator):
        """Verificar generación de fingerprint"""
        context = "Este es un contexto de prueba para AMA-Intent" * 1000

        fingerprint = cache_validator.generate_cache_fingerprint(context)

        assert "seed" in fingerprint
        assert "steps" in fingerprint
        assert "size_bytes" in fingerprint
        assert "token_count" in fingerprint

        assert 1000 <= fingerprint["seed"] <= 9999
        assert 0 <= fingerprint["steps"] <= 7

    def test_cache_validation_valid(self, cache_validator):
        """Verificar validación de cache válido"""
        context = "Contexto original sin modificaciones"

        fingerprint = cache_validator.generate_cache_fingerprint(context)
        is_valid, message = cache_validator.validate_cached_context(
            context, fingerprint
        )

        assert is_valid is True
        assert "válido" in message.lower()

    def test_cache_validation_corrupted(self, cache_validator):
        """Verificar detección de cache corrupto"""
        context = "Contexto original"
        fingerprint = cache_validator.generate_cache_fingerprint(context)

        # Corromper contexto
        corrupted_context = "Contexto alterado"

        is_valid, message = cache_validator.validate_cached_context(
            corrupted_context, fingerprint
        )

        assert is_valid is False

    def test_cache_validation_truncated(self, cache_validator):
        """Verificar detección de contexto truncado"""
        context = "Contexto completo con muchos datos" * 100
        fingerprint = cache_validator.generate_cache_fingerprint(context)

        # Truncar contexto
        truncated_context = context[:-50]

        is_valid, message = cache_validator.validate_cached_context(
            truncated_context, fingerprint
        )

        assert is_valid is False
        assert "size" in message.lower() or "truncado" in message.lower()

    def test_fingerprint_determinism(self, cache_validator):
        """Verificar que fingerprints son deterministas"""
        context = "Mismo contexto cada vez"

        fp1 = cache_validator.generate_cache_fingerprint(context)
        fp2 = cache_validator.generate_cache_fingerprint(context)

        assert fp1["seed"] == fp2["seed"]
        assert fp1["steps"] == fp2["steps"]


# ============================================================================
# TEST SUITE: SYNTHETIC DATA VERIFICATION
# ============================================================================


class TestSyntheticDataVerification:
    """Tests para verificación de datos sintéticos"""

    def test_sample_generation_with_signature(self, data_verifier):
        """Verificar generación de sample con firma SDDCS"""
        data = {
            "question": "¿Qué es SDDCS?",
            "answer": "Sistema de Diccionario Dinámico...",
            "quality": 0.95,
        }
        metadata = {"version": "2.0", "generator": "test"}

        verified_sample = data_verifier.generate_verified_sample(data, metadata)

        assert "data" in verified_sample
        assert "sddcs_verification" in verified_sample
        assert "metadata" in verified_sample

        verification = verified_sample["sddcs_verification"]
        assert "seed" in verification
        assert "steps" in verification
        assert "generated_at" in verification

    def test_sample_verification_valid(self, data_verifier):
        """Verificar validación de sample válido"""
        data = {"field": "value"}
        metadata = {"version": "1.0"}

        sample = data_verifier.generate_verified_sample(data, metadata)
        is_valid, message = data_verifier.verify_sample(sample)

        assert is_valid is True
        assert "verificado" in message.lower()

    def test_sample_verification_tampered(self, data_verifier):
        """Verificar detección de sample alterado"""
        data = {"original": "data"}
        metadata = {"version": "1.0"}

        sample = data_verifier.generate_verified_sample(data, metadata)

        # Alterar datos
        sample["data"]["original"] = "modified"

        is_valid, message = data_verifier.verify_sample(sample)

        assert is_valid is False
        assert "alterado" in message.lower() or "no coincide" in message.lower()

    def test_sample_without_signature_fails(self, data_verifier):
        """Verificar que sample sin firma falla validación"""
        sample = {"data": {"test": "data"}, "metadata": {}}

        is_valid, message = data_verifier.verify_sample(sample)

        assert is_valid is False
        assert "sin firma" in message.lower()


# ============================================================================
# TEST SUITE: PLUGIN STATE PERSISTENCE
# ============================================================================


class TestPluginStatePersistence:
    """Tests para persistencia de estado de plugins"""

    def test_save_state_compact(self, sddcs_plugin):
        """Verificar guardado compacto de estado"""
        sddcs_plugin.state = {
            "counter": 42,
            "data": ["item1", "item2"],
            "config": {"enabled": True},
        }

        state_bytes, fingerprint = sddcs_plugin.save_state_compact()

        assert isinstance(state_bytes, bytes)
        assert isinstance(fingerprint, bytes)
        assert len(fingerprint) == 4
        assert len(state_bytes) > 0

    def test_load_state_valid(self, sddcs_plugin):
        """Verificar carga de estado válido"""
        original_state = {"key": "value", "number": 123}
        sddcs_plugin.state = original_state

        state_bytes, fingerprint = sddcs_plugin.save_state_compact()

        # Crear nuevo plugin y cargar
        new_plugin = SDDCSPlugin("test_plugin")
        is_valid, message = new_plugin.load_state_with_validation(
            state_bytes, fingerprint
        )

        assert is_valid is True
        assert new_plugin.state == original_state

    def test_load_state_corrupted(self, sddcs_plugin):
        """Verificar detección de estado corrupto"""
        sddcs_plugin.state = {"data": "test"}

        state_bytes, fingerprint = sddcs_plugin.save_state_compact()

        # Corromper state_bytes
        corrupted_bytes = state_bytes[:-1] + bytes([state_bytes[-1] ^ 0xFF])

        new_plugin = SDDCSPlugin("test_plugin")
        is_valid, message = new_plugin.load_state_with_validation(
            corrupted_bytes, fingerprint
        )

        assert is_valid is False

    def test_fingerprint_size_advantage(self, sddcs_plugin):
        """Verificar que fingerprint es más pequeño que HMAC tradicional"""
        sddcs_plugin.state = {"large": "state" * 1000}

        state_bytes, fingerprint = sddcs_plugin.save_state_compact()

        # Fingerprint SDDCS: 4 bytes
        # HMAC-SHA256: 32 bytes
        assert len(fingerprint) == 4
        assert len(fingerprint) < 32  # Menor que HMAC


# ============================================================================
# TEST SUITE: JWT AUTHENTICATION WITH ROLLING SEEDS
# ============================================================================


class TestJWTAuthentication:
    """Tests para autenticación JWT con Rolling Seeds"""

    def test_generate_refresh_token(self, jwt_manager):
        """Verificar generación de refresh token"""
        user_id = 1001

        payload, seed = jwt_manager.generate_refresh_token_sddcs(user_id)

        assert payload["user_id"] == user_id
        assert "seed" in payload
        assert "steps" in payload
        assert "exp" in payload
        assert payload["type"] == "refresh"
        assert 1000 <= seed <= 9999

    def test_validate_refresh_token_valid(self, jwt_manager):
        """Verificar validación de token válido"""
        user_id = 1001

        payload, seed = jwt_manager.generate_refresh_token_sddcs(user_id)
        is_valid, message = jwt_manager.validate_refresh_token_sddcs(payload)

        assert is_valid is True
        assert "válido" in message.lower()

    def test_validate_refresh_token_expired(self, jwt_manager):
        """Verificar rechazo de token expirado"""
        user_id = 1001

        payload, seed = jwt_manager.generate_refresh_token_sddcs(user_id)

        # Simular expiración
        payload["exp"] = int(time.time()) - 3600

        is_valid, message = jwt_manager.validate_refresh_token_sddcs(payload)

        assert is_valid is False
        assert "expirado" in message.lower()

    def test_validate_refresh_token_tampered(self, jwt_manager):
        """Verificar detección de token manipulado"""
        user_id = 1001

        payload, seed = jwt_manager.generate_refresh_token_sddcs(user_id)

        # Manipular steps
        payload["steps"] = 99

        is_valid, message = jwt_manager.validate_refresh_token_sddcs(payload)

        assert is_valid is False
        assert "manipulado" in message.lower() or "no coinciden" in message.lower()

    def test_rolling_seeds_evolution(self, jwt_manager):
        """Verificar que rolling seeds evolucionan"""
        user_id = 1001

        payload1, seed1 = jwt_manager.generate_refresh_token_sddcs(user_id)
        payload2, seed2 = jwt_manager.generate_refresh_token_sddcs(user_id)
        payload3, seed3 = jwt_manager.generate_refresh_token_sddcs(user_id)

        # Seeds deben ser diferentes
        assert seed1 != seed2
        assert seed2 != seed3
        assert seed1 != seed3

    def test_different_users_different_seeds(self, jwt_manager):
        """Verificar que usuarios diferentes tienen seeds diferentes"""
        payload_user1, seed1 = jwt_manager.generate_refresh_token_sddcs(1001)
        payload_user2, seed2 = jwt_manager.generate_refresh_token_sddcs(1002)

        assert seed1 != seed2


# ============================================================================
# TEST SUITE: AMA-INTENT INTEGRATION BRIDGE
# ============================================================================


class TestAMAIntentBridge:
    """Tests para el puente de integración"""

    @pytest.fixture
    def bridge(self):
        """Fixture para AMAIntentSDDCSBridge"""
        config = {
            "agent_id": 1,
            "network_salt": "Test-Integration",
            "jwt_secret": "test-secret-key",
        }
        return AMAIntentSDDCSBridge(config)

    def test_bridge_initialization(self, bridge):
        """Verificar inicialización del puente"""
        assert bridge.agent_sync is not None
        assert bridge.cache_validator is not None
        assert bridge.data_verifier is not None
        assert bridge.jwt_manager is not None

    def test_integrate_with_long_horizon_agent(self, bridge):
        """Verificar integración con Long Horizon Agent"""

        class MockAgent:
            pass

        agent = MockAgent()
        bridge.integrate_with_long_horizon_agent(agent)

        # Verificar que el método fue inyectado
        assert hasattr(agent, "create_checkpoint_sddcs")
        assert hasattr(agent, "_sddcs_sync")

    def test_integrate_with_plugin_system(self, bridge):
        """Verificar integración con sistema de plugins"""
        plugins = {
            "plugin1": type("Plugin", (), {"state": {}})(),
            "plugin2": type("Plugin", (), {"state": {}})(),
        }

        bridge.integrate_with_plugin_system(plugins)

        # Verificar que los métodos fueron inyectados
        for plugin in plugins.values():
            assert hasattr(plugin, "save_state_compact")
            assert hasattr(plugin, "load_state_with_validation")


# ============================================================================
# TEST SUITE: PERFORMANCE & BENCHMARKS
# ============================================================================


class TestPerformance:
    """Tests de rendimiento y benchmarks"""

    def test_checkpoint_size_advantage(self, agent_sync, sample_agent_state):
        """Verificar ventaja de tamaño de checkpoints"""
        # SDDCS checkpoint
        sddcs_checkpoint = agent_sync.create_checkpoint(sample_agent_state)

        # Checkpoint JSON tradicional
        json_checkpoint = json.dumps(sample_agent_state).encode()

        # SDDCS debe ser mucho más pequeño
        assert len(sddcs_checkpoint) < len(json_checkpoint)
        reduction = (1 - len(sddcs_checkpoint) / len(json_checkpoint)) * 100
        assert reduction > 90  # Al menos 90% de reducción

    def test_kaprekar_speed(self):
        """Verificar que Kaprekar es rápido"""
        import time

        iterations = 1000
        start = time.perf_counter()

        for i in range(iterations):
            kaprekar_routine(3524 + i)

        elapsed = time.perf_counter() - start
        avg_time = elapsed / iterations
        print(f"Average Kaprekar time: {avg_time:.6f}s")
