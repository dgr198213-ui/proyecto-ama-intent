"""
Agentic Data Synthesizer - Inspirado en Kimi K2
Genera trayectorias sintéticas para entrenar Reward Models
RLVR: Reinforcement Learning with Verifiable Rewards
"""

import asyncio
import random
import ast
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json


class BugType(Enum):
    """Tipos de bugs sintéticos a inyectar"""
    SECURITY = "security"  # eval(), exec(), sql injection
    PERFORMANCE = "performance"  # O(n²) innecesario, loops ineficientes
    LOGIC = "logic"  # Condiciones incorrectas, off-by-one
    STYLE = "style"  # PEP8 violations
    RESOURCE_LEAK = "resource_leak"  # Files no cerrados, memory leaks
    EXCEPTION = "exception"  # Try/except faltante


@dataclass
class BugPattern:
    """Patrón de bug a inyectar"""
    type: BugType
    original_code: str
    buggy_code: str
    description: str
    severity: str  # "critical", "high", "medium", "low"


@dataclass
class CodeTrajectory:
    """Trayectoria completa de corrección de código"""
    original_code: str
    buggy_code: str
    bug_type: BugType
    corrections: List[Dict[str, Any]]  # Lista de intentos de corrección
    metadata: Dict[str, Any]


class BugInjector:
    """
    Inyecta bugs sintéticos en código Python
    """
    
    def __init__(self):
        self.patterns = self._load_bug_patterns()
    
    def _load_bug_patterns(self) -> Dict[BugType, List[callable]]:
        """Carga patrones de bugs"""
        return {
            BugType.SECURITY: [
                self._inject_eval_bug,
                self._inject_sql_injection,
                self._inject_command_injection
            ],
            BugType.PERFORMANCE: [
                self._inject_nested_loops,
                self._inject_repeated_computation
            ],
            BugType.LOGIC: [
                self._inject_off_by_one,
                self._inject_wrong_condition
            ],
            BugType.RESOURCE_LEAK: [
                self._inject_file_leak,
                self._inject_unclosed_connection
            ]
        }
    
    def inject_bug(self, code: str, bug_type: Optional[BugType] = None) -> BugPattern:
        """
        Inyecta bug en el código
        
        Args:
            code: Código original limpio
            bug_type: Tipo específico o None para aleatorio
            
        Returns:
            BugPattern con original y versión bugueada
        """
        if bug_type is None:
            bug_type = random.choice(list(BugType))
        
        # Seleccionar injector aleatorio del tipo
        injectors = self.patterns.get(bug_type, [])
        if not injectors:
            return BugPattern(
                type=bug_type,
                original_code=code,
                buggy_code=code,
                description="No injector disponible",
                severity="low"
            )
        
        injector = random.choice(injectors)
        return injector(code)
    
    # Inyectores específicos de bugs
    
    def _inject_eval_bug(self, code: str) -> BugPattern:
        """Inyecta uso inseguro de eval()"""
        # Buscar función que procese strings
        tree = ast.parse(code)
        
        # Encontrar una función
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Insertar eval malicioso
                buggy = code.replace(
                    f"def {node.name}",
                    f"def {node.name}_buggy"
                )
                buggy += f"\n\n# BUG: eval() inseguro\nresult = eval(user_input)\n"
                
                return BugPattern(
                    type=BugType.SECURITY,
                    original_code=code,
                    buggy_code=buggy,
                    description="eval() permite inyección de código arbitrario",
                    severity="critical"
                )
        
        return self._generic_bug_pattern(code, BugType.SECURITY)
    
    def _inject_sql_injection(self, code: str) -> BugPattern:
        """Inyecta vulnerabilidad SQL injection"""
        buggy = code + '''

# BUG: SQL Injection vulnerable
def query_user(username):
    query = f"SELECT * FROM users WHERE name = '{username}'"
    # Vulnerable a: username = "' OR '1'='1"
    return execute_query(query)
'''
        
        return BugPattern(
            type=BugType.SECURITY,
            original_code=code,
            buggy_code=buggy,
            description="Concatenación directa de strings en SQL permite injection",
            severity="critical"
        )
    
    def _inject_command_injection(self, code: str) -> BugPattern:
        """Inyecta command injection"""
        buggy = code + '''

# BUG: Command Injection
import os
def process_file(filename):
    # Vulnerable a: filename = "file.txt; rm -rf /"
    os.system(f"cat {filename}")
'''
        
        return BugPattern(
            type=BugType.SECURITY,
            original_code=code,
            buggy_code=buggy,
            description="os.system con input no sanitizado",
            severity="critical"
        )
    
    def _inject_nested_loops(self, code: str) -> BugPattern:
        """Inyecta loops anidados innecesarios"""
        buggy = code + '''

# BUG: O(n²) innecesario
def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(len(items)):
            if i != j and items[i] == items[j]:
                duplicates.append(items[i])
    return duplicates

# MEJOR: usar set O(n)
def find_duplicates_fixed(items):
    seen = set()
    duplicates = set()
    for item in items:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return list(duplicates)
'''
        
        return BugPattern(
            type=BugType.PERFORMANCE,
            original_code=code,
            buggy_code=buggy,
            description="Complejidad O(n²) cuando O(n) es posible",
            severity="medium"
        )
    
    def _inject_repeated_computation(self, code: str) -> BugPattern:
        """Inyecta computaciones repetidas"""
        buggy = code + '''

# BUG: Computación repetida en loop
def calculate_totals(data):
    results = []
    for item in data:
        # len() se calcula en cada iteración innecesariamente
        average = sum(data) / len(data)
        results.append(item * average)
    return results
'''
        
        return BugPattern(
            type=BugType.PERFORMANCE,
            original_code=code,
            buggy_code=buggy,
            description="Cálculos constantes dentro de loops",
            severity="medium"
        )
    
    def _inject_off_by_one(self, code: str) -> BugPattern:
        """Inyecta error off-by-one"""
        buggy = code + '''

# BUG: Off-by-one error
def get_last_n_items(items, n):
    # Error: debería ser [-n:] no [:-n]
    return items[:-n]  # Retorna todo EXCEPTO los últimos n
'''
        
        return BugPattern(
            type=BugType.LOGIC,
            original_code=code,
            buggy_code=buggy,
            description="Error de índice en slicing",
            severity="high"
        )
    
    def _inject_wrong_condition(self, code: str) -> BugPattern:
        """Inyecta condición lógica incorrecta"""
        buggy = code + '''

# BUG: Condición invertida
def is_valid_age(age):
    # Error: debería ser >= 18, no < 18
    return age < 18  # Retorna True para menores!
'''
        
        return BugPattern(
            type=BugType.LOGIC,
            original_code=code,
            buggy_code=buggy,
            description="Condición booleana invertida",
            severity="high"
        )
    
    def _inject_file_leak(self, code: str) -> BugPattern:
        """Inyecta resource leak"""
        buggy = code + '''

# BUG: File handle no cerrado
def read_config(filename):
    f = open(filename, 'r')
    data = f.read()
    # FALTA: f.close()
    return data

# CORRECTO: usar context manager
def read_config_fixed(filename):
    with open(filename, 'r') as f:
        return f.read()
'''
        
        return BugPattern(
            type=BugType.RESOURCE_LEAK,
            original_code=code,
            buggy_code=buggy,
            description="File handle no cerrado explícitamente",
            severity="medium"
        )
    
    def _inject_unclosed_connection(self, code: str) -> BugPattern:
        """Inyecta connection leak"""
        buggy = code + '''

# BUG: DB connection no cerrada
import sqlite3
def query_database(query):
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    result = cursor.execute(query).fetchall()
    # FALTA: conn.close()
    return result
'''
        
        return BugPattern(
            type=BugType.RESOURCE_LEAK,
            original_code=code,
            buggy_code=buggy,
            description="Conexión de base de datos no cerrada",
            severity="medium"
        )
    
    def _generic_bug_pattern(self, code: str, bug_type: BugType) -> BugPattern:
        """Patrón genérico cuando no hay injector específico"""
        return BugPattern(
            type=bug_type,
            original_code=code,
            buggy_code=code + "\n# Generic bug injected\n",
            description="Bug genérico",
            severity="low"
        )


class CodeVerifier:
    """
    Verifica correcciones de código ejecutando tests
    RLVR: Solo da reward si el código REALMENTE funciona
    """
    
    def __init__(self):
        self.sandbox_enabled = True
    
    def verify_code(self, code: str, test_cases: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Verifica código ejecutándolo
        
        Returns:
            {
                "passed": bool,
                "tests_passed": int,
                "tests_failed": int,
                "errors": List[str],
                "reward": float
            }
        """
        results = {
            "passed": False,
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": [],
            "reward": 0.0
        }
        
        try:
            # 1. Verificar sintaxis
            ast.parse(code)
            results["tests_passed"] += 1
        except SyntaxError as e:
            results["errors"].append(f"Syntax Error: {e}")
            results["tests_failed"] += 1
            return results
        
        # 2. Análisis estático de seguridad
        security_score = self._check_security(code)
        if security_score < 0.5:
            results["errors"].append("Vulnerabilidades de seguridad detectadas")
            results["tests_failed"] += 1
        else:
            results["tests_passed"] += 1
        
        # 3. Ejecutar en sandbox (si está habilitado)
        if self.sandbox_enabled and test_cases:
            exec_results = self._execute_in_sandbox(code, test_cases)
            results["tests_passed"] += exec_results["passed"]
            results["tests_failed"] += exec_results["failed"]
            results["errors"].extend(exec_results["errors"])
        
        # 4. Calcular reward
        total_tests = results["tests_passed"] + results["tests_failed"]
        if total_tests > 0:
            results["passed"] = results["tests_failed"] == 0
            results["reward"] = results["tests_passed"] / total_tests
        
        return results
    
    def _check_security(self, code: str) -> float:
        """
        Análisis estático de seguridad (0-1)
        1.0 = muy seguro, 0.0 = muy inseguro
        """
        security_issues = []
        
        # Patrones inseguros
        unsafe_patterns = [
            ("eval(", "Uso de eval()"),
            ("exec(", "Uso de exec()"),
            ("os.system(", "Uso de os.system()"),
            ("subprocess.call(", "Uso directo de subprocess sin validación"),
            ("__import__", "Import dinámico"),
            ("compile(", "Compilación dinámica")
        ]
        
        for pattern, description in unsafe_patterns:
            if pattern in code:
                security_issues.append(description)
        
        # Score basado en issues encontrados
        if not security_issues:
            return 1.0
        
        return max(0.0, 1.0 - (len(security_issues) * 0.3))
    
    def _execute_in_sandbox(self, code: str, test_cases: List[Dict]) -> Dict[str, Any]:
        """
        Ejecuta código en sandbox aislado
        """
        results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Ejecutar Python en subprocess (sandbox simple)
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=5  # Timeout de 5 segundos
            )
            
            if result.returncode == 0:
                results["passed"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(result.stderr)
                
        except subprocess.TimeoutExpired:
            results["failed"] += 1
            results["errors"].append("Timeout: código tardó más de 5 segundos")
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(str(e))
        finally:
            # Limpiar archivo temporal
            Path(temp_file).unlink(missing_ok=True)
        
        return results


class AgenticDataSynthesizer:
    """
    Sintetizador de datos agénticos para entrenar Reward Models
    Genera trayectorias de corrección de código
    """
    
    def __init__(self, llm_hub, kg=None):
        self.llm = llm_hub
        self.kg = kg
        self.bug_injector = BugInjector()
        self.verifier = CodeVerifier()
    
    async def generate_trajectories(self, 
                                   num_trajectories: int = 1000,
                                   variants_per_bug: int = 5) -> List[CodeTrajectory]:
        """
        Genera trayectorias sintéticas
        
        Args:
            num_trajectories: Número de trayectorias a generar
            variants_per_bug: Variantes de corrección por bug
            
        Returns:
            Lista de trayectorias completas
        """
        print(f"🔬 Generando {num_trajectories} trayectorias sintéticas...")
        
        trajectories = []
        
        for i in range(num_trajectories):
            # 1. Obtener código base (del KG si está disponible)
            base_code = await self._get_base_code()
            
            # 2. Inyectar bug
            bug_pattern = self.bug_injector.inject_bug(base_code)
            
            # 3. Generar múltiples correcciones
            corrections = await self._generate_corrections(
                bug_pattern,
                num_variants=variants_per_bug
            )
            
            # 4. Verificar cada corrección
            verified_corrections = []
            for correction in corrections:
                verification = self.verifier.verify_code(correction["code"])
                correction["verification"] = verification
                correction["reward"] = verification["reward"]
                verified_corrections.append(correction)
            
            # 5. Crear trayectoria
            trajectory = CodeTrajectory(
                original_code=bug_pattern.original_code,
                buggy_code=bug_pattern.buggy_code,
                bug_type=bug_pattern.type,
                corrections=verified_corrections,
                metadata={
                    "bug_description": bug_pattern.description,
                    "severity": bug_pattern.severity
                }
            )
            
            trajectories.append(trajectory)
            
            if (i + 1) % 100 == 0:
                print(f"  Progreso: {i+1}/{num_trajectories} trayectorias")
        
        print(f"✅ {len(trajectories)} trayectorias generadas")
        
        return trajectories
    
    async def _get_base_code(self) -> str:
        """Obtiene código base del KG o genera uno simple"""
        if self.kg and self.kg.entities:
            # Seleccionar función aleatoria del KG
            functions = [e for e in self.kg.entities if e.type.value == "function"]
            if functions:
                func = random.choice(functions)
                # En producción: leer código real del archivo
                return f"def {func.name}():\n    pass\n"
        
        # Código base simple por defecto
        return '''
def process_data(items):
    """Procesa una lista de items"""
    result = []
    for item in items:
        if item > 0:
            result.append(item * 2)
    return result
'''
    
    async def _generate_corrections(self, 
                                   bug_pattern: BugPattern,
                                   num_variants: int = 5) -> List[Dict[str, Any]]:
        """
        Genera múltiples variantes de corrección usando LLM
        """
        corrections = []
        
        for variant_id in range(num_variants):
            # Prompt para el LLM
            prompt = f"""Eres un experto en seguridad y calidad de código.

BUG DETECTADO:
Tipo: {bug_pattern.type.value}
Severidad: {bug_pattern.severity}
Descripción: {bug_pattern.description}

CÓDIGO BUGUEADO:
```python
{bug_pattern.buggy_code}
```

Genera una corrección (variante #{variant_id+1}). 
Considera diferentes enfoques:
- Variante 1: Solución simple y directa
- Variante 2: Solución con validación adicional
- Variante 3: Solución con manejo robusto de errores
- Variante 4: Solución optimizada para rendimiento
- Variante 5: Solución con logging y monitoreo

Responde SOLO con el código corregido, sin explicaciones.
"""
            
            from llm_connector import AnalysisRequest
            
            request = AnalysisRequest(
                code=bug_pattern.buggy_code,
                file_path="synthetic_correction",
                task="refactor",
                context=prompt,
                max_tokens=1000,
                temperature=0.7 + (variant_id * 0.1)  # Más variedad con temperatura
            )
            
            response = await self.llm.analyze(request)
            
            if response.success:
                # Limpiar código (quitar markdown)
                code = self._extract_code(response.content)
                
                corrections.append({
                    "variant_id": variant_id,
                    "code": code,
                    "approach": f"Variante {variant_id+1}"
                })
        
        return corrections
    
    def _extract_code(self, llm_response: str) -> str:
        """Extrae código de la respuesta del LLM"""
        # Quitar bloques de markdown
        if "```python" in llm_response:
            code = llm_response.split("```python")[1].split("```")[0]
        elif "```" in llm_response:
            code = llm_response.split("```")[1].split("```")[0]
        else:
            code = llm_response
        
        return code.strip()
    
    def convert_to_preference_pairs(self, 
                                   trajectories: List[CodeTrajectory]) -> List[Dict[str, Any]]:
        """
        Convierte trayectorias a pares de preferencias (Bradley-Terry)
        
        Returns:
            Lista de pares {prompt, chosen, rejected}
        """
        pairs = []
        
        for traj in trajectories:
            # Separar correcciones buenas y malas
            good_corrections = [c for c in traj.corrections if c["reward"] >= 0.8]
            bad_corrections = [c for c in traj.corrections if c["reward"] < 0.5]
            
            # Crear pares
            prompt = f"Corrige