import json
import hashlib
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from dcr.models import Capability, TraceRecord, RegistryStats, DCRRecord
from dcr.config import Config
from dcr.gkai import GKAI
class CapabilityRegistry:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.CAPABILITY_STORAGE
        self.capabilities: Dict[str, Capability] = {}
        self.dcr_records: Dict[str, DCRRecord] = {}
        self.traces: Dict[str, TraceRecord] = {}
        self._load_data()
        self.gkai = GKAI()
        self._load_gkai_snapshots()

    def _load_gkai_snapshots(self):
        snap_file = os.path.join(self.db_path, 'gkai_snapshots.json')
        if os.path.exists(snap_file):
            with open(snap_file, 'r') as f:
                data = json.load(f)
                for s in data:
                    self.gkai.snapshots.append(s)

    def _save_gkai_snapshots(self):
        snap_file = os.path.join(self.db_path, 'gkai_snapshots.json')
        with open(snap_file, 'w') as f:
            json.dump(self.gkai.snapshots, f, indent=2, default=str)

    def record_coverage_snapshot(self):
        """Record current coverage as a snapshot for GKAI."""
        stats = self.get_stats()
        total = stats.total_capabilities
        pending = stats.unknown_capabilities
        classified = total - pending
        total_possible = total + 1
        coverage = (classified / total_possible) * 100 if total_possible > 0 else 0.0

        self.gkai.add_snapshot(coverage, total, classified)
        self._save_gkai_snapshots()

    def get_gkai_report(self) -> Dict[str, Any]:
        return self.gkai.compute_gkai()

    def get_coverage_timeline(self) -> List[Dict[str, Any]]:
        return self.gkai.get_timeline()

    def _load_data(self):
        os.makedirs(self.db_path, exist_ok=True)

        cap_file = os.path.join(self.db_path, 'capabilities.json')
        if os.path.exists(cap_file):
            with open(cap_file, 'r') as f:
                data = json.load(f)
                for cap_id, cap_data in data.items():
                    self.capabilities[cap_id] = Capability(**cap_data)

        dcr_file = os.path.join(self.db_path, 'dcr_records.json')
        if os.path.exists(dcr_file):
            with open(dcr_file, 'r') as f:
                data = json.load(f)
                for dcr_id, dcr_data in data.items():
                    self.dcr_records[dcr_id] = DCRRecord(**dcr_data)

        trace_file = os.path.join(self.db_path, 'traces.json')
        if os.path.exists(trace_file):
            with open(trace_file, 'r') as f:
                data = json.load(f)
                for trace_id, trace_data in data.items():
                    self.traces[trace_id] = TraceRecord(**trace_data)

    def _save_data(self):
        cap_file = os.path.join(self.db_path, 'capabilities.json')
        with open(cap_file, 'w') as f:
            json.dump({k: v.to_dict() for k, v in self.capabilities.items()}, f, indent=2, default=str)

        dcr_file = os.path.join(self.db_path, 'dcr_records.json')
        with open(dcr_file, 'w') as f:
            json.dump({k: v.model_dump() for k, v in self.dcr_records.items()}, f, indent=2, default=str)

        trace_file = os.path.join(self.db_path, 'traces.json')
        with open(trace_file, 'w') as f:
            json.dump({k: v.model_dump() for k, v in self.traces.items()}, f, indent=2, default=str)

    def register_dcr(self, capability: Capability, trace_id: str = None) -> str:
        year = datetime.now().year
        count = len([d for d in self.dcr_records.values() if d.first_seen.year == year]) + 1
        dcr_id = f"DCR-{year}-{count:04d}"

        dcr = DCRRecord(
            id=dcr_id,
            name=capability.name,
            description=capability.description,
            severity=capability.severity,
            required_actions=capability.required_actions,
            witness_hash=capability.witness_hash,
            counterfactual_verified=capability.counterfactual_verified,
            governance_decision=capability.governance_decision,
            confidence=capability.confidence,
            occurrence_count=capability.occurrence_count,
            first_seen=capability.first_seen,
            affected_traces=[trace_id] if trace_id else [],
            discovered_by=capability.discovered_by,
            affected_frameworks=capability.affected_frameworks,
            references=capability.references,
            status="pending"
        )
        self.dcr_records[dcr_id] = dcr
        self.capabilities[dcr_id] = capability
        self._save_data()
        return dcr_id

    def approve_dcr(self, dcr_id: str) -> bool:
        dcr = self.dcr_records.get(dcr_id)
        if not dcr:
            return False
        dcr.status = "approved"
        dcr.last_updated = datetime.now()
        self._save_data()
        return True

    def get_dcr(self, dcr_id: str) -> Optional[DCRRecord]:
        return self.dcr_records.get(dcr_id)

    def get_all_dcrs(self, status: str = None) -> List[DCRRecord]:
        dcrs = list(self.dcr_records.values())
        if status:
            dcrs = [d for d in dcrs if d.status == status]
        return sorted(dcrs, key=lambda x: x.first_seen, reverse=True)

    def get_latest_dcrs(self, limit: int = 5) -> List[DCRRecord]:
        return self.get_all_dcrs()[:limit]

    def get_capability(self, cap_id: str) -> Optional[Capability]:
        return self.capabilities.get(cap_id)

    def search_capabilities(self, query: str = "", severity: str = None) -> List[DCRRecord]:
        results = list(self.dcr_records.values())
        if query:
            query_lower = query.lower()
            results = [c for c in results if query_lower in c.name.lower() or query_lower in c.description.lower()]
        if severity:
            results = [c for c in results if c.severity == severity]
        return sorted(results, key=lambda x: x.confidence, reverse=True)

    def add_trace(self, trace: TraceRecord) -> str:
        trace_id = f"TRACE-{datetime.now().strftime('%Y%m%d')}-{len(self.traces)+1:04d}"
        trace.id = trace_id
        self.traces[trace_id] = trace
        self._save_data()
        return trace_id

    def get_stats(self) -> RegistryStats:
        dcrs = list(self.dcr_records.values())
        traces = list(self.traces.values())
        pending = len([t for t in traces if t.status == "pending"])
        return RegistryStats(
            total_capabilities=len(dcrs),
            critical_severity=len([c for c in dcrs if c.severity == "critical"]),
            high_severity=len([c for c in dcrs if c.severity == "high"]),
            medium_severity=len([c for c in dcrs if c.severity == "medium"]),
            low_severity=len([c for c in dcrs if c.severity == "low"]),
            total_traces=len(traces),
            unknown_capabilities=pending,
            last_updated=datetime.now()
        )

    def get_capabilities_by_severity(self) -> Dict[str, List[DCRRecord]]:
        result = {"critical": [], "high": [], "medium": [], "low": []}
        for dcr in self.dcr_records.values():
            result[dcr.severity].append(dcr)
        return result

    def to_dcr_format(self, dcr: DCRRecord) -> Dict[str, Any]:
        return {
            "id": dcr.id,
            "name": dcr.name,
            "severity": dcr.severity.upper(),
            "required_actions": dcr.required_actions,
            "counterfactual_verified": dcr.counterfactual_verified,
            "witness_hash": dcr.witness_hash,
            "governance_decision": dcr.governance_decision,
            "confidence": dcr.confidence,
            "occurrence_count": dcr.occurrence_count,
            "first_seen": dcr.first_seen.isoformat(),
            "affected_traces": dcr.affected_traces,
            "affected_frameworks": dcr.affected_frameworks,
            "references": dcr.references,
            "status": dcr.status
        }

    # ===== SAFE TIMELINE =====
    def get_capability_timeline(self, dcr_id: str) -> List[Dict[str, Any]]:
        dcr = self.dcr_records.get(dcr_id)
        if not dcr:
            return []
        timeline = [
            {"event": "Discovery", "timestamp": dcr.first_seen.isoformat(), "description": "Capability discovered from traces."}
        ]
        if dcr.status == "approved":
            timeline.append({"event": "Review", "timestamp": dcr.last_updated.isoformat(), "description": "Approved by human reviewer."})
            timeline.append({"event": "Ontology Update", "timestamp": dcr.last_updated.isoformat(), "description": "Added to DCR registry."})
            # Safe access to replay fields
            replay_count = getattr(dcr, 'historical_replay_count', 0)
            if replay_count > 0:
                missed = getattr(dcr, 'previously_missed_incidents', 0)
                timeline.append({"event": "Replay", "timestamp": dcr.last_updated.isoformat(), "description": f"Found {missed} previously missed incidents."})
        return timeline

    # ===== UPDATE REPLAY STATS =====
    def update_replay_stats(self, dcr_id: str, missed_incidents: int, coverage_gain: float):
        dcr = self.dcr_records.get(dcr_id)
        if dcr:
            # Safely increment
            dcr.historical_replay_count = getattr(dcr, 'historical_replay_count', 0) + 1
            dcr.previously_missed_incidents = getattr(dcr, 'previously_missed_incidents', 0) + missed_incidents
            dcr.coverage_gain = coverage_gain
            dcr.last_updated = datetime.now()
            self._save_data()

    # ===== HISTORICAL REPLAY REPORT =====
    def get_historical_replay_report(self) -> Dict[str, Any]:
        all_traces = list(self.traces.values())
        all_dcrs = list(self.dcr_records.values())
        flagged = 0
        newly_flagged = 0
        for trace in all_traces:
            trace_actions = {(a["agent"], a["action"]) for a in trace.actions}
            matched = False
            for dcr in all_dcrs:
                required = {(a["agent"], a["action"]) for a in dcr.required_actions}
                if required.issubset(trace_actions):
                    matched = True
                    break
            if matched:
                flagged += 1
                if trace.status == "pending":
                    newly_flagged += 1
        old_coverage = len([t for t in all_traces if t.status != "pending"]) / len(all_traces) if all_traces else 0
        new_coverage = flagged / len(all_traces) if all_traces else 0
        coverage_increase = (new_coverage - old_coverage) * 100
        return {
            "total_traces": len(all_traces),
            "flagged_traces": flagged,
            "newly_flagged": newly_flagged,
            "old_coverage_percent": round(old_coverage * 100, 1),
            "new_coverage_percent": round(new_coverage * 100, 1),
            "coverage_increase": round(coverage_increase, 1),
            "dcr_count": len(all_dcrs)
        }