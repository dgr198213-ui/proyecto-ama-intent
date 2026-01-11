import json
import time


class EngineBus:
    def __init__(self):
        self.engines = {}
        self.metrics = {"calls": 0, "errors": 0, "total_time": 0.0}
        self.logs = []

    def register(self, name, engine_instance):
        self.engines[name] = engine_instance

    def has(self, name):
        return name in self.engines

    def list_engines(self):
        return list(self.engines.keys())

    def call(self, name, payload):
        if name not in self.engines:
            raise ValueError(f"Engine '{name}' not registered.")

        start_time = time.time()
        self.metrics["calls"] += 1

        try:
            result = self.engines[name].run(payload)
            duration = time.time() - start_time
            self.metrics["total_time"] += duration

            log_entry = {
                "timestamp": time.time(),
                "engine": name,
                "payload": payload,
                "result": result,
                "duration": duration,
                "status": "success",
            }
            self.logs.append(log_entry)
            return result
        except Exception as e:
            self.metrics["errors"] += 1
            duration = time.time() - start_time
            log_entry = {
                "timestamp": time.time(),
                "engine": name,
                "payload": payload,
                "error": str(e),
                "duration": duration,
                "status": "error",
            }
            self.logs.append(log_entry)
            raise e

    def pipeline(self, names, initial_payload):
        current_payload = initial_payload
        for name in names:
            current_payload = self.call(name, current_payload)
        return current_payload

    def get_metrics(self):
        avg_time = (
            self.metrics["total_time"] / self.metrics["calls"]
            if self.metrics["calls"] > 0
            else 0
        )
        return {
            "calls": self.metrics["calls"],
            "errors": self.metrics["errors"],
            "avg_time": avg_time,
        }

    def export_log(self, path):
        with open(path, "w") as f:
            json.dump(self.logs, f, indent=2)
