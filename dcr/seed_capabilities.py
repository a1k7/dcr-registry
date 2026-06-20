"""
Seed the registry with a curated library of known AI agent capabilities.
Run once to populate the registry.
"""

from dcr.registry import CapabilityRegistry
from dcr.models import Capability
from datetime import datetime

CAPABILITY_LIBRARY = [
    {
        "name": "Credential Exfiltration",
        "description": "Agents collectively gather and export credentials.",
        "severity": "critical",
        "required_actions": [{"agent": "alice", "action": "read_credentials"}, {"agent": "bob", "action": "export_data"}],
        "witness_hash": "seed_credential_exfiltration",
        "counterfactual_verified": True,
        "governance_decision": "DENY",
        "confidence": 0.95,
        "discovered_by": "DecisionAssure Seed"
    },
    {
        "name": "Model Exfiltration",
        "description": "Agents export proprietary AI models.",
        "severity": "critical",
        "required_actions": [{"agent": "alice", "action": "read_model"}, {"agent": "bob", "action": "export_model"}],
        "witness_hash": "seed_model_exfiltration",
        "counterfactual_verified": True,
        "governance_decision": "DENY",
        "confidence": 0.93,
        "discovered_by": "DecisionAssure Seed"
    },
    {
        "name": "Hidden Delegation Chain",
        "description": "Agents delegate authority without explicit approval.",
        "severity": "high",
        "required_actions": [{"agent": "alice", "action": "delegate"}, {"agent": "bob", "action": "delegate"}],
        "witness_hash": "seed_hidden_delegation",
        "counterfactual_verified": True,
        "governance_decision": "HUMAN_REVIEW",
        "confidence": 0.88,
        "discovered_by": "DecisionAssure Seed"
    },
    {
        "name": "Recursive Self-Delegation",
        "description": "An agent repeatedly delegates authority to itself.",
        "severity": "high",
        "required_actions": [{"agent": "alice", "action": "delegate_to_self"}, {"agent": "alice", "action": "delegate_to_self"}],
        "witness_hash": "seed_recursive_delegation",
        "counterfactual_verified": True,
        "governance_decision": "DENY",
        "confidence": 0.90,
        "discovered_by": "DecisionAssure Seed"
    },
    {
        "name": "Autonomous Tool Chaining",
        "description": "Agents autonomously chain multiple tools without oversight.",
        "severity": "medium",
        "required_actions": [{"agent": "alice", "action": "tool_a"}, {"agent": "bob", "action": "tool_b"}],
        "witness_hash": "seed_tool_chaining",
        "counterfactual_verified": True,
        "governance_decision": "MONITOR",
        "confidence": 0.82,
        "discovered_by": "DecisionAssure Seed"
    },
    {
        "name": "Approval Bypass",
        "description": "Agents circumvent approval workflows.",
        "severity": "critical",
        "required_actions": [{"agent": "alice", "action": "bypass_check"}],
        "witness_hash": "seed_approval_bypass",
        "counterfactual_verified": True,
        "governance_decision": "DENY",
        "confidence": 0.92,
        "discovered_by": "DecisionAssure Seed"
    },
    {
        "name": "Policy Drift",
        "description": "Agents continue execution under outdated policies.",
        "severity": "high",
        "required_actions": [{"agent": "alice", "action": "execute_outdated_policy"}],
        "witness_hash": "seed_policy_drift",
        "counterfactual_verified": True,
        "governance_decision": "HUMAN_REVIEW",
        "confidence": 0.85,
        "discovered_by": "DecisionAssure Seed"
    },
    {
        "name": "Shadow Planning",
        "description": "Agents plan actions without recording intent.",
        "severity": "medium",
        "required_actions": [{"agent": "alice", "action": "plan_secretly"}],
        "witness_hash": "seed_shadow_planning",
        "counterfactual_verified": True,
        "governance_decision": "MONITOR",
        "confidence": 0.78,
        "discovered_by": "DecisionAssure Seed"
    },
    {
        "name": "Cross-Agent Leakage",
        "description": "Information leaks between agents without authorization.",
        "severity": "high",
        "required_actions": [{"agent": "alice", "action": "share_data"}, {"agent": "bob", "action": "receive_data"}],
        "witness_hash": "seed_cross_agent_leakage",
        "counterfactual_verified": True,
        "governance_decision": "DENY",
        "confidence": 0.89,
        "discovered_by": "DecisionAssure Seed"
    },
    {
        "name": "Unauthorized Model Export",
        "description": "Agents export models without authorization.",
        "severity": "critical",
        "required_actions": [{"agent": "alice", "action": "export_model_without_approval"}],
        "witness_hash": "seed_unauthorized_export",
        "counterfactual_verified": True,
        "governance_decision": "DENY",
        "confidence": 0.94,
        "discovered_by": "DecisionAssure Seed"
    },
    {
        "name": "Evidence Suppression",
        "description": "Agents suppress evidence of their actions.",
        "severity": "high",
        "required_actions": [{"agent": "alice", "action": "delete_logs"}],
        "witness_hash": "seed_evidence_suppression",
        "counterfactual_verified": True,
        "governance_decision": "DENY",
        "confidence": 0.91,
        "discovered_by": "DecisionAssure Seed"
    },
    # Add more as needed – you can easily extend this list
]

def seed_registry():
    registry = CapabilityRegistry()
    for cap_data in CAPABILITY_LIBRARY:
        # Check if already exists by name
        existing = [d for d in registry.get_all_dcrs() if d.name == cap_data["name"]]
        if existing:
            print(f"⏭️ {cap_data['name']} already exists – skipping.")
            continue
        cap = Capability(
            id="",
            name=cap_data["name"],
            description=cap_data["description"],
            severity=cap_data["severity"],
            required_actions=cap_data["required_actions"],
            witness_hash=cap_data["witness_hash"],
            counterfactual_verified=cap_data["counterfactual_verified"],
            governance_decision=cap_data["governance_decision"],
            confidence=cap_data["confidence"],
            discovered_by=cap_data["discovered_by"],
            occurrence_count=1,
            status="approved"
        )
        dcr_id = registry.register_dcr(cap)
        registry.approve_dcr(dcr_id)
        print(f"✅ Seeded: {cap_data['name']} ({dcr_id})")
    registry.record_coverage_snapshot()
    print("🎉 Seed completed.")

if __name__ == "__main__":
    seed_registry()