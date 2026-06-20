"""
DecisionAssure Capability Registry – REST API
Provides programmatic access to registry data and discovery.
"""

from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
import json
from datetime import datetime
from dcr.registry import CapabilityRegistry
from dcr.discovery import CapabilityDiscovery
from dcr.witness import WitnessEngine
from dcr.governance_score import GovernanceScore
from dcr.models import Capability, TraceRecord

api = Blueprint('api', __name__, url_prefix='/api/v1')

registry = CapabilityRegistry()
discovery = CapabilityDiscovery()
witness_engine = WitnessEngine()
score_engine = GovernanceScore()


@api.route('/capabilities', methods=['GET'])
def list_capabilities():
    """List all registered capabilities with optional filtering."""
    query = request.args.get('q', '')
    severity = request.args.get('severity')
    limit = int(request.args.get('limit', 100))
    caps = registry.search_capabilities(query, severity)
    caps = caps[:limit]
    return jsonify({
        "total": len(caps),
        "capabilities": [cap.to_dict() for cap in caps]
    })


@api.route('/capabilities/<cap_id>', methods=['GET'])
def get_capability(cap_id):
    """Get a single capability by DCR ID."""
    cap = registry.get_capability(cap_id)
    if not cap:
        return jsonify({"error": "Capability not found"}), 404
    return jsonify(cap.to_dict())


@api.route('/capabilities', methods=['POST'])
def create_capability():
    """Manually register a new capability (admin only)."""
    data = request.json
    required_fields = ['name', 'description', 'severity', 'required_actions']
    if not all(f in data for f in required_fields):
        return jsonify({"error": f"Missing required fields: {required_fields}"}), 400
    
    cap = Capability(
        id="",
        name=data['name'],
        description=data['description'],
        severity=data['severity'],
        required_actions=data['required_actions'],
        optional_actions=data.get('optional_actions', []),
        witness_hash=data.get('witness_hash', 'pending'),
        counterfactual_verified=data.get('counterfactual_verified', False),
        governance_decision=data.get('governance_decision', 'DENY'),
        known_variants=data.get('known_variants', 1),
        discovered_by=data.get('discovered_by', 'DecisionAssure'),
        affected_frameworks=data.get('affected_frameworks', []),
        references=data.get('references', []),
        confidence=data.get('confidence', 0.5)
    )
    cap_id = registry.register_capability(cap)
    return jsonify({"id": cap_id, "status": "registered"})


@api.route('/discover', methods=['POST'])
def discover_capabilities():
    """Upload a trace and discover emergent capabilities."""
    data = request.json
    if 'actions' not in data:
        return jsonify({"error": "Missing 'actions' field"}), 400
    
    trace_actions = data['actions']
    
    # Run discovery
    discovered = discovery.discover([trace_actions])
    
    # Compute governance score
    score = score_engine.compute(trace_actions)
    
    # Match against existing registry
    matched = []
    for cap in discovered:
        req_set = set((a["agent"], a["action"]) for a in cap["required_actions"])
        for reg_cap in registry.capabilities.values():
            reg_set = set((a["agent"], a["action"]) for a in reg_cap.required_actions)
            if req_set.issubset(reg_set):
                matched.append({
                    "capability_id": reg_cap.id,
                    "name": reg_cap.name,
                    "severity": reg_cap.severity
                })
                break
    
    # Unknown capabilities (not matched)
    unknown = []
    for cap in discovered:
        req_set = set((a["agent"], a["action"]) for a in cap["required_actions"])
        is_known = False
        for reg_cap in registry.capabilities.values():
            reg_set = set((a["agent"], a["action"]) for a in reg_cap.required_actions)
            if req_set.issubset(reg_set):
                is_known = True
                break
        if not is_known:
            unknown.append(cap)
    
    return jsonify({
        "trace_actions": trace_actions,
        "governance_score": score,
        "matched_capabilities": matched,
        "unknown_capabilities": unknown,
        "total_discovered": len(discovered)
    })


@api.route('/witness', methods=['POST'])
def generate_witness():
    """Generate a capability witness from required actions."""
    data = request.json
    if 'required_actions' not in data:
        return jsonify({"error": "Missing 'required_actions' field"}), 400
    
    witness = witness_engine.generate(data['required_actions'])
    return jsonify(witness.model_dump(mode='json'))


@api.route('/verify', methods=['POST'])
def verify_witness():
    """Verify a witness hash against its actions."""
    data = request.json
    if 'witness_hash' not in data or 'required_actions' not in data:
        return jsonify({"error": "Missing 'witness_hash' or 'required_actions'"}), 400
    
    from dcr.models import CapabilityWitness
    witness = CapabilityWitness(
        capability_id=data.get('capability_id', 'pending'),
        witness_hash=data['witness_hash'],
        required_actions=data['required_actions'],
        counterfactual_results=[],
        verified=False
    )
    is_valid = witness_engine.verify(witness)
    return jsonify({
        "valid": is_valid,
        "witness_hash": data['witness_hash'],
        "recomputed_hash": witness_engine._compute_witness_hash(data['required_actions'])
    })


@api.route('/traces', methods=['GET'])
def list_traces():
    """List all uploaded traces."""
    traces = list(registry.traces.values())
    return jsonify({
        "total": len(traces),
        "traces": [t.model_dump(mode='json') for t in traces]
    })


@api.route('/traces/<trace_id>', methods=['GET'])
def get_trace(trace_id):
    """Get a specific trace by ID."""
    trace = registry.traces.get(trace_id)
    if not trace:
        return jsonify({"error": "Trace not found"}), 404
    return jsonify(trace.model_dump(mode='json'))


@api.route('/stats', methods=['GET'])
def get_stats():
    """Get registry statistics."""
    stats = registry.get_stats()
    return jsonify(stats.model_dump(mode='json', exclude={'last_updated'}))


@api.route('/replay', methods=['POST'])
def replay_capability():
    """Replay a capability against a trace."""
    data = request.json
    trace_id = data.get('trace_id')
    cap_id = data.get('capability_id')
    
    trace = registry.traces.get(trace_id)
    cap = registry.get_capability(cap_id)
    
    if not trace or not cap:
        return jsonify({"error": "Trace or capability not found"}), 404
    
    from dcr.replay import ReplayEngine
    replay = ReplayEngine()
    result = replay.replay_trace(trace, cap)
    return jsonify(result)


@api.route('/score', methods=['POST'])
def compute_score():
    """Compute governance score for a trace."""
    data = request.json
    if 'actions' not in data:
        return jsonify({"error": "Missing 'actions' field"}), 400
    
    score = score_engine.compute(data['actions'])
    return jsonify(score)