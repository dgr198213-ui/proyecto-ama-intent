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
    SECURITY = "security"
    PERFORMANCE = "performance"
    LOGIC = "logic"
    STYLE = "style"
    RESOURCE_LEAK = "resource_leak"
    EXCEPTION = "exception"


@dataclass
class BugPattern:
    """Patrón de bug a inyectar"""
    type: BugType
    original_code: str
    buggy_code: str
    description: str
    severity: str


@dataclass
class CodeTrajectory:
    """Trayectoria completa de corrección de código"""
    original_code: str
    buggy_code: str
    bug_type: BugType
    corrections: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class BugInjector:
    """Inyecta bugs sintéticos en código Python"""
    
    def __init__(self):
        self.patterns = self._load_bug_patterns()
    
    def _load_bug_patterns(self) -> Dict[BugType, List[callable]]:
        return {
            BugType.SECURITY: [self._inject_eval_bug, self._inject_sql_injection],
            BugType.PERFORMANCE: [self._inject_nested_loops],
            BugType.LOGIC: [self._inject_off_by_one],
            BugType.RESOURCE_LEAK: [self._inject_file_leak]
        }
    
    def inject_bug(self, code: str, bug_type: Optional[BugType] = None) -> BugPattern:
        if bug_type is None:
            bug_type = random.choice(list(self.patterns.keys()))
        
        injectors = self.patterns.get(bug_type, [])
        if not injectors:
            return BugPattern(bug_type, code, code, "No injector", "low")
        
        injector = random.choice(injectors)
        return injector(code)
    
    def _inject_eval_bug(self, code: str) -> BugPattern:
        buggy = code + "\n\ndef unsafe_execute(user_input):\n    return eval(user_input)  # BUG: eval() inseguro\n"
        return BugPattern(BugType.SECURITY, code, buggy, "Uso de eval() con input no sanitizado", "critical")

    def _inject_sql_injection(self, code: str) -> BugPattern:
        buggy = code + "\n\ndef get_user(db, name):\n    return db.execute(f'SELECT * FROM users WHERE name=\"{name}\"')  # BUG: SQL Injection\n"
        return BugPattern(BugType.SECURITY, code, buggy, "Concatenación de strings en query SQL", "critical")

    def _inject_nested_loops(self, code: str) -> BugPattern:
        buggy = code + "\n\ndef has_duplicates(items):\n    for i in range(len(items)):\n        for j in range(len(items)):\n            if i != j and items[i] == items[j]: return True\n    return False\n"
        return BugPattern(BugType.PERFORMANCE, code, buggy, "Bucle anidado O(n^2) innecesario", "medium")

    def _inject_off_by_one(self, code: str) -> BugPattern:
        buggy = code + "\n\ndef get_first_n(items, n):\n    return items[:n+1]  # BUG: Off-by-one\n"
        return BugPattern(BugType.LOGIC, code, buggy, "Error de índice off-by-one en slicing", "high")

    def _inject_file_leak(self, code: str) -> BugPattern:
        buggy = code + "\n\ndef read_data(path):\n    f = open(path, 'r')\n    return f.read()  # BUG: File leak\n"
        return BugPattern(BugType.RESOURCE_LEAK, code, buggy, "Archivo abierto sin cerrar", "medium")


class CodeVerifier:
    """Verifica correcciones de código"""
    
    def verify_code(self, code: str) -> Dict[str, Any]:
        try:
            ast.parse(code)
            return {"passed": True, "reward": 1.0, "errors": []}
        except SyntaxError as e:
            return {"passed": False, "reward": 0.0, "errors": [str(e)]}


class AgenticDataSynthesizer:
    """Sintetizador de datos agénticos"""
    
    def __init__(self, llm_hub):
        self.llm = llm_hub
        self.bug_injector = BugInjector()
        self.verifier = CodeVerifier()
    
    async def generate_trajectories(self, num_trajectories: int = 10) -> List[CodeTrajectory]:
        trajectories = []
        base_code = "def process(x):\n    return x * 2"
        
        for _ in range(num_trajectories):
            bug_pattern = self.bug_injector.inject_bug(base_code)
            # Simulación de correcciones
            corrections = [{"code": base_code, "reward": 1.0}]
            
            trajectories.append(CodeTrajectory(
                original_code=base_code,
                buggy_code=bug_pattern.buggy_code,
                bug_type=bug_pattern.type,
                corrections=corrections,
                metadata={"description": bug_pattern.description}
            ))
        return trajectories

    def convert_to_preference_pairs(self, trajectories: List[CodeTrajectory]) -> List[Dict[str, Any]]:
        pairs = []
        for traj in trajectories:
            pairs.append({
                "prompt": f"Corrige el siguiente código: {traj.buggy_code}",
                "chosen": traj.original_code,
                "rejected": traj.buggy_code
            })
        return pairs
