"""
Code Explainer Module
Explains complex code in natural language
"""

import re
from typing import Dict, List, Any

class CodeExplainer:
    def __init__(self):
        self.patterns = {
            'list_comprehension': r'\[.+\s+for\s+.+\s+in\s+.+\]',
            'lambda': r'lambda\s+\w+:',
            'decorator': r'@\w+',
            'generator': r'yield\s+',
            'context_manager': r'with\s+.+\s+as\s+',
        }
    
    def explain_code(self, code: str) -> Dict[str, Any]:
        """Generate explanation for code snippet"""
        explanation = {
            "summary": self._generate_summary(code),
            "features": self._identify_features(code),
            "complexity": self._estimate_complexity(code),
            "suggestions": []
        }
        return explanation
    
    def _generate_summary(self, code: str) -> str:
        """Generate high-level summary"""
        lines = code.strip().split('\n')
        if 'def ' in code:
            return "Function definition with implementation"
        elif 'class ' in code:
            return "Class definition"
        else:
            return f"Code snippet with {len(lines)} lines"
    
    def _identify_features(self, code: str) -> List[str]:
        """Identify Python features used"""
        features = []
        for feature, pattern in self.patterns.items():
            if re.search(pattern, code):
                features.append(feature)
        return features
    
    def _estimate_complexity(self, code: str) -> str:
        """Estimate complexity level"""
        lines = len(code.split('\n'))
        if lines < 10:
            return "simple"
        elif lines < 30:
            return "moderate"
        else:
            return "complex"
