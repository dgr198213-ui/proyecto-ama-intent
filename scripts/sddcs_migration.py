#!/usr/bin/env python3
"""
Migración de BD para soporte SDDCS
"""

import argparse
import os
import sqlite3

# Configurar ruta de la base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ama_dashboard.db")


def migrate(create_schema_only=False):
    # Asegurar que el directorio data existe
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabla para checkpoints de agentes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_checkpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER NOT NULL,
            step_number INTEGER NOT NULL,
            checkpoint_data BLOB NOT NULL,
            fingerprint BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (agent_id) REFERENCES users(id)
        )
    """)

    # Tabla para fingerprints de cache
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cache_fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key TEXT NOT NULL UNIQUE,
            seed INTEGER NOT NULL,
            steps INTEGER NOT NULL,
            size_bytes INTEGER NOT NULL,
            token_count INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabla para estados de plugins
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plugin_states_sddcs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plugin_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            state_data BLOB NOT NULL,
            fingerprint BLOB NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(plugin_id, user_id)
        )
    """)

    # Tabla para JWT rolling seeds
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jwt_rolling_seeds (
            user_id INTEGER PRIMARY KEY,
            current_seed INTEGER NOT NULL,
            session_counter INTEGER DEFAULT 0,
            last_refresh TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()

    if create_schema_only:
        print("✅ Esquema SDDCS creado exitosamente")
    else:
        print("✅ Migración SDDCS completada exitosamente")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migración de BD para soporte SDDCS")
    parser.add_argument(
        "--create-schema-only",
        action="store_true",
        help="Solo crear el esquema sin mensajes de migración completa",
    )
    args = parser.parse_args()

    migrate(create_schema_only=args.create_schema_only)
