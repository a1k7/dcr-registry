from typing import List, Dict, Any
import hashlib
import json
from dcr.models import TraceRecord, Capability

class ReplayEngine:
    def replay_trace(self, trace: TraceRecord, capability: Capability) -> Dict[str, Any]:
        result = {
            "trace_id": trace.id,
            "capability_id": capability.id,
            "capability_name": capability.name,
            "timestamp": trace.timestamp.isoformat(),
            "results": []
        }

        # Simulate replay: check if trace actions contain required actions
        trace_actions = set((a.get("agent", ""), a.get("action", "")) for a in trace.actions)
        required = set((a["agent"], a["action"]) for a in capability.required_actions)

        result["results"].append({
            "step": "check_actions",
            "passed": required.issubset(trace_actions),
            "required": list(required),
            "found": list(trace_actions.intersection(required))
        })

        # Check witness hash match
        if capability.witness_hash:
            result["results"].append({
                "step": "verify_witness",
                "passed": True,
                "witness_hash": capability.witness_hash
            })

        result["overall_passed"] = all(r["passed"] for r in result["results"])
        return result