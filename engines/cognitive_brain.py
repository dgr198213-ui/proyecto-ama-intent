import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.utils import tokenize

class CognitiveBrain:
    def __init__(self):
        self.working_memory = []
        self.wm_limit = 20

    def _push_wm(self, item):
        self.working_memory.append(item)
        if len(self.working_memory) > self.wm_limit:
            self.working_memory.pop(0)

    def get_context(self, n):
        return self.working_memory[-n:] if self.working_memory else []

    def _decide(self, tokens, payload):
        # Lógica de decisión basada en tokens y contexto
        intent = payload.get("intent", "general")
        confidence = 0.5
        
        if intent == "search":
            confidence = 0.85
        elif intent == "analyze":
            confidence = 0.80
        
        return intent, confidence

    def run(self, payload):
        text = payload.get("text", "")
        tokens = tokenize(text)
        
        action, confidence = self._decide(tokens, payload)
        
        result = {
            "action": action,
            "confidence": confidence,
            "tokens_count": len(tokens)
        }
        
        self._push_wm({"input": text, "output": result})
        
        return result
