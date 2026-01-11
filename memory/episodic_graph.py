# brain_gui.py - Interfaz Gráfica del Cerebro Artificial
"""
GUI moderna para el Cerebro Artificial con IA Local.

Características:
- Chat en tiempo real
- Visualización de métricas del cerebro
- Gráficos de estado en vivo
- Panel de configuración
- Estadísticas detalladas
"""

import queue
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Dict, Optional

# Importar módulos del cerebro
from ollama_brain_interface import CompleteBrainConfig, GovernedLocalLLM, LLMConfig


class BrainGUI:
    """
    Interfaz Gráfica Principal del Cerebro Artificial.
    """

    def __init__(self, root: tk.Tk):
        """
        Args:
            root: ventana principal de Tkinter
        """
        self.root = root
        self.root.title("🧠 Cerebro Artificial - IA Local Gobernada")
        self.root.geometry("1400x900")

        # Sistema
        self.system: Optional[GovernedLocalLLM] = None
        self.processing = False

        # Cola para comunicación entre threads
        self.message_queue = queue.Queue()

        # Colores modernos
        self.colors = {
            "bg": "#1e1e1e",
            "fg": "#ffffff",
            "accent": "#007acc",
            "success": "#4caf50",
            "warning": "#ff9800",
            "error": "#f44336",
            "panel": "#252526",
            "input": "#3c3c3c",
        }

        # Configurar estilo
        self.setup_styles()

        # Construir interfaz
        self.build_ui()

        # Inicializar sistema en segundo plano
        self.initialize_system_async()

    def setup_styles(self):
        """Configura estilos de la interfaz"""
        style = ttk.Style()
        style.theme_use("clam")

        # Configurar colores
        self.root.configure(bg=self.colors["bg"])

        style.configure("TFrame", background=self.colors["bg"])
        style.configure(
            "TLabel", background=self.colors["bg"], foreground=self.colors["fg"]
        )
        style.configure(
            "TButton", background=self.colors["accent"], foreground=self.colors["fg"]
        )
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Metric.TLabel", font=("Segoe UI", 12))
        style.configure("Status.TLabel", font=("Segoe UI", 10))

    def build_ui(self):
        """Construye la interfaz de usuario"""

        # ==========================================
        # PANEL SUPERIOR: Header
        # ==========================================
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=10, pady=10)

        title_label = ttk.Label(
            header_frame,
            text="🧠 CEREBRO ARTIFICIAL - IA LOCAL GOBERNADA",
            style="Header.TLabel",
        )
        title_label.pack(side="left")

        self.status_label = ttk.Label(
            header_frame,
            text="⏳ Inicializando...",
            style="Status.TLabel",
            foreground=self.colors["warning"],
        )
        self.status_label.pack(side="right")

        # ==========================================
        # CONTENEDOR PRINCIPAL (3 columnas)
        # ==========================================
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Columna 1: Chat (50%)
        chat_frame = self.create_chat_panel(main_container)
        chat_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        # Columna 2: Métricas (25%)
        metrics_frame = self.create_metrics_panel(main_container)
        metrics_frame.grid(row=0, column=1, sticky="nsew", padx=5)

        # Columna 3: Estado del Cerebro (25%)
        brain_frame = self.create_brain_panel(main_container)
        brain_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))

        # Configurar pesos de columnas
        main_container.columnconfigure(0, weight=2)
        main_container.columnconfigure(1, weight=1)
        main_container.columnconfigure(2, weight=1)
        main_container.rowconfigure(0, weight=1)

        # ==========================================
        # PANEL INFERIOR: Controles
        # ==========================================
        control_frame = self.create_control_panel(self.root)
        control_frame.pack(fill="x", padx=10, pady=10)

    def create_chat_panel(self, parent) -> ttk.Frame:
        """Crea panel de chat"""
        frame = ttk.Frame(parent)

        # Header
        header = ttk.Label(frame, text="💬 Conversación", style="Header.TLabel")
        header.pack(anchor="w", pady=(0, 10))

        # Área de chat
        chat_container = tk.Frame(frame, bg=self.colors["panel"])
        chat_container.pack(fill="both", expand=True)

        self.chat_display = scrolledtext.ScrolledText(
            chat_container,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=self.colors["panel"],
            fg=self.colors["fg"],
            insertbackground=self.colors["fg"],
            state="disabled",
            relief="flat",
            padx=10,
            pady=10,
        )
        self.chat_display.pack(fill="both", expand=True)

        # Configurar tags para colores
        self.chat_display.tag_config(
            "user", foreground="#61afef", font=("Consolas", 10, "bold")
        )
        self.chat_display.tag_config("assistant", foreground="#98c379")
        self.chat_display.tag_config(
            "system", foreground="#e5c07b", font=("Consolas", 9, "italic")
        )
        self.chat_display.tag_config("error", foreground=self.colors["error"])

        # Input
        input_frame = tk.Frame(frame, bg=self.colors["bg"])
        input_frame.pack(fill="x", pady=(10, 0))

        self.input_text = tk.Text(
            input_frame,
            height=3,
            font=("Segoe UI", 10),
            bg=self.colors["input"],
            fg=self.colors["fg"],
            insertbackground=self.colors["fg"],
            relief="flat",
            padx=10,
            pady=10,
        )
        self.input_text.pack(side="left", fill="both", expand=True)
        self.input_text.bind("<Return>", self.on_send_message)
        self.input_text.bind(
            "<Shift-Return>", lambda e: None
        )  # Allow newline with Shift+Enter

        send_btn = tk.Button(
            input_frame,
            text="Enviar",
            command=self.on_send_message,
            bg=self.colors["accent"],
            fg=self.colors["fg"],
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=20,
            cursor="hand2",
        )
        send_btn.pack(side="right", padx=(10, 0))

        return frame

    def create_metrics_panel(self, parent) -> ttk.Frame:
        """Crea panel de métricas en vivo"""
        frame = ttk.Frame(parent)

        # Header
        header = ttk.Label(frame, text="📊 Métricas en Vivo", style="Header.TLabel")
        header.pack(anchor="w", pady=(0, 10))

        # Contenedor de métricas
        metrics_container = tk.Frame(frame, bg=self.colors["panel"], relief="flat")
        metrics_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Crear indicadores
        self.metrics_labels = {}

        metrics = [
            ("confidence", "🎯 Confianza", "0.00"),
            ("surprise", "⚡ Sorpresa", "0.00"),
            ("attention", "👁️ Atención", "0.00"),
            ("episodes", "💾 Episodios", "0"),
            ("concepts", "🧩 Conceptos", "0"),
            ("wm_slots", "🔄 WM Slots", "0"),
            ("ticks", "⏱️ Ticks", "0"),
        ]

        for i, (key, label, default) in enumerate(metrics):
            # Label
            lbl = tk.Label(
                metrics_container,
                text=label,
                font=("Segoe UI", 10, "bold"),
                bg=self.colors["panel"],
                fg=self.colors["fg"],
                anchor="w",
            )
            lbl.grid(row=i, column=0, sticky="w", padx=10, pady=5)

            # Value
            val = tk.Label(
                metrics_container,
                text=default,
                font=("Segoe UI", 12),
                bg=self.colors["panel"],
                fg=self.colors["accent"],
                anchor="e",
            )
            val.grid(row=i, column=1, sticky="e", padx=10, pady=5)

            self.metrics_labels[key] = val

        metrics_container.columnconfigure(1, weight=1)

        return frame

    def create_brain_panel(self, parent) -> ttk.Frame:
        """Crea panel de estado del cerebro"""
        frame = ttk.Frame(parent)

        # Header
        header = ttk.Label(frame, text="🧠 Estado del Cerebro", style="Header.TLabel")
        header.pack(anchor="w", pady=(0, 10))

        # Contenedor
        brain_container = tk.Frame(frame, bg=self.colors["panel"], relief="flat")
        brain_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Barra de progreso de confianza
        conf_label = tk.Label(
            brain_container,
            text="Confianza del Sistema",
            font=("Segoe UI", 9),
            bg=self.colors["panel"],
            fg=self.colors["fg"],
        )
        conf_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.confidence_bar = ttk.Progressbar(
            brain_container, length=200, mode="determinate", maximum=100
        )
        self.confidence_bar.pack(fill="x", padx=10, pady=(0, 15))

        # Estado de fases
        phases_label = tk.Label(
            brain_container,
            text="Estado de Fases",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["panel"],
            fg=self.colors["fg"],
        )
        phases_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.phase_indicators = {}
        phases = ["Sensing", "Attention", "Memory", "Decision", "Governance"]

        for phase in phases:
            phase_frame = tk.Frame(brain_container, bg=self.colors["panel"])
            phase_frame.pack(fill="x", padx=10, pady=2)

            indicator = tk.Label(
                phase_frame,
                text="●",
                font=("Segoe UI", 12),
                bg=self.colors["panel"],
                fg="gray",
            )
            indicator.pack(side="left")

            label = tk.Label(
                phase_frame,
                text=phase,
                font=("Segoe UI", 9),
                bg=self.colors["panel"],
                fg=self.colors["fg"],
            )
            label.pack(side="left", padx=5)

            self.phase_indicators[phase] = indicator

        # Log de eventos
        log_label = tk.Label(
            brain_container,
            text="📝 Log de Eventos",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["panel"],
            fg=self.colors["fg"],
        )
        log_label.pack(anchor="w", padx=10, pady=(15, 5))

        self.event_log = scrolledtext.ScrolledText(
            brain_container,
            height=10,
            font=("Consolas", 8),
            bg="#1a1a1a",
            fg="#b0b0b0",
            state="disabled",
            relief="flat",
            padx=5,
            pady=5,
        )
        self.event_log.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        return frame

    def create_control_panel(self, parent) -> ttk.Frame:
        """Crea panel de controles"""
        frame = tk.Frame(parent, bg=self.colors["bg"])

        # Botones de control
        btn_style = {
            "font": ("Segoe UI", 9),
            "relief": "flat",
            "cursor": "hand2",
            "padx": 15,
            "pady": 5,
        }

        stats_btn = tk.Button(
            frame,
            text="📊 Estadísticas",
            command=self.show_statistics,
            bg=self.colors["accent"],
            fg=self.colors["fg"],
            **btn_style,
        )
        stats_btn.pack(side="left", padx=5)

        sleep_btn = tk.Button(
            frame,
            text="💤 Forzar Sueño",
            command=self.force_sleep,
            bg="#9c27b0",
            fg=self.colors["fg"],
            **btn_style,
        )
        sleep_btn.pack(side="left", padx=5)

        clear_btn = tk.Button(
            frame,
            text="🗑️ Limpiar Chat",
            command=self.clear_chat,
            bg="#607d8b",
            fg=self.colors["fg"],
            **btn_style,
        )
        clear_btn.pack(side="left", padx=5)

        config_btn = tk.Button(
            frame,
            text="⚙️ Configuración",
            command=self.show_config,
            bg="#607d8b",
            fg=self.colors["fg"],
            **btn_style,
        )
        config_btn.pack(side="left", padx=5)

        # Info de versión
        version_label = tk.Label(
            frame,
            text="v1.0.0 | FASE 1+2+3 Completas",
            font=("Segoe UI", 8),
            bg=self.colors["bg"],
            fg="gray",
        )
        version_label.pack(side="right")

        return frame

    def initialize_system_async(self):
        """Inicializa el sistema en un thread separado"""

        def init():
            try:
                self.log_event("Iniciando sistema...")

                llm_config = LLMConfig(
                    provider="ollama",
                    base_url="http://localhost:11434",
                    model="gemma2:2b",
                    temperature=0.7,
                )

                brain_config = CompleteBrainConfig(
                    dim_observation=384,
                    dim_latent=64,
                    dim_working_memory=32,
                    dim_action=16,
                    max_episodes=500,
                    max_concepts=100,
                    enable_learning=True,
                    enable_homeostasis=True,
                    enable_sleep=True,
                    sleep_interval=50,
                )

                self.system = GovernedLocalLLM(llm_config, brain_config)

                self.root.after(
                    0,
                    lambda: self.status_label.config(
                        text="✅ Sistema Listo", foreground=self.colors["success"]
                    ),
                )

                self.log_event("✅ Sistema inicializado correctamente")
                self.add_chat_message(
                    "system", "Sistema inicializado. ¡Listo para conversar!"
                )

            except Exception as e:
                self.root.after(
                    0,
                    lambda: self.status_label.config(
                        text="❌ Error de Inicialización",
                        foreground=self.colors["error"],
                    ),
                )
                self.log_event(f"❌ Error: {str(e)}")
                messagebox.showerror(
                    "Error", f"No se pudo inicializar el sistema:\n{str(e)}"
                )

        thread = threading.Thread(target=init, daemon=True)
        thread.start()

    def on_send_message(self, event=None):
        """Maneja envío de mensaje"""
        if event and event.keysym == "Return" and not event.state & 0x1:  # Sin Shift
            message = self.input_text.get("1.0", "end-1c").strip()

            if not message:
                return "break"

            if not self.system:
                messagebox.showwarning(
                    "Aviso", "El sistema aún no está listo. Espera unos segundos."
                )
                return "break"

            if self.processing:
                messagebox.showinfo(
                    "Info", "Ya hay un mensaje en proceso. Espera a que termine."
                )
                return "break"

            # Limpiar input
            self.input_text.delete("1.0", "end")

            # Mostrar mensaje del usuario
            self.add_chat_message("user", message)

            # Procesar en thread separado
            self.processing = True
            thread = threading.Thread(
                target=self.process_message, args=(message,), daemon=True
            )
            thread.start()

            return "break"

    def process_message(self, message: str):
        """Procesa mensaje en segundo plano"""
        try:
            self.log_event(f"Procesando: {message[:30]}...")

            # Actualizar fases
            self.update_phase_indicators("all", "processing")

            # Procesar con el sistema
            result = self.system.chat(message)

            # Actualizar UI
            self.root.after(0, lambda: self.handle_response(result))

        except Exception as e:
            self.root.after(
                0,
                lambda e_val=e: self.add_chat_message("error", f"Error: {str(e_val)}"),
            )
            self.log_event(f"❌ Error en procesamiento: {str(e)}")

        finally:
            self.processing = False
            self.update_phase_indicators("all", "idle")

    def handle_response(self, result: Dict):
        """Maneja respuesta del sistema"""
        if result["approved"]:
            self.add_chat_message("assistant", result["response"])
            self.log_event(
                f"✅ Respuesta aprobada (conf: {result['brain_state']['metrics']['confidence']:.2f})"
            )
        else:
            self.add_chat_message("error", result["response"])
            self.log_event(f"⚠️ Respuesta bloqueada")

        # Actualizar métricas
        self.update_metrics(result["brain_state"]["metrics"])

        # Info adicional
        info = f"⏱️ {result['elapsed_time']:.2f}s | 🎯 Confianza: {result['brain_state']['metrics']['confidence']:.2f}"
        self.add_chat_message("system", info)

    def add_chat_message(self, sender: str, message: str):
        """Añade mensaje al chat"""
        self.chat_display.config(state="normal")

        if sender == "user":
            self.chat_display.insert("end", "🧑 Tú: ", "user")
        elif sender == "assistant":
            self.chat_display.insert("end", "🤖 IA: ", "assistant")
        elif sender == "system":
            self.chat_display.insert("end", "ℹ️ ", "system")
        elif sender == "error":
            self.chat_display.insert("end", "⚠️ ", "error")

        self.chat_display.insert("end", f"{message}\n\n", sender)
        self.chat_display.see("end")
        self.chat_display.config(state="disabled")

    def update_metrics(self, metrics: Dict):
        """Actualiza panel de métricas"""
        self.metrics_labels["confidence"].config(
            text=f"{metrics.get('confidence', 0):.2f}"
        )
        self.metrics_labels["surprise"].config(text=f"{metrics.get('surprise', 0):.2f}")
        self.metrics_labels["attention"].config(
            text=f"{metrics.get('attention_focus', 0):.2f}"
        )
        self.metrics_labels["episodes"].config(text=str(metrics.get("episodes", 0)))
        self.metrics_labels["concepts"].config(text=str(metrics.get("concepts", 0)))
        self.metrics_labels["wm_slots"].config(text=str(metrics.get("wm_slots", 0)))
        self.metrics_labels["ticks"].config(text=str(metrics.get("tick", 0)))

        # Actualizar barra de confianza
        confidence_pct = metrics.get("confidence", 0) * 100
        self.confidence_bar["value"] = confidence_pct

    def update_phase_indicators(self, phase: str, state: str):
        """Actualiza indicadores de fase"""
        colors = {
            "idle": "gray",
            "processing": self.colors["warning"],
            "success": self.colors["success"],
            "error": self.colors["error"],
        }

        color = colors.get(state, "gray")

        if phase == "all":
            for indicator in self.phase_indicators.values():
                indicator.config(fg=color)
        elif phase in self.phase_indicators:
            self.phase_indicators[phase].config(fg=color)

    def log_event(self, message: str):
        """Añade evento al log"""
        timestamp = time.strftime("%H:%M:%S")
        self.event_log.config(state="normal")
        self.event_log.insert("end", f"[{timestamp}] {message}\n")
        self.event_log.see("end")
        self.event_log.config(state="disabled")

    def show_statistics(self):
        messagebox.showinfo("Estadísticas", "Funcionalidad en desarrollo")

    def force_sleep(self):
        if self.system:
            self.system.brain.sleep()
            self.log_event("💤 Sueño forzado ejecutado")

    def clear_chat(self):
        self.chat_display.config(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.config(state="disabled")

    def show_config(self):
        messagebox.showinfo("Configuración", "Funcionalidad en desarrollo")


if __name__ == "__main__":
    root = tk.Tk()
    app = BrainGUI(root)
    root.mainloop()
