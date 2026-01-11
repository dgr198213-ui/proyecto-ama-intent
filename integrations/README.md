# Integrations Directory

Este directorio contiene las integraciones externas del sistema AMA-Intent v2.0.

## Módulos Disponibles

### SDDCS-Kaprekar Integration (`sddcs_kaprekar.py`)

Integración del protocolo SDDCS (Sistema de Diccionario Dinámico de Compensación Estocástica) basado en el algoritmo de Kaprekar para:

- **Agent State Synchronization**: Sincronización de estado del Long Horizon Agent
- **Context Cache Validation**: Validación de integridad de contextos cacheados
- **Synthetic Data Verification**: Verificación de datos sintéticos del Agentic Data Synthesizer
- **Plugin State Persistence**: Persistencia ligera de estado de plugins
- **JWT Authentication with Rolling Seeds**: Autenticación JWT con semillas rotativas

## Uso

```python
from integrations.sddcs_kaprekar import (
    AgentStateSync,
    SDDCSCacheValidator,
    SyntheticDataVerifier,
    SDDCSPlugin,
    SDDCSJWTManager
)

# Ejemplo: Sincronización de estado del agente
agent_sync = AgentStateSync(agent_id=42)
checkpoint = agent_sync.create_checkpoint(agent_state)
is_valid = agent_sync.validate_checkpoint(checkpoint, agent_state)
```

## Documentación

Para más detalles sobre la integración SDDCS-Kaprekar, consulte:
- `docs/SDDCS_KAPREKAR_INTEGRATION.md`
- `docs/SDDCS_FORMULATION.md`

## Tests

Los tests de integración se encuentran en:
- `tests/test_sddcs_integration.py`

Ejecutar tests:
```bash
pytest tests/test_sddcs_integration.py -v
```
