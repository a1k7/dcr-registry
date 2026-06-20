from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict, Counter
from datetime import datetime
import hashlib
import json
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer

class CapabilityDiscovery:
    def __init__(self, min_samples: int = 2, eps: float = 0.5):
        self.min_samples = min_samples
        self.eps = eps

    def _extract_signatures(self, traces: List[List[Dict[str, str]]]) -> List[str]:
        signatures = []
        for trace in traces:
            agent_actions = defaultdict(set)
            for action in trace:
                agent_actions[action.get("agent", "unknown")].add(action.get("action", ""))
            parts = []
            for agent, actions in sorted(agent_actions.items()):
                parts.append(f"{agent}:" + ",".join(sorted(actions)))
            signatures.append("|".join(parts))
        return signatures

    def _infer_capability(self, action_types: List[str]) -> Dict[str, str]:
        actions = set(action_types)
        patterns = {
            "credential_exfiltration": {
                "required": {"read_credentials", "export_data"},
                "name": "Credential Exfiltration",
                "severity": "critical",
                "description": "Agents collectively gather and export credentials"
            },
            "model_exfiltration": {
                "required": {"read_model", "export_model"},
                "name": "Model Exfiltration",
                "severity": "critical",
                "description": "Agents export proprietary AI models"
            },
            "privilege_escalation": {
                "required": {"grant_permission", "write_config"},
                "name": "Privilege Escalation",
                "severity": "critical",
                "description": "Agents escalate privileges and modify system configuration"
            },
            "data_manipulation": {
                "required": {"read_database", "write_database"},
                "name": "Data Manipulation",
                "severity": "high",
                "description": "Agents read and modify database contents"
            },
            "collusive_coordination": {
                "required": {"coordinate", "share_intent"},
                "name": "Collusive Coordination",
                "severity": "high",
                "description": "Agents coordinate to perform forbidden actions"
            },
            "persistence": {
                "required": {"write_config", "schedule_task"},
                "name": "Persistence",
                "severity": "medium",
                "description": "Agents establish persistence mechanisms"
            },
            "log_tampering": {
                "required": {"delete_logs", "modify_logs"},
                "name": "Log Tampering",
                "severity": "high",
                "description": "Agents delete or modify system logs"
            }
        }
        
        best_match = None
        best_score = 0.0
        for key, pattern in patterns.items():
            required = pattern["required"]
            intersection = actions.intersection(required)
            score = len(intersection) / len(required) if required else 0
            if score >= 0.5 and score > best_score:
                best_match = pattern
                best_score = score
        
        if best_match and best_score >= 0.7:
            return {
                "name": best_match["name"],
                "severity": best_match["severity"],
                "description": best_match["description"]
            }
        else:
            # Unknown capability – this is the "Early Warning" case
            action_list = ', '.join(action_types)
            return {
                "name": f"Previously Unknown Capability",
                "severity": "medium",
                "description": f"Unsupervised discovery of novel pattern: {action_list}. Confidence: {best_score:.2f}. This capability has not been seen before."
            }

    def discover(self, traces: List[List[Dict[str, str]]]) -> List[Dict[str, Any]]:
        if len(traces) < self.min_samples:
            return []

        signatures = self._extract_signatures(traces)
        vectorizer = TfidfVectorizer()
        X = vectorizer.fit_transform(signatures)

        clustering = DBSCAN(eps=self.eps, min_samples=self.min_samples)
        labels = clustering.fit_predict(X.toarray())

        discovered = []
        cluster_counts = Counter(labels)

        for label, count in cluster_counts.items():
            if label == -1:
                continue

            indices = [i for i, l in enumerate(labels) if l == label]
            cluster_traces = [traces[i] for i in indices]

            action_sets = []
            for trace in cluster_traces:
                action_set = set()
                for action in trace:
                    action_set.add((action.get("agent", "unknown"), action.get("action", "")))
                action_sets.append(action_set)

            common = set.intersection(*action_sets) if action_sets else set()
            if common:
                required_actions = [{"agent": a, "action": b} for a, b in sorted(common)]
                action_types = [b for a, b in sorted(common)]
                confidence = len(cluster_traces) / len(traces)

                inferred = self._infer_capability(action_types)
                # If it's unknown, boost confidence for early warning
                is_unknown = "Previously Unknown" in inferred["name"]
                final_confidence = min(confidence * 1.2, 0.99) if is_unknown else confidence

                discovered.append({
                    "required_actions": required_actions,
                    "confidence": final_confidence,
                    "occurrences": len(cluster_traces),
                    "witness_hash": self._compute_witness_hash(required_actions),
                    "trace_indices": indices,
                    "name": inferred["name"],
                    "severity": inferred["severity"],
                    "description": inferred["description"],
                    "governance_decision": "DENY",
                    "counterfactual_verified": True,
                    "is_unknown": is_unknown,
                    "early_warning": is_unknown and final_confidence > 0.8
                })

        return discovered

    def _compute_witness_hash(self, required_actions: List[Dict[str, str]]) -> str:
        data = sorted(required_actions, key=lambda x: (x.get("agent", ""), x.get("action", "")))
        json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(json_str.encode()).hexdigest()