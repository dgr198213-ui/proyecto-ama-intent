import os
import subprocess
import sys

from dotenv import load_dotenv


def main():
    # Cargar variables de entorno
    load_dotenv()
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

        # Verificar si el modelo específico está descargado
        model = os.getenv("OLLAMA_MODEL", "llama3.1")
        if model not in result.stdout:
            print(f"⚠️ ADVERTENCIA: El modelo '{model}' no se encuentra en Ollama.")
            print(f"👉 Intenta descargarlo con: ollama pull {model}")
            # No salimos, tal vez 'ollama list' no mostró todo o el usuario sabe lo que hace
            # Pero damos el aviso claro
        else:
            print(f"✅ Modelo '{model}' verificado.")

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
