"""
Plugin: Code Companion (FIXED)
Análisis, ejecución y documentación de código
"""

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List


class CodeCompanionPlugin:
    """
    Plugin de asistencia de código

    Funciones:
    - Análisis de código
    - Ejecución de scripts
    - Generación de documentación (CORREGIDA)
    """

    def __init__(self):
        self.name = "code_companion"
        self.version = "1.1.0"
        self.supported_languages = ["python", "javascript", "bash"]

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Punto de entrada principal del plugin"""
        action = context.get("action", "analyze")

        if action == "analyze":
            return self.analyze_code(context.get("code", ""))
        elif action == "execute":
            return self.execute_code(
                context.get("code", ""), context.get("language", "python")
            )
        elif action == "document":
            return self.generate_docs(context.get("code", ""))
        else:
            return {"error": f"Unknown action: {action}"}

    def analyze_code(self, code: str) -> Dict[str, Any]:
        """Análisis básico de código"""
        if not code:
            return {"error": "No code provided"}

        lines = code.split("\n")

        analysis = {
            "lines": len(lines),
            "non_empty_lines": len([line for line in lines if line.strip()]),
            "comments": len([line for line in lines if line.strip().startswith("#")]),
            "functions": len([line for line in lines if "def " in line]),
            "classes": len([line for line in lines if "class " in line]),
            "imports": len(
                [line for line in lines if "import " in line or "from " in line]
            ),
        }

        # Detección de problemas comunes
        issues = []
        if analysis["lines"] > 500:
            issues.append("Code is very long (>500 lines), consider splitting")
        if analysis["comments"] == 0 and analysis["lines"] > 50:
            issues.append("No comments found in non-trivial code")
        if analysis["functions"] == 0 and analysis["classes"] == 0:
            issues.append("No functions or classes detected")

        analysis["issues"] = issues
        analysis["score"] = self._calculate_quality_score(analysis)

        return {
            "success": True,
            "analysis": analysis,
            "recommendations": self._get_recommendations(analysis),
        }

    def _calculate_quality_score(self, analysis: Dict) -> float:
        """Calcular score de calidad (0-100)"""
        score = 100.0

        if analysis["lines"] > 0:
            comment_ratio = analysis["comments"] / analysis["lines"]
            if comment_ratio < 0.1:
                score -= 20

        if analysis["lines"] > 300:
            if analysis["functions"] + analysis["classes"] < 5:
                score -= 15

        score -= len(analysis["issues"]) * 10

        return max(0, min(100, score))

    def _get_recommendations(self, analysis: Dict) -> list:
        """Generar recomendaciones"""
        recs = []

        if analysis["score"] < 60:
            recs.append("Consider refactoring to improve code quality")

        if analysis["comments"] / max(analysis["lines"], 1) < 0.1:
            recs.append("Add more comments to explain complex logic")

        if analysis["functions"] > 20:
            recs.append("Consider organizing functions into classes")

        return recs

    def execute_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Ejecutar código de forma segura"""
        if language not in self.supported_languages:
            return {"error": f"Unsupported language: {language}"}

        if not code:
            return {"error": "No code provided"}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=f".{language}", delete=False
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            if language == "python":
                result = subprocess.run(
                    ["python3", temp_file],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
            elif language == "javascript":
                result = subprocess.run(
                    ["node", temp_file],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
            elif language == "bash":
                result = subprocess.run(
                    ["bash", temp_file],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {"error": "Execution timeout (>5s)"}
        except Exception as e:
            return {"error": str(e)}
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def generate_docs(self, code: str) -> Dict[str, Any]:
        """
        Generar documentación automática (MEJORADA)

        Extrae:
        - Funciones con parámetros y docstrings
        - Clases con métodos
        - Imports y dependencias
        - Generación de Markdown
        """
        if not code:
            return {"error": "No code provided"}

        lines = code.split("\n")

        # Estructuras de datos para documentación
        functions = []
        classes = []
        imports = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Detectar imports
            if line.startswith("import ") or line.startswith("from "):
                imports.append(line)

            # Detectar funciones
            elif line.startswith("def "):
                func_info = self._parse_function(lines, i)
                if func_info:
                    functions.append(func_info)

            # Detectar clases
            elif line.startswith("class "):
                class_info = self._parse_class(lines, i)
                if class_info:
                    classes.append(class_info)

            i += 1

        # Generar documentación en formato Markdown
        markdown = self._generate_markdown(functions, classes, imports)

        # Resumen
        summary = {
            "total_functions": len(functions),
            "total_classes": len(classes),
            "total_imports": len(imports),
            "documented_functions": len([f for f in functions if f.get("docstring")]),
            "documented_classes": len([c for c in classes if c.get("docstring")]),
            "coverage": self._calculate_doc_coverage(functions, classes),
        }

        return {
            "success": True,
            "documentation": {
                "functions": functions,
                "classes": classes,
                "imports": imports,
            },
            "summary": summary,
            "markdown": markdown,
        }

    def _parse_function(self, lines: List[str], start_idx: int) -> Dict[str, Any]:
        """Parsear definición de función"""
        line = lines[start_idx].strip()

        # Extraer nombre y parámetros
        match = re.match(r"def\s+(\w+)\s*\((.*?)\)", line)
        if not match:
            return None

        func_name = match.group(1)
        params = match.group(2).strip()

        # Buscar docstring
        docstring = ""
        return_type = None

        if start_idx + 1 < len(lines):
            next_line = lines[start_idx + 1].strip()
            if next_line.startswith('"""') or next_line.startswith("'''"):
                # Extraer docstring multilínea
                quote = next_line[:3]
                docstring = next_line[3:]
                idx = start_idx + 2

                while idx < len(lines) and quote not in lines[idx]:
                    docstring += "\n" + lines[idx].strip()
                    idx += 1

                if idx < len(lines):
                    docstring += "\n" + lines[idx].strip().replace(quote, "")

                docstring = docstring.strip()

        # Detectar tipo de retorno
        if "->" in line:
            return_type = line.split("->")[-1].split(":")[0].strip()

        return {
            "name": func_name,
            "params": params,
            "docstring": docstring,
            "return_type": return_type,
            "line": start_idx + 1,
        }

    def _parse_class(self, lines: List[str], start_idx: int) -> Dict[str, Any]:
        """Parsear definición de clase"""
        line = lines[start_idx].strip()

        # Extraer nombre de clase
        match = re.match(r"class\s+(\w+)", line)
        if not match:
            return None

        class_name = match.group(1)

        # Buscar docstring de clase
        docstring = ""
        if start_idx + 1 < len(lines):
            next_line = lines[start_idx + 1].strip()
            if next_line.startswith('"""') or next_line.startswith("'''"):
                quote = next_line[:3]
                docstring = next_line[3:]
                idx = start_idx + 2

                while idx < len(lines) and quote not in lines[idx]:
                    docstring += "\n" + lines[idx].strip()
                    idx += 1

                if idx < len(lines):
                    docstring += "\n" + lines[idx].strip().replace(quote, "")

                docstring = docstring.strip()

        # Buscar métodos de la clase
        methods = []
        indent_level = len(lines[start_idx]) - len(lines[start_idx].lstrip())

        for i in range(start_idx + 1, len(lines)):
            current_indent = len(lines[i]) - len(lines[i].lstrip())

            # Si volvemos al nivel de indentación original, terminamos
            if lines[i].strip() and current_indent <= indent_level:
                break

            # Detectar métodos
            if lines[i].strip().startswith("def "):
                method_info = self._parse_function(lines, i)
                if method_info:
                    methods.append(method_info)

        return {
            "name": class_name,
            "docstring": docstring,
            "methods": methods,
            "line": start_idx + 1,
        }

    def _generate_markdown(self, functions: List, classes: List, imports: List) -> str:
        """Generar documentación en formato Markdown"""
        md = ["# Code Documentation\n"]

        # Imports
        if imports:
            md.append("## Dependencies\n")
            for imp in imports:
                md.append(f"- `{imp}`")
            md.append("")

        # Clases
        if classes:
            md.append("## Classes\n")
            for cls in classes:
                md.append(f"### {cls['name']}\n")
                if cls.get("docstring"):
                    md.append(f"{cls['docstring']}\n")

                if cls.get("methods"):
                    md.append("**Methods:**\n")
                    for method in cls["methods"]:
                        params = f"({method['params']})" if method["params"] else "()"
                        md.append(f"- `{method['name']}{params}`")
                        if method.get("docstring"):
                            md.append(f"  - {method['docstring'][:100]}")
                md.append("")

        # Funciones
        if functions:
            md.append("## Functions\n")
            for func in functions:
                params = f"({func['params']})" if func["params"] else "()"
                return_info = (
                    f" -> {func['return_type']}" if func.get("return_type") else ""
                )

                md.append(f"### {func['name']}{params}{return_info}\n")
                if func.get("docstring"):
                    md.append(f"{func['docstring']}\n")
                md.append("")

        return "\n".join(md)

    def _calculate_doc_coverage(self, functions: List, classes: List) -> float:
        """Calcular cobertura de documentación"""
        total_items = len(functions) + len(classes)
        if total_items == 0:
            return 100.0

        documented = sum(1 for f in functions if f.get("docstring"))
        documented += sum(1 for c in classes if c.get("docstring"))

        return round((documented / total_items) * 100, 1)

    def get_capabilities(self) -> Dict[str, Any]:
        """Retornar capacidades del plugin"""
        return {
            "name": self.name,
            "version": self.version,
            "actions": ["analyze", "execute", "document"],
            "supported_languages": self.supported_languages,
            "features": [
                "Code quality analysis",
                "Safe code execution",
                "Automatic documentation generation",
                "Markdown export",
                "Docstring extraction",
                "Class and method parsing",
            ],
        }
