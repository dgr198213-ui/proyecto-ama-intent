import os
import subprocess
import sys


def main():
    print("🧠 Iniciando Protocolo AMA-Intent v3...")

    # Verificar que existe la carpeta data
    if not os.path.exists("data"):
        os.makedirs("data")
        print("📁 Carpeta de memoria creada.")

    # Verificar Ollama (solución pragmática)
    try:
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            print("❌ ERROR: Ollama no parece estar instalado o corriendo.")
            print("👉 Ejecuta 'ollama serve' en otra terminal.")
            sys.exit(1)
    except FileNotFoundError:
        print("❌ ERROR: Ollama no está instalado.")
        print("👉 Instala Ollama desde https://ollama.ai")
        sys.exit(1)

    # Lanzar puente
    print("🚀 Levantando el puente neuronal en puerto 5001...")
    try:
        subprocess.run([sys.executable, "-m", "bridge.server"], check=True)
    except KeyboardInterrupt:
        print("\n✅ Sistema detenido correctamente.")
    except Exception as e:
        print(f"❌ Error al iniciar el servidor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
