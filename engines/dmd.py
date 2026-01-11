class DMD:
    def __init__(self):
        pass

    def _normalize(self, alternatives):
        # Normalización min-max simple para cada criterio
        if not alternatives:
            return []

        criteria_keys = alternatives[0]["criteria"].keys()
        normalized = [alt.copy() for alt in alternatives]

        for key in criteria_keys:
            values = [alt["criteria"][key] for alt in alternatives]
            v_min = min(values)
            v_max = max(values)

            for alt in normalized:
                if v_max > v_min:
                    alt["criteria"][key] = (alt["criteria"][key] - v_min) / (
                        v_max - v_min
                    )
                else:
                    alt["criteria"][key] = 1.0  # Si todos son iguales, score máximo

        return normalized

    def run(self, payload):
        alternatives = payload.get("alternatives", [])
        weights = payload.get("weights", {})

        if not alternatives:
            return {"best": None, "ranking": []}

        # Normalizar
        norm_alts = self._normalize(alternatives)

        # Calcular scores ponderados
        ranked = []
        for i, alt in enumerate(norm_alts):
            score = 0.0
            for criterion, weight in weights.items():
                score += alt["criteria"].get(criterion, 0) * weight

            ranked.append(
                {
                    "name": alternatives[i]["name"],
                    "score": score,
                    "original_criteria": alternatives[i]["criteria"],
                }
            )

        # Ordenar ranking
        ranked.sort(key=lambda x: x["score"], reverse=True)

        return {"best": ranked[0]["name"] if ranked else None, "ranking": ranked}
