"""
Image Service - MiniMax Integration
====================================

Servicio para generación de imágenes usando MiniMax.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any, List


class ImageService:
    """
    Servicio de generación de imágenes que utiliza MiniMax.

    Este servicio proporciona capacidades de text-to-image para visualización
    de grafos de conocimiento, diagramas de arquitectura y otros elementos visuales.
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Inicializa el servicio de imágenes.

        Args:
            output_dir: Directorio donde se guardarán las imágenes generadas.
                       Por defecto: ./ama_data/images/
        """
        if output_dir is None:
            output_dir = str(Path(__file__).parent.parent / "ama_data" / "images")

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        n: int = 1,
        optimize_prompt: bool = True,
    ) -> Dict[str, Any]:
        """
        Genera una imagen a partir de un prompt de texto.

        Args:
            prompt: Descripción de la imagen a generar
            aspect_ratio: Relación de aspecto ("1:1", "16:9", "4:3", "3:2", etc.)
            n: Número de imágenes a generar (1-9)
            optimize_prompt: Si se debe optimizar el prompt automáticamente

        Returns:
            Dict con información sobre las imágenes generadas
        """
        args = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "n": n,
            "prompt_optimizer": optimize_prompt,
            "output_directory": str(self.output_dir),
        }

        try:
            result = subprocess.run(
                [
                    "manus-mcp-cli",
                    "tool",
                    "call",
                    "text_to_image",
                    "--server",
                    "minimax",
                    "--input",
                    json.dumps(args),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            return {
                "success": True,
                "output": result.stdout.strip(),
                "output_dir": str(self.output_dir),
                "prompt": prompt,
                "count": n,
            }

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": str(e),
                "stderr": e.stderr,
            }

    def generate_architecture_diagram(
        self, components: List[str], relationships: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Genera un diagrama de arquitectura basado en componentes y relaciones.

        Args:
            components: Lista de nombres de componentes
            relationships: Lista de diccionarios con 'from', 'to', 'type'

        Returns:
            Dict con información sobre el diagrama generado
        """
        # Construir prompt descriptivo
        prompt = f"Professional software architecture diagram showing {len(components)} components: "
        prompt += ", ".join(components)
        prompt += ". "

        if relationships:
            prompt += "Connections: "
            for rel in relationships:
                prompt += f"{rel['from']} {rel.get('type', 'connects to')} {rel['to']}, "

        prompt += (
            "Clean, modern design with clear labels, arrows showing data flow, "
            "technical illustration style, white background, high contrast"
        )

        return self.generate_image(prompt=prompt, aspect_ratio="16:9")

    def generate_knowledge_graph_visualization(
        self, nodes: List[str], edges: List[Dict[str, str]], title: str = "Knowledge Graph"
    ) -> Dict[str, Any]:
        """
        Genera una visualización de un grafo de conocimiento.

        Args:
            nodes: Lista de nodos del grafo
            edges: Lista de aristas con 'source' y 'target'
            title: Título del grafo

        Returns:
            Dict con información sobre la visualización generada
        """
        prompt = f"Knowledge graph visualization titled '{title}' with {len(nodes)} nodes: "
        prompt += ", ".join(nodes[:10])  # Limitar a 10 para no saturar el prompt

        if len(nodes) > 10:
            prompt += f" and {len(nodes) - 10} more nodes"

        prompt += f". {len(edges)} connections between nodes. "
        prompt += (
            "Network diagram style, nodes as circles with labels, "
            "edges as lines with arrows, hierarchical layout, "
            "colorful but professional, clear and readable"
        )

        return self.generate_image(prompt=prompt, aspect_ratio="16:9")

    def generate_icon(
        self, description: str, style: str = "modern"
    ) -> Dict[str, Any]:
        """
        Genera un icono basado en una descripción.

        Args:
            description: Descripción del icono
            style: Estilo del icono ("modern", "flat", "3d", "minimalist")

        Returns:
            Dict con información sobre el icono generado
        """
        prompt = f"{style} icon of {description}, simple, clean design, "
        prompt += "centered on white background, professional, high quality"

        return self.generate_image(prompt=prompt, aspect_ratio="1:1", n=1)

    def generate_dashboard_widget_background(
        self, theme: str = "dark", color_scheme: str = "blue"
    ) -> Dict[str, Any]:
        """
        Genera un fondo para widgets del dashboard.

        Args:
            theme: Tema ("dark", "light")
            color_scheme: Esquema de color ("blue", "green", "purple", "orange")

        Returns:
            Dict con información sobre el fondo generado
        """
        prompt = f"Abstract {theme} theme background with {color_scheme} gradient, "
        prompt += (
            "subtle geometric patterns, modern and professional, "
            "suitable for dashboard widget, smooth gradients, "
            "not too busy, elegant and clean"
        )

        return self.generate_image(prompt=prompt, aspect_ratio="16:9", n=1)

    def generate_project_logo(
        self, project_name: str, project_description: str
    ) -> Dict[str, Any]:
        """
        Genera un logo para un proyecto.

        Args:
            project_name: Nombre del proyecto
            project_description: Descripción breve del proyecto

        Returns:
            Dict con información sobre el logo generado
        """
        prompt = f"Professional logo for '{project_name}', a project about {project_description}. "
        prompt += (
            "Modern, clean design, memorable, scalable, "
            "suitable for software/tech, vector style, "
            "on white background"
        )

        return self.generate_image(prompt=prompt, aspect_ratio="1:1", n=3)


# Ejemplo de uso
if __name__ == "__main__":
    image_service = ImageService()

    # Test 1: Generar diagrama de arquitectura
    print("Test 1: Diagrama de arquitectura de AMA-Intent")
    components = [
        "Dashboard",
        "Core Cognitivo",
        "Knowledge Graph",
        "Plugins",
        "Base de Datos",
    ]
    relationships = [
        {"from": "Dashboard", "to": "Core Cognitivo", "type": "uses"},
        {"from": "Core Cognitivo", "to": "Knowledge Graph", "type": "queries"},
        {"from": "Core Cognitivo", "to": "Plugins", "type": "manages"},
        {"from": "Dashboard", "to": "Base de Datos", "type": "stores data in"},
    ]

    result = image_service.generate_architecture_diagram(components, relationships)
    print(f"Resultado: {result}")

    # Test 2: Generar icono para el sistema
    print("\nTest 2: Icono del sistema")
    icon_result = image_service.generate_icon(
        description="artificial brain with neural connections", style="modern"
    )
    print(f"Icono: {icon_result}")

    # Test 3: Generar logo del proyecto
    print("\nTest 3: Logo del proyecto")
    logo_result = image_service.generate_project_logo(
        project_name="AMA-Intent",
        project_description="biomimetic artificial intelligence system for task orchestration",
    )
    print(f"Logo: {logo_result}")
