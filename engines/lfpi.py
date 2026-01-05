from utils.utils import clamp

class LFPI:
    def __init__(self):
        pass

    def calculate(self, gain, loss, feedback, amplitude):
        # Fórmula: LFPI = clamp(100 * (gain - loss + amplitude * feedback), 0, 100)
        value = 100 * (gain - loss + amplitude * feedback)
        return clamp(value, 0, 100)

    def classify(self, score):
        if score >= 80: return "excellent"
        if score >= 60: return "good"
        if score >= 40: return "fair"
        return "poor"

    def run(self, payload):
        gain = payload.get("gain", 0.0)
        loss = payload.get("loss", 0.0)
        feedback = payload.get("feedback", 0.0)
        amplitude = payload.get("amplitude", 1.0)
        
        score = self.calculate(gain, loss, feedback, amplitude)
        level = self.classify(score)
        
        return {
            "value": score,
            "level": level,
            "components": {
                "gain": gain,
                "loss": loss,
                "feedback": feedback,
                "amplitude": amplitude
            }
        }
