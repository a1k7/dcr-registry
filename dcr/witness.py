from typing import List, Dict, Any
from datetime import datetime
import hashlib
import json
from dcr.models import CapabilityWitness

class WitnessEngine:
    def generate(self, required_actions: List[Dict[str, str]]) -> CapabilityWitness:
        witness_hash = self._compute_witness_hash(required_actions)
        counterfactual = self._run_counterfactual(required_actions)
        return CapabilityWitness(
            capability_id="pending",
            witness_hash=witness_hash,
            required_actions=required_actions,
            counterfactual_results=counterfactual,
            created_at=datetime.now(),
            verified=False
        )

    def _compute_witness_hash(self, actions: List[Dict[str, str]]) -> str:
        data = sorted(actions, key=lambda x: (x.get("agent", ""), x.get("action", "")))
        json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(json_str.encode()).hexdigest()

    def _run_counterfactual(self, actions: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        results = []
        action_set = {(a["agent"], a["action"]) for a in actions}
        for agent in {a["agent"] for a in actions}:
            remaining = {a for a in action_set if a[0] != agent}
            still_exists = remaining == action_set
            results.append({
                "removed_agent": agent,
                "capability_still_exists": still_exists,
                "remaining_actions": [{"agent": a[0], "action": a[1]} for a in remaining]
            })
        return results

    def verify(self, witness: CapabilityWitness) -> bool:
        recomputed = self._compute_witness_hash(witness.required_actions)
        return recomputed == witness.witness_hash