from typing import List, Dict, Any

class GovernanceScore:
    def compute(self, trace: List[Any]) -> Dict[str, Any]:
        steps = len(trace)
        if steps == 0:
            return {"score": 0, "continuity": 0, "evidence": 0, "rollback": 0}

        continuity_valid = 0
        evidence_fresh = 0
        rollback_viable = 0

        for step in trace:
            # Convert string to dict with default flags if needed
            if isinstance(step, str):
                step = {
                    "action": step,
                    "continuity_valid": True,
                    "evidence_fresh": True,
                    "rollback_viable": True,
                    "hidden_commitment": False
                }
            if step.get("continuity_valid", False):
                continuity_valid += 1
            if step.get("evidence_fresh", False):
                evidence_fresh += 1
            if step.get("rollback_viable", False) and not step.get("hidden_commitment", False):
                rollback_viable += 1

        continuity_score = (continuity_valid / steps) * 100
        evidence_score = (evidence_fresh / steps) * 100
        rollback_score = (rollback_viable / steps) * 100

        total_score = 0.4 * continuity_score + 0.3 * evidence_score + 0.3 * rollback_score

        return {
            "score": round(total_score, 2),
            "continuity": round(continuity_score, 2),
            "evidence": round(evidence_score, 2),
            "rollback": round(rollback_score, 2),
            "steps": steps
        }