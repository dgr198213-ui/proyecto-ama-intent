#!/usr/bin/env python3
"""
AMA-Intent Prometheus Metrics Exporter
=======================================

Expone métricas de AMA-Intent + SDDCS en formato Prometheus

Integración:
    # En ama_personal_dashboard.py
    from src.metrics.prometheus_exporter import setup_metrics, metrics

    app = Flask(__name__)
    setup_metrics(app)

    @app.route('/api/task')
    def task():
        with metrics.task_duration.time():
            # ... lógica ...
        metrics.tasks_completed.inc()

Endpoint: /metrics
"""

import os
import sqlite3
import time
from functools import wraps
from pathlib import Path
from typing import Callable

import psutil
from flask import Flask, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Summary,
    generate_latest,
)
from prometheus_client.multiprocess import MultiProcessCollector

# ============================================================================
# MÉTRICAS GLOBALES
# ============================================================================


class AMAMetrics:
    """
    Colección de todas las métricas de AMA-Intent
    """

    def __init__(self):
        # HTTP Requests
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
        )

        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
        )

        # SDDCS Metrics
        self.sddcs_checkpoints_created_total = Counter(
            "sddcs_checkpoints_created_total", "Total SDDCS checkpoints created"
        )

        self.sddcs_checkpoints_validated_total = Counter(
            "sddcs_checkpoints_validated_total", "Total SDDCS checkpoints validated"
        )

        self.sddcs_validation_failures_total = Counter(
            "sddcs_validation_failures_total", "Total SDDCS validation failures"
        )

        self.sddcs_validation_success_rate = Gauge(
            "sddcs_validation_success_rate", "SDDCS validation success rate (0-1)"
        )

        self.sddcs_checkpoint_duration_seconds = Histogram(
            "sddcs_checkpoint_duration_seconds",
            "Time to create SDDCS checkpoint",
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5],
        )

        self.sddcs_cache_validations_total = Counter(
            "sddcs_cache_validations_total", "Total SDDCS cache validations"
        )

        self.sddcs_jwt_rolling_refreshes_total = Counter(
            "sddcs_jwt_rolling_refreshes_total", "Total JWT rolling seed refreshes"
        )

        # Long Horizon Agent
        self.agent_tasks_started_total = Counter(
            "agent_tasks_started_total", "Total agent tasks started"
        )

        self.agent_tasks_completed_total = Counter(
            "agent_tasks_completed_total", "Total agent tasks completed"
        )

        self.agent_tasks_failed_total = Counter(
            "agent_tasks_failed_total", "Total agent tasks failed"
        )

        self.agent_task_duration_seconds = Histogram(
            "agent_task_duration_seconds",
            "Agent task completion time",
            buckets=[1, 5, 10, 30, 60, 120, 300, 600],
        )

        self.agent_current_step = Gauge(
            "agent_current_step", "Current step of running agent"
        )

        self.agent_total_steps = Gauge("agent_total_steps", "Total steps in agent task")

        # Cache Metrics
        self.cache_hits_total = Counter("cache_hits_total", "Total cache hits")

        self.cache_misses_total = Counter("cache_misses_total", "Total cache misses")

        self.context_size_bytes = Histogram(
            "context_size_bytes",
            "Size of cached contexts in bytes",
            buckets=[1024, 10240, 102400, 1024000, 10240000, 102400000],
        )

        # System Metrics
        self.database_size_bytes = Gauge(
            "database_size_bytes", "Size of SQLite database in bytes"
        )

        self.active_users = Gauge("active_users", "Number of active users")

        # Backup Metrics
        self.backup_last_success_timestamp_seconds = Gauge(
            "backup_last_success_timestamp_seconds",
            "Unix timestamp of last successful backup",
        )

        self.backup_duration_seconds = Histogram(
            "backup_duration_seconds",
            "Backup completion time",
            buckets=[10, 30, 60, 120, 300, 600],
        )

        self.backup_size_bytes = Gauge(
            "backup_size_bytes", "Size of last backup in bytes"
        )

    def update_validation_rate(self):
        """Actualiza la tasa de validación SDDCS"""
        total = self.sddcs_checkpoints_validated_total._value.get()
        failures = self.sddcs_validation_failures_total._value.get()

        if total > 0:
            rate = 1 - (failures / total)
            self.sddcs_validation_success_rate.set(rate)


# Instancia global
metrics = AMAMetrics()


# ============================================================================
# DECORADORES
# ============================================================================


def track_request(f: Callable) -> Callable:
    """
    Decorator para trackear requests HTTP

    Uso:
        @app.route('/api/task')
        @track_request
        def task():
            ...
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()

        # Ejecutar función
        response = f(*args, **kwargs)

        # Registrar métricas
        duration = time.time() - start_time

        from flask import request

        method = request.method
        endpoint = request.endpoint or "unknown"
        status = getattr(response, "status_code", 200)

        metrics.http_requests_total.labels(
            method=method, endpoint=endpoint, status=status
        ).inc()

        metrics.http_request_duration_seconds.labels(
            method=method, endpoint=endpoint
        ).observe(duration)

        return response

    return decorated_function


def track_agent_task(f: Callable) -> Callable:
    """
    Decorator para trackear tareas del Long Horizon Agent

    Uso:
        @track_agent_task
        def process_project(project_path):
            ...
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        metrics.agent_tasks_started_total.inc()
        start_time = time.time()

        try:
            result = f(*args, **kwargs)

            duration = time.time() - start_time
            metrics.agent_task_duration_seconds.observe(duration)
            metrics.agent_tasks_completed_total.inc()

            return result

        except Exception as e:
            metrics.agent_tasks_failed_total.inc()
            raise

    return decorated_function


# ============================================================================
# COLLECTORS PERSONALIZADOS
# ============================================================================


class SystemMetricsCollector:
    """Recolecta métricas del sistema"""

    @staticmethod
    def collect_db_size():
        """Actualiza tamaño de la base de datos"""
        db_path = Path("/app/data/ama_dashboard.db")

        if db_path.exists():
            size = db_path.stat().st_size
            metrics.database_size_bytes.set(size)

    @staticmethod
    def collect_active_users():
        """Cuenta usuarios activos en los últimos 5 minutos"""
        db_path = Path("/app/data/ama_dashboard.db")

        if not db_path.exists():
            return

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Contar usuarios con actividad reciente
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) 
                FROM user_activity 
                WHERE timestamp > datetime('now', '-5 minutes')
            """)

            count = cursor.fetchone()[0]
            metrics.active_users.set(count)

            conn.close()

        except sqlite3.Error:
            pass  # Tabla puede no existir

    @staticmethod
    def collect_all():
        """Recolecta todas las métricas del sistema"""
        SystemMetricsCollector.collect_db_size()
        SystemMetricsCollector.collect_active_users()


# ============================================================================
# INTEGRACIÓN CON FLASK
# ============================================================================


def setup_metrics(app: Flask):
    """
    Configura endpoint /metrics en la aplicación Flask

    Args:
        app: Instancia de Flask
    """

    @app.route("/metrics")
    def prometheus_metrics():
        """Endpoint de métricas Prometheus"""
        # Actualizar métricas dinámicas
        SystemMetricsCollector.collect_all()
        metrics.update_validation_rate()

        # Generar respuesta
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    @app.route("/api/sddcs/metrics")
    def sddcs_metrics():
        """Endpoint específico de SDDCS (formato JSON)"""
        from flask import jsonify

        return jsonify(
            {
                "checkpoints": {
                    "created": metrics.sddcs_checkpoints_created_total._value.get(),
                    "validated": metrics.sddcs_checkpoints_validated_total._value.get(),
                    "validation_rate": metrics.sddcs_validation_success_rate._value.get(),
                },
                "cache": {
                    "validations": metrics.sddcs_cache_validations_total._value.get(),
                    "hits": metrics.cache_hits_total._value.get(),
                    "misses": metrics.cache_misses_total._value.get(),
                },
                "jwt": {
                    "rolling_refreshes": metrics.sddcs_jwt_rolling_refreshes_total._value.get()
                },
            }
        )

    @app.route("/api/sddcs/health")
    def sddcs_health():
        """Health check específico de SDDCS"""
        from flask import jsonify

        # Verificar tasa de validación
        validation_rate = metrics.sddcs_validation_success_rate._value.get()

        is_healthy = validation_rate >= 0.85

        return jsonify(
            {
                "status": "healthy" if is_healthy else "degraded",
                "validation_rate": validation_rate,
                "checkpoints_created": metrics.sddcs_checkpoints_created_total._value.get(),
            }
        ), (200 if is_healthy else 503)


# ============================================================================
# HELPERS PARA USO EN LA APLICACIÓN
# ============================================================================


class MetricsContext:
    """Context manager para métricas con timing"""

    def __init__(self, metric_name: str):
        self.metric_name = metric_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time

        # Registrar en el histogram correspondiente
        if self.metric_name == "checkpoint":
            metrics.sddcs_checkpoint_duration_seconds.observe(duration)
        elif self.metric_name == "agent_task":
            metrics.agent_task_duration_seconds.observe(duration)
        elif self.metric_name == "backup":
            metrics.backup_duration_seconds.observe(duration)


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    """
    Ejemplo de cómo integrar métricas en la aplicación
    """

    app = Flask(__name__)
    setup_metrics(app)

    @app.route("/api/test")
    @track_request
    def test_endpoint():
        """Endpoint de prueba con tracking"""

        # Simular creación de checkpoint
        with MetricsContext("checkpoint"):
            time.sleep(0.01)  # Simular trabajo

        metrics.sddcs_checkpoints_created_total.inc()

        return {"status": "ok"}

    @app.route("/api/agent/task")
    @track_request
    @track_agent_task
    def agent_task_endpoint():
        """Endpoint de Long Horizon Agent"""

        # Simular tarea de agente
        metrics.agent_total_steps.set(100)

        for step in range(100):
            metrics.agent_current_step.set(step)
            time.sleep(0.001)

        return {"status": "completed", "steps": 100}

    # Iniciar servidor
    print("🚀 Metrics exporter running on http://localhost:5000/metrics")
    app.run(host="0.0.0.0", port=5000)
