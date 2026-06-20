"""
GKAI – Governance Knowledge Accumulation Index
Measures long-term governance learning and coverage growth.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta

class GKAI:
    def __init__(self):
        self.snapshots: List[Dict[str, Any]] = []

    def add_snapshot(self, coverage: float, total_capabilities: int, classified: int, timestamp: datetime = None):
        if timestamp is None:
            timestamp = datetime.now()
        self.snapshots.append({
            "timestamp": timestamp.isoformat(),
            "coverage": coverage,
            "total_capabilities": total_capabilities,
            "classified": classified
        })

    def compute_gkai(self) -> Dict[str, Any]:
        """Compute GKAI (Governance Knowledge Accumulation Index)."""
        if len(self.snapshots) < 2:
            return {
                "gkai": 0.0,
                "base_coverage": self.snapshots[0]["coverage"] if self.snapshots else 0.0,
                "current_coverage": self.snapshots[-1]["coverage"] if self.snapshots else 0.0,
                "knowledge_gain": 0.0,
                "average_gain_per_version": 0.0,
                "versions": len(self.snapshots)
            }

        base = self.snapshots[0]["coverage"]
        current = self.snapshots[-1]["coverage"]
        knowledge_gain = current - base
        avg_gain = knowledge_gain / (len(self.snapshots) - 1)

        # GKAI formula: weighted combination of coverage gain and knowledge growth rate
        # Scale: 0-100, higher is better
        gkai = 0.5 * (current) + 0.3 * (knowledge_gain) + 0.2 * (avg_gain * 10)
        
        # ===== CLAMP: NEVER SHOW 100 =====
        gkai = min(max(gkai, 0), 99.9)  # Ensures GKAI never appears as 100

        return {
            "gkai": round(gkai, 2),
            "base_coverage": round(base, 1),
            "current_coverage": round(current, 1),
            "knowledge_gain": round(knowledge_gain, 1),
            "average_gain_per_version": round(avg_gain, 1),
            "versions": len(self.snapshots)
        }

    def get_timeline(self) -> List[Dict[str, Any]]:
        return self.snapshots