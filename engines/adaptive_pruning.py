class AdaptivePruning:
    def __init__(self):
        pass

    def run(self, payload):
        items = payload.get("items", [])
        alpha = payload.get("alpha", 0.5)
        beta = payload.get("beta", 0.5)
        threshold = payload.get("threshold", 0.4)
        
        kept = []
        removed = []
        
        for item in items:
            importance = item.get("importance", 0.0)
            usage = item.get("usage", 0.0)
            
            score = alpha * importance + beta * usage
            
            if score >= threshold:
                kept.append(item)
            else:
                removed.append(item)
        
        efficiency = len(removed) / len(items) if items else 0.0
        
        return {
            "kept": kept,
            "removed": removed,
            "efficiency": efficiency,
            "stats": {
                "total": len(items),
                "kept_count": len(kept),
                "removed_count": len(removed)
            }
        }
