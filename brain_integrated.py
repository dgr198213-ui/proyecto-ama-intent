# install.py - Script de Instalación Automatizada
"""
Script para instalar y configurar el Cerebro Artificial automáticamente.

Uso:
    python install.py
"""

import json
import os
import platform
import subprocess
import sys
import urllib.request


class Colors:
    """Códigos de color ANSI"""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(text):
    """Imprime header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}")
    print(f"{text}")
    print(f"{'='*70}{Colors.ENDC}\n")


def print_step(step, text):
    """Imprime paso"""
    print(f"{Colors.OKBLUE}[{step}]{Colors.ENDC} {text}")


def print_success(text):
    """Imprime éxito"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text):
    """Imprime error"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text):
    """Imprime advertencia"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def check_python_version():
    """Verifica versión de Python"""
    print_step("1/6", "Verificando versión de Python...")

    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python {version.major}.{version.minor} detectado")
        print_error("Se requiere Python 3.8 o superior")
        return False

    print_success(f"Python {version.major}.{version.minor}.{version.micro} OK")
    return True


def check_ollama():
    """Verifica si Ollama está instalado"""
    print_step("2/6", "Verificando Ollama...")

    try:
        # Intentar conectar al servidor
        response = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        if response.status == 200:
            print_success("Ollama está ejecutándose")

            # Listar modelos
            data = json.loads(response.read())
            models = data.get("models", [])

            if models:
                print_success(f"Modelos disponibles: {len(models)}")
                for model in models[:3]:
                    print(f"  - {model.get('name', 'Unknown')}")
                if len(models) > 3:
                    print(f"  ... y {len(models) - 3} más")
            else:
                print_warning("No hay modelos descargados")
                print("Ejecuta: ollama pull gemma2:2b")

            return True

    except:
        print_warning("Ollama no está ejecutándose")
        print("Opciones:")
        print("  1. Instalar Ollama desde: https://ollama.ai")
        print("  2. Iniciar Ollama: ollama serve")
        print("  3. O usar LM Studio como alternativa")

        choice = input("\n¿Continuar sin Ollama? (s/n): ").lower()
        return choice == "s"


def install_dependencies():
    """Instala dependencias de Python"""
    print_step("3/6", "Instalando dependencias...")

    dependencies = ["numpy", "requests"]

    optional_deps = ["sentence-transformers", "scikit-learn"]

    # Instalar dependencias principales
    print("Instalando paquetes principales...")
    for dep in dependencies:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", dep, "-q"],
                stdout=subprocess.DEVNULL,
            )
            print_success(f"{dep} instalado")
        except:
            print_error(f"Error instalando {dep}")
            return False

    # Preguntar por dependencias opcionales
    print("\nDependencias opcionales (mejoran embeddings):")
    print("  - sentence-transformers")
    print("  - scikit-learn")

    install_optional = input("\n¿Instalar dependencias opcionales? (s/n): ").lower()

    if install_optional == "s":
        print("\nInstalando dependencias opcionales...")
        for dep in optional_deps:
            try:
                print(f"Instalando {dep}... (puede tardar unos minutos)")
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", dep],
                    stdout=subprocess.DEVNULL,
                )
                print_success(f"{dep} instalado")
            except:
                print_warning(f"No se pudo instalar {dep} (opcional)")

    print_success("Dependencias instaladas")
    return True


def create_project_structure():
    """Crea estructura de directorios"""
    print_step("4/6", "Creando estructura del proyecto...")

    directories = [
        "sensing",
        "cortex",
        "memory",
        "decision",
        "governance",
        "control",
        "learning",
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

        # Crear __init__.py
        init_file = os.path.join(directory, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write(f'"""Módulo {directory}"""\n')

    print_success("Estructura creada")
    return True


def create_launcher():
    """Crea script de inicio"""
    print_step("5/6", "Creando launcher...")

    launcher_content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Launcher del Cerebro Artificial
\"\"\"

import sys
import os

# Añadir path del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Cerebro Artificial - IA Local Gobernada')
    parser.add_argument('--cli', action='store_true', help='Modo CLI (terminal)')
    parser.add_argument('--gui', action='store_true', help='Modo GUI (interfaz gráfica)')
    parser.add_argument('--version', action='version', version='Cerebro Artificial v1.0.0')
    
    args = parser.parse_args()
    
    if args.cli:
        print("Iniciando modo CLI...")
        from cli_interactive import InteractiveCLI
        cli = InteractiveCLI()
        cli.run()
    
    elif args.gui:
        print("Iniciando modo GUI...")
        try:
            import tkinter as tk
            from brain_gui import BrainGUI
            
            root = tk.Tk()
            app = BrainGUI(root)
            root.mainloop()
        
        except ImportError:
            print("Error: tkinter no está instalado")
            print("Instálalo con: sudo apt-get install python3-tk (Linux)")
            print("O usa --cli para modo terminal")
    
    else:
        # Por defecto, intentar GUI
        try:
            import tkinter as tk
            from brain_gui import BrainGUI
            
            root = tk.Tk()
            app = BrainGUI(root)
            root.mainloop()
        
        except ImportError:
            print("tkinter no disponible, iniciando CLI...")
            from cli_interactive import InteractiveCLI
            cli = InteractiveCLI()
            cli.run()

if __name__ == "__main__":
    main()
"""

    with open("start.py", "w", encoding="utf-8") as f:
        f.write(launcher_content)

    # Hacer ejecutable en Unix
    if platform.system() != "Windows":
        os.chmod("start.py", 0o755)

    print_success("Launcher creado: start.py")
    return True


def create_readme():
    """Crea README con instrucciones"""
    print_step("6/6", "Creando documentación...")

    readme_content = """# 🧠 Cerebro Artificial - IA Local Gobernada

Sistema de IA local completamente gobernado con arquitectura biomimética.

## 🚀 Inicio Rápido

### Modo GUI (Recomendado)
```bash
python start.py --gui
```

### Modo CLI (Terminal)
```bash
python start.py --cli
```

### Sin argumentos (auto-detecta)
```bash
python start.py
```

## 📋 Requisitos

- Python 3.8+
- Ollama o LM Studio
- 8 GB RAM (16 GB recomendado)

## 🔧 Configuración

### Ollama
```bash
# Instalar desde https://ollama.ai

# Descargar modelo
ollama pull gemma2:2b

# Iniciar servidor
ollama serve
```

### LM Studio
1. Descargar desde https://lmstudio.ai
2. Descargar modelo desde la interfaz
3. Iniciar servidor local

## 📚 Documentación

Ver `INSTALL.md` para instalación detallada.

## 🎯 Características

- ✅ Gobernanza AMA-G en cada interacción
- ✅ Memoria episódica y semántica
- ✅ Aprendizaje continuo
- ✅ Homeostasis automática
- ✅ Consolidación nocturna ("sueño")
- ✅ 100% local y privado

## 📊 Arquitectura

```
FASE 1: Percepción + Decisión + Gobernanza
FASE 2: Memoria (Episódica/Semántica/Working)
FASE 3: Aprendizaje (PID/Loss/Estabilidad/Sueño)
```

## 🛠️ Comandos

### CLI
- `/help` - Ayuda
- `/stats` - Estadísticas
- `/sleep` - Forzar consolidación
- `/exit` - Salir

### GUI
- Botones en la interfaz para todas las funciones

## 📝 Versión

v1.0.0 - Sistema completo funcional
"""

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    print_success("README.md creado")
    return True


def main():
    """Función principal"""
    print_header("🧠 INSTALACIÓN DEL CEREBRO ARTIFICIAL")

    print("Este script configurará automáticamente el sistema.")
    print("Estimado: 5-10 minutos\n")

    input("Presiona Enter para continuar...")

    # Paso 1: Verificar Python
    if not check_python_version():
        print_error("\nInstalación abortada: Python no compatible")
        return 1

    # Paso 2: Verificar Ollama
    if not check_ollama():
        print_warning("\nContinuando sin Ollama...")

    # Paso 3: Instalar dependencias
    if not install_dependencies():
        print_error("\nInstalación abortada: Error en dependencias")
        return 1

    # Paso 4: Crear estructura
    if not create_project_structure():
        print_error("\nInstalación abortada: Error creando estructura")
        return 1

    # Paso 5: Crear launcher
    if not create_launcher():
        print_error("\nInstalación abortada: Error creando launcher")
        return 1

    # Paso 6: Crear README
    if not create_readme():
        print_warning("\nAdvertencia: No se pudo crear README")

    # Finalización
    print_header("✅ INSTALACIÓN COMPLETADA")

    print("El sistema está listo para usar.\n")
    print("📝 PRÓXIMOS PASOS:")
    print("\n1. Asegúrate de que Ollama esté ejecutándose:")
    print("   ollama serve")
    print("\n2. Descarga un modelo (si no lo has hecho):")
    print("   ollama pull gemma2:2b")
    print("\n3. Inicia el sistema:")
    print("   python start.py --gui    (interfaz gráfica)")
    print("   python start.py --cli    (terminal)")
    print("\n4. ¡Disfruta de tu IA local gobernada! 🚀")

    # Preguntar si iniciar ahora
    print("\n" + "=" * 70)
    start_now = input("\n¿Iniciar el sistema ahora? (s/n): ").lower()

    if start_now == "s":
        print("\nIniciando...")
        try:
            subprocess.call([sys.executable, "start.py"])
        except:
            print_error("Error al iniciar. Ejecuta manualmente: python start.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
