"""
Debug Assistant for Personal Projects
Analyzes errors and suggests solutions
"""

import traceback
import re
from typing import Dict, List, Any
import subprocess
import sys

class DebugAssistant:
    def __init__(self):
        self.common_solutions = {
            "ModuleNotFoundError": {
                "patterns": ["No module named", "ModuleNotFoundError"],
                "solutions": [
                    "pip install <module_name>",
                    "Check if module is in requirements.txt",
                    "Verify Python path and virtual environment"
                ]
            },
            "ImportError": {
                "patterns": ["ImportError", "cannot import name"],
                "solutions": [
                    "Check circular imports",
                    "Verify __init__.py files",
                    "Ensure module is in PYTHONPATH"
                ]
            },
            "SyntaxError": {
                "patterns": ["SyntaxError", "invalid syntax"],
                "solutions": [
                    "Check for missing parentheses, brackets, or quotes",
                    "Verify indentation (especially mixing tabs and spaces)",
                    "Look for incomplete statements"
                ]
            },
            "TypeError": {
                "patterns": ["TypeError", "unsupported operand"],
                "solutions": [
                    "Check variable types before operations",
                    "Ensure function arguments match expected types",
                    "Convert types explicitly if needed"
                ]
            },
            "KeyError": {
                "patterns": ["KeyError"],
                "solutions": [
                    "Check if key exists in dictionary before accessing",
                    "Use dict.get() with default value",
                    "Verify dictionary initialization"
                ]
            },
            "AttributeError": {
                "patterns": ["AttributeError", "has no attribute"],
                "solutions": [
                    "Check object type and available attributes",
                    "Verify method/attribute names for typos",
                    "Ensure object is properly initialized"
                ]
            }
        }
    
    def analyze_error(self, error_traceback: str) -> Dict[str, Any]:
        """Analyze error traceback and provide solutions"""
        error_info = {
            "error_type": "Unknown",
            "error_message": "",
            "file": "",
            "line": 0,
            "solutions": [],
            "quick_fix": "",
            "confidence": 0.0
        }
        
        # Parse traceback
        lines = error_traceback.strip().split('\n')
        
        # Find error type and message
        for line in reversed(lines):
            if any(err in line for err in ["Error:", "Exception:"]):
                error_parts = line.split(":", 1)
                if len(error_parts) > 1:
                    error_info["error_type"] = error_parts[0].strip()
                    error_info["error_message"] = error_parts[1].strip()
                break
        
        # Find file and line number
        for line in lines:
            if "File \"" in line and ", line" in line:
                match = re.search(r'File \"(.+?)\", line (\d+)', line)
                if match:
                    error_info["file"] = match.group(1)
                    error_info["line"] = int(match.group(2))
                break
        
        # Match error with known solutions
        for error_name, error_data in self.common_solutions.items():
            for pattern in error_data["patterns"]:
                if pattern in error_info["error_type"] or pattern in error_info["error_message"]:
                    error_info["solutions"] = error_data["solutions"]
                    error_info["quick_fix"] = error_data["solutions"][0] if error_data["solutions"] else ""
                    error_info["confidence"] = 0.8
                    break
        
        # Special handling for common patterns
        if "No module named" in error_info["error_message"]:
            module_match = re.search(r"No module named '(.+?)'", error_info["error_message"])
            if module_match:
                module_name = module_match.group(1)
                error_info["solutions"] = [
                    f"pip install {module_name}",
                    f"Add '{module_name}' to requirements.txt",
                    f"Check if you need to activate virtual environment"
                ]
                error_info["quick_fix"] = f"pip install {module_name}"
                error_info["confidence"] = 0.9
        
        # If no specific solution found, provide general debugging steps
        if not error_info["solutions"]:
            error_info["solutions"] = [
                "Read the error message carefully",
                "Check line number mentioned in traceback",
                "Add print() statements to debug variable values",
                "Use try-except blocks to catch and inspect errors",
                "Search online for the exact error message"
            ]
            error_info["quick_fix"] = "Review the code at the mentioned line number"
            error_info["confidence"] = 0.5
        
        return error_info
    
    def analyze_code_snippet(self, code: str) -> Dict[str, Any]:
        """Analyze code snippet for potential issues"""
        issues = []
        suggestions = []
        
        # Check for common issues
        if "import *" in code:
            issues.append({
                "type": "wildcard_import",
                "message": "Wildcard imports can cause namespace pollution",
                "severity": "medium",
                "line": code.count('\n', 0, code.find("import *")) + 1
            })
            suggestions.append("Import specific functions/classes instead of using '*'")
        
        if "eval(" in code:
            issues.append({
                "type": "eval_usage",
                "message": "eval() can be a security risk",
                "severity": "high",
                "line": code.count('\n', 0, code.find("eval(")) + 1
            })
            suggestions.append("Consider using ast.literal_eval() or safer alternatives")
        
        if "password" in code.lower() or "secret" in code.lower():
            if any(word in code.lower() for word in ["hardcoded", "= \"", "= '"]):
                issues.append({
                    "type": "hardcoded_secret",
                    "message": "Secrets should not be hardcoded",
                    "severity": "high",
                    "line": 1  # General issue
                })
                suggestions.append("Use environment variables or secure config files for secrets")
        
        # Check for long functions
        lines = code.split('\n')
        function_start = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("def "):
                if function_start != -1:
                    function_length = i - function_start
                    if function_length > 30:
                        issues.append({
                            "type": "long_function",
                            "message": f"Function at line {function_start + 1} is {function_length} lines long",
                            "severity": "low",
                            "line": function_start + 1
                        })
                        suggestions.append(f"Consider breaking the function into smaller functions")
                function_start = i
        
        return {
            "issues_found": len(issues),
            "issues": issues,
            "suggestions": suggestions,
            "complexity": self._estimate_complexity(code)
        }
    
    def _estimate_complexity(self, code: str) -> str:
        """Estimate code complexity"""
        lines = len(code.split('\n'))
        
        if lines < 20:
            return "simple"
        elif lines < 50:
            return "moderate"
        elif lines < 100:
            return "complex"
        else:
            return "very complex"
    
    def generate_test_stub(self, function_code: str) -> str:
        """Generate a test stub for a function"""
        # Extract function name
        match = re.search(r"def (\w+)\(", function_code)
        if not match:
            return "# Could not parse function definition"
        
        func_name = match.group(1)
        
        test_code = f'''import pytest

def test_{func_name}():
    """
    Test for {func_name} function
    TODO: Add specific test cases
    """
    # Example test cases
    
    # Test normal case
    # result = {func_name}(...)
    # assert result == expected_value
    
    # Test edge cases
    # result = {func_name}(...)
    # assert result == expected_value
    
    # Test error cases
    # with pytest.raises(ExpectedError):
    #     {func_name}(...)
    
    pass  # Remove this when adding actual tests

# Additional tests can be added here
'''
        return test_code
    
    def get_debug_report(self, error_info: Dict, code_analysis: Dict) -> str:
        """Generate comprehensive debug report"""
        report = "# 🐛 Debug Report\n\n"
        
        report += "## Error Analysis\n\n"
        report += f"**Error Type:** {error_info.get('error_type', 'Unknown')}\n"
        report += f"**Message:** {error_info.get('error_message', '')}\n"
        report += f"**File:** {error_info.get('file', 'Unknown')}\n"
        report += f"**Line:** {error_info.get('line', 0)}\n"
        report += f"**Confidence:** {error_info.get('confidence', 0) * 100:.1f}%\n\n"
        
        report += "## 🔧 Suggested Solutions\n\n"
        for i, solution in enumerate(error_info.get('solutions', []), 1):
            report += f"{i}. {solution}\n"
        
        report += f"\n**Quick Fix:** {error_info.get('quick_fix', '')}\n\n"
        
        if code_analysis.get('issues_found', 0) > 0:
            report += "## ⚠️ Code Quality Issues\n\n"
            for issue in code_analysis.get('issues', []):
                emoji = "🔴" if issue['severity'] == 'high' else "🟡" if issue['severity'] == 'medium' else "🔵"
                report += f"{emoji} **{issue['type']}** (line {issue.get('line', '?')}): {issue['message']}\n"
        
        report += "\n## 💡 Additional Suggestions\n\n"
        for suggestion in code_analysis.get('suggestions', []):
            report += f"- {suggestion}\n"
        
        report += f"\n## 📊 Code Complexity: {code_analysis.get('complexity', 'unknown').title()}\n"
        
        return report