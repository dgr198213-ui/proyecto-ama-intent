# cli_interactive.py - Interfaz de Consola Interactiva
"""
CLI interactiva para chatear con la IA local gobernada.

Uso:
    python cli_interactive.py

Comandos especiales:
    /help      - Muestra ayuda
    /stats     - Muestra estadísticas
    /config    - Muestra configuración
    /sleep     - Fuerza ciclo de sueño
    /reset     - Resetea el cerebro
    /exit      - Sale del programa
"""

import os
import readline  # Para historial de comandos
import sys
from typing import Optional

# Añadir path del proyecto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ollama_brain_interface import CompleteBrainConfig, GovernedLocalLLM, LLMConfig


class InteractiveCLI:
    """
    Interfaz de línea de comandos interactiva.
    """

    def __init__(self):
        """Inicializa la CLI"""
        self.system: Optional[GovernedLocalLLM] = None
        self.running = False

    def print_banner(self):
        """Imprime banner de bienvenida"""
        print("\n" + "=" * 70)
        print("🧠 IA LOCAL GOBERNADA - Chat Interactivo")
        print("   Cerebro Artificial + Ollama/LM Studio")
        print("=" * 70)
        print("\nEscribe /help para ver comandos disponibles\n")

    def print_help(self):
        """Muestra ayuda"""
        print("\n" + "=" * 70)
        print("📖 COMANDOS DISPONIBLES")
        print("=" * 70)
        print("  /help      - Muestra esta ayuda")
        print("  /stats     - Muestra estadísticas del sistema")
        print("  /config    - Muestra configuración actual")
        print("  /sleep     - Fuerza un ciclo de sueño/consolidación")
        print("  /reset     - Resetea el cerebro (borra memoria)")
        print("  /history   - Muestra historial de conversación")
        print("  /export    - Exporta estadísticas a JSON")
        print("  /exit      - Sale del programa")
        print("=" * 70 + "\n")

    def print_stats(self):
        """Muestra estadísticas"""
        if not self.system:
            print("⚠ Sistema no inicializado")
            return

        stats = self.system.get_statistics()

        print("\n" + "=" * 70)
        print("📊 ESTADÍSTICAS DEL SISTEMA")
        print("=" * 70)
        print(f"\n💬 Conversación:")
        print(f"  Total de mensajes: {stats['total_conversations']}")
        print(f"  Tasa de aprobación: {stats['approval_rate']:.1%}")

        brain_stats = stats["brain_stats"]
        print(f"\n🧠 Cerebro:")
        print(f"  Ticks ejecutados: {brain_stats['total_ticks']}")
        print(
            f"  Episodios en memoria: {brain_stats['episodic_memory']['total_episodes']}"
        )
        print(
            f"  Conceptos semánticos: {brain_stats['semantic_memory']['total_concepts']}"
        )
        print(f"  Ciclos de sueño: {brain_stats['sleep']['total_cycles']}")

        auditor = brain_stats.get("auditor", {})
        if auditor:
            print(f"\n🛡️ Gobernanza (AMA-G):")
            print(f"  Auditorías totales: {auditor.get('total_audits', 0)}")
            print(f"  Tasa de aprobación: {auditor.get('pass_rate', 0):.1%}")
            print(f"  Tasa de revisión: {auditor.get('revision_rate', 0):.1%}")
            print(f"  Tasa de fallo: {auditor.get('fail_rate', 0):.1%}")

        print("=" * 70 + "\n")

    def print_config(self):
        """Muestra configuración"""
        if not self.system:
            print("⚠ Sistema no inicializado")
            return

        print("\n" + "=" * 70)
        print("⚙️ CONFIGURACIÓN")
        print("=" * 70)
        print(f"\n🤖 LLM:")
        print(f"  Provider: {self.system.llm_config.provider}")
        print(f"  URL: {self.system.llm_config.base_url}")
        print(f"  Modelo: {self.system.llm_config.model}")
        print(f"  Temperature: {self.system.llm_config.temperature}")
        print(f"  Max tokens: {self.system.llm_config.max_tokens}")

        print(f"\n🧠 Cerebro:")
        print(f"  Dim observación: {self.system.brain.config.dim_observation}")
        print(f"  Dim latente: {self.system.brain.config.dim_latent}")
        print(
            f"  Aprendizaje: {'✓' if self.system.brain.config.enable_learning else '✗'}"
        )
        print(
            f"  Homeostasis: {'✓' if self.system.brain.config.enable_homeostasis else '✗'}"
        )
        print(f"  Sueño: {'✓' if self.system.brain.config.enable_sleep else '✗'}")
        print(f"  Intervalo de sueño: {self.system.brain.config.sleep_interval} ticks")

        print("=" * 70 + "\n")

    def force_sleep(self):
        """Fuerza ciclo de sueño"""
        if not self.system:
            print("⚠ Sistema no inicializado")
            return

        print("\n💤 Iniciando ciclo de sueño forzado...\n")

        sleep_stats = self.system.brain.sleep_cycle.execute_sleep_cycle(
            self.system.brain.episodic_memory,
            self.system.brain.semantic_memory,
            self.system.brain.cortex,
            self.system.brain.q_estimator,
            self.system.brain.pruning_system,
        )

        print(f"\n✅ Ciclo de sueño completado")
        print(f"  Episodios consolidados: {sleep_stats.get('episodes_replayed', 0)}")
        print(f"  Conceptos fusionados: {sleep_stats.get('concepts_merged', 0)}")
        print(f"  Items podados: {sleep_stats.get('items_pruned', 0)}\n")

    def show_history(self):
        """Muestra historial de conversación"""
        if not self.system or not self.system.conversation_history:
            print("⚠ No hay historial disponible")
            return

        print("\n" + "=" * 70)
        print("📜 HISTORIAL DE CONVERSACIÓN")
        print("=" * 70 + "\n")

        for i, conv in enumerate(self.system.conversation_history[-10:], 1):
            print(f"[{i}] Usuario: {conv['user'][:60]}...")
            if conv["approved"]:
                print(f"    IA: {conv['assistant'][:60]}...")
                print(
                    f"    ✓ Aprobado (confianza: {conv['brain_state']['metrics']['confidence']:.2f})"
                )
            else:
                print(f"    ✗ Bloqueado")
            print()

        if len(self.system.conversation_history) > 10:
            print(f"... y {len(self.system.conversation_history) - 10} mensajes más\n")

        print("=" * 70 + "\n")

    def export_stats(self):
        """Exporta estadísticas a JSON"""
        if not self.system:
            print("⚠ Sistema no inicializado")
            return

        import json
        from datetime import datetime

        stats = self.system.get_statistics()

        # Preparar datos serializables
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "total_conversations": stats["total_conversations"],
            "approval_rate": float(stats["approval_rate"]),
            "brain_ticks": stats["brain_stats"]["total_ticks"],
            "episodes": stats["brain_stats"]["episodic_memory"]["total_episodes"],
            "concepts": stats["brain_stats"]["semantic_memory"]["total_concepts"],
            "sleep_cycles": stats["brain_stats"]["sleep"]["total_cycles"],
        }

        filename = f"brain_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, "w") as f:
            json.dump(export_data, f, indent=2)

        print(f"\n✅ Estadísticas exportadas a: {filename}\n")

    def initialize_system(self):
        """Inicializa el sistema con configuración del usuario"""
        print("\n🔧 Configuración del sistema\n")

        # Configuración LLM
        print("Configuración del LLM:")
        provider = (
            input("  Provider (ollama/lmstudio) [ollama]: ").strip().lower() or "ollama"
        )

        if provider == "ollama":
            base_url = (
                input("  URL [http://localhost:11434]: ").strip()
                or "http://localhost:11434"
            )
            model = input("  Modelo [gemma2:2b]: ").strip() or "gemma2:2b"
        else:
            base_url = (
                input("  URL [http://localhost:1234]: ").strip()
                or "http://localhost:1234"
            )
            model = input("  Modelo [local-model]: ").strip() or "local-model"

        temperature = input("  Temperature [0.7]: ").strip()
        temperature = float(temperature) if temperature else 0.7

        llm_config = LLMConfig(
            provider=provider, base_url=base_url, model=model, temperature=temperature
        )

        # Configuración Cerebro (usar defaults)
        brain_config = CompleteBrainConfig(
            dim_observation=384,
            dim_latent=64,
            dim_working_memory=32,
            dim_action=16,
            max_episodes=1000,
            max_concepts=200,
            enable_learning=True,
            enable_homeostasis=True,
            enable_sleep=True,
            sleep_interval=50,
        )

        print("\n⏳ Inicializando sistema...\n")

        try:
            self.system = GovernedLocalLLM(llm_config, brain_config)
            print("\n✅ Sistema inicializado correctamente\n")
            return True
        except Exception as e:
            print(f"\n❌ Error al inicializar: {e}\n")
            return False

    def process_command(self, user_input: str) -> bool:
        """
        Procesa comando especial.

        Returns:
            bool: True si debe continuar, False si debe salir
        """
        cmd = user_input.strip().lower()

        if cmd == "/help":
            self.print_help()

        elif cmd == "/stats":
            self.print_stats()

        elif cmd == "/config":
            self.print_config()

        elif cmd == "/sleep":
            self.force_sleep()

        elif cmd == "/history":
            self.show_history()

        elif cmd == "/export":
            self.export_stats()

        elif cmd == "/reset":
            confirm = input("⚠️  ¿Seguro que quieres resetear el cerebro? (s/n): ")
            if confirm.lower() == "s":
                if self.initialize_system():
                    print("✅ Cerebro reseteado\n")

        elif cmd == "/exit":
            print("\n👋 ¡Hasta luego!\n")
            return False

        else:
            print(f"\n⚠️  Comando desconocido: {cmd}")
            print("Escribe /help para ver comandos disponibles\n")

        return True

    def run(self):
        """Ejecuta el loop principal de la CLI"""
        self.print_banner()

        # Inicializar sistema
        if not self.initialize_system():
            return

        self.running = True

        # Loop principal
        while self.running:
            try:
                # Leer input
                user_input = input("🧑 Tú: ").strip()

                if not user_input:
                    continue

                # Comandos especiales
                if user_input.startswith("/"):
                    self.running = self.process_command(user_input)
                    continue

                # Procesar mensaje normal
                print()  # Nueva línea
                result = self.system.chat(user_input)

                # Mostrar respuesta
                if result["approved"]:
                    print(f"\n🤖 IA: {result['response']}\n")
                    print(f"   ⏱️  Tiempo: {result['elapsed_time']:.2f}s")
                    print(
                        f"   ✓ Confianza: {result['brain_state']['metrics']['confidence']:.2f}"
                    )
                else:
                    print(f"\n⛔ IA: {result['response']}\n")
                    print(f"   Razón: Respuesta bloqueada por gobernanza AMA-G")
                    if not result.get("intent_preserved", True):
                        print(f"   ⚠️  Intención no preservada")

                print()

            except KeyboardInterrupt:
                print("\n\n👋 Saliendo...\n")
                break

            except Exception as e:
                print(f"\n❌ Error: {e}\n")
                continue


# =========================
# Entry Point
# =========================

if __name__ == "__main__":
    cli = InteractiveCLI()
    cli.run()
