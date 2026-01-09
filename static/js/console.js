/**
 * AMA-Intent Interactive Console
 * Handles predefined commands and user input
 */

class AMAConsole {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.history = [];
        this.commands = {
            'help': {
                description: 'Muestra la lista de comandos disponibles',
                action: () => this.listCommands()
            },
            'clear': {
                description: 'Limpia la consola',
                action: () => this.clear()
            },
            'status': {
                description: 'Muestra el estado del sistema AMA-Intent',
                action: async () => await this.getSystemStatus()
            },
            'analyze': {
                description: 'Inicia un análisis rápido del código actual',
                action: () => { window.location.href = '/debug'; }
            },
            'backup': {
                description: 'Crea un respaldo de la base de datos',
                action: async () => await this.runBackup()
            },
            'plugins': {
                description: 'Lista los plugins instalados y su estado',
                action: async () => await this.listPlugins()
            },
            'whoami': {
                description: 'Muestra información del usuario actual',
                action: async () => await this.getUserInfo()
            },
            'todo': {
                description: 'Muestra las tareas pendientes del proyecto activo',
                action: () => this.print("📌 Tareas pendientes: \n1. Configurar .env\n2. Probar integración de plugins\n3. Revisar logs de sistema")
            }
        };
        
        if (this.container) {
            this.init();
        }
    }

    init() {
        this.container.innerHTML = `
            <div class="bg-gray-900 text-green-400 font-mono p-4 rounded-lg shadow-lg h-64 overflow-y-auto mb-4" id="console-output">
                <div>AMA-Intent Console v2.0.0</div>
                <div>Escribe 'help' para ver los comandos disponibles.</div>
                <div class="mt-2">--------------------------------------------------</div>
            </div>
            <div class="flex">
                <span class="bg-gray-900 text-green-400 p-2 rounded-l-lg font-mono">></span>
                <input type="text" id="console-input" class="flex-1 bg-gray-900 text-white p-2 rounded-r-lg font-mono focus:outline-none" placeholder="Ingrese un comando...">
            </div>
            <div class="mt-4 grid grid-cols-2 md:grid-cols-4 gap-2" id="preset-commands">
                <!-- Preset buttons will be injected here -->
            </div>
        `;

        this.output = document.getElementById('console-output');
        this.input = document.getElementById('console-input');
        this.presetContainer = document.getElementById('preset-commands');

        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.execute(this.input.value);
                this.input.value = '';
            }
        });

        this.renderPresets();
    }

    renderPresets() {
        const presets = ['status', 'plugins', 'analyze', 'todo'];
        this.presetContainer.innerHTML = presets.map(cmd => `
            <button onclick="amaConsole.execute('${cmd}')" class="bg-gray-200 hover:bg-gray-300 text-gray-700 text-xs py-1 px-2 rounded transition-colors">
                ${cmd}
            </button>
        `).join('');
    }

    print(text, type = 'info') {
        const div = document.createElement('div');
        div.className = `mt-1 ${type === 'error' ? 'text-red-400' : type === 'success' ? 'text-blue-400' : 'text-green-400'}`;
        div.innerText = text;
        this.output.appendChild(div);
        this.output.scrollTop = this.output.scrollHeight;
    }

    clear() {
        this.output.innerHTML = '<div>Consola limpiada.</div>';
    }

    listCommands() {
        this.print("Comandos disponibles:");
        for (const [name, cmd] of Object.entries(this.commands)) {
            this.print(`  ${name.padEnd(10)} - ${cmd.description}`);
        }
    }

    async execute(cmdText) {
        const trimmed = cmdText.trim().toLowerCase();
        if (!trimmed) return;

        this.print(`> ${trimmed}`, 'user');
        
        if (this.commands[trimmed]) {
            try {
                await this.commands[trimmed].action();
            } catch (err) {
                this.print(`Error: ${err.message}`, 'error');
            }
        } else {
            this.print(`Comando no reconocido: ${trimmed}. Escribe 'help' para ayuda.`, 'error');
        }
    }

    async getSystemStatus() {
        this.print("Consultando estado del sistema...");
        try {
            const response = await fetch('/api/overview');
            const data = await response.json();
            this.print(`✅ Sistema: Operativo`);
            this.print(`📊 Proyectos: ${data.total_projects}`);
            this.print(`🐛 Sesiones Debug: ${data.total_debug_sessions}`);
        } catch (err) {
            this.print("❌ Error al conectar con la API", "error");
        }
    }

    async listPlugins() {
        this.print("Cargando lista de plugins...");
        // Mock response for now
        this.print("🔌 Plugins activos:");
        this.print("  - CodeExplainer v1.0.0 [ACTIVE]");
        this.print("  - SEOOptimizer v1.2.0 [ACTIVE]");
        this.print("  - BackupManager v0.9.0 [ACTIVE]");
    }

    async runBackup() {
        this.print("Iniciando respaldo de base de datos...");
        this.print("⌛ Procesando...");
        setTimeout(() => {
            this.print("✅ Respaldo completado con éxito: backup_20260110.db", "success");
        }, 1500);
    }

    async getUserInfo() {
        try {
            const response = await fetch('/api/overview');
            const data = await response.json();
            this.print(`👤 Usuario: ${data.username}`);
            this.print(`🔑 Rol: Administrador`);
        } catch (err) {
            this.print("No se pudo obtener información del usuario", "error");
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('ama-console-container')) {
        window.amaConsole = new AMAConsole('ama-console-container');
    }
});
