import os
import sys


def main():
    print("🧠 Iniciando Protocolo AMA-Intent v3...")

    # Verificar que existe la carpeta data
    if not os.path.exists("data"):
        os.makedirs("data")
        print("📁 Carpeta de memoria creada.")

    # Verificar Ollama (solución pragmática)
    res = os.system("ollama list > /dev/null 2>&1")
    if res != 0:
        print("❌ ERROR: Ollama no parece estar instalado o corriendo.")
        print("👉 Ejecuta 'ollama serve' en otra terminal.")
        sys.exit(1)

    # Lanzar puente
    print("🚀 Levantando el puente neuronal en puerto 5001...")
    os.system("python bridge/server.py")


if __name__ == "__main__":
    main()
