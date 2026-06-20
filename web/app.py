from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from flask_cors import CORS
import os
import json
import hashlib
import traceback
from datetime import datetime
from dcr.registry import CapabilityRegistry
from dcr.discovery import CapabilityDiscovery
from dcr.witness import WitnessEngine
from dcr.replay import ReplayEngine
from dcr.governance_score import GovernanceScore
from dcr.models import Capability, TraceRecord, DCRRecord
from dcr.config import Config
from dcr.adapters import parse_trace
from dcr.report_generator import DCRReportGenerator

# Set the reports directory path
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = Config.SECRET_KEY
CORS(app)

registry = CapabilityRegistry()
discovery = CapabilityDiscovery()
witness_engine = WitnessEngine()
replay_engine = ReplayEngine()
score_engine = GovernanceScore()

@app.route('/')
def index():
    stats = registry.get_stats()
    latest = registry.get_latest_dcrs(limit=5)

    # Compute previously missed incidents
    all_traces = list(registry.traces.values())
    previously_missed = len([t for t in all_traces if t.discovered_capabilities and len(t.discovered_capabilities) > 0])

    # Coverage percent
    total_caps = stats.total_capabilities
    pending = stats.unknown_capabilities
    classified = total_caps - pending
    total_possible = total_caps + 1
    coverage_percent = round((classified / total_possible) * 100, 1) if total_possible > 0 else 0.0

    stats_dict = stats.model_dump(mode='json', exclude={'last_updated'})
    stats_dict['previously_missed'] = previously_missed
    stats_dict['coverage_percent'] = coverage_percent
    stats_dict['gkai'] = registry.get_gkai_report().get('gkai', 0.0)

    timeline = registry.get_coverage_timeline()

    return render_template('index.html', stats=stats_dict, latest=latest, timeline=timeline)

@app.route('/registry')
def registry_page():
    capabilities = registry.get_all_dcrs()
    return render_template('registry.html', capabilities=capabilities)

# ===== SINGLE capability detail page =====
@app.route('/capability/<dcr_id>')
def capability_page(dcr_id):
    dcr = registry.get_dcr(dcr_id)
    if not dcr:
        return "Capability not found", 404
    timeline = registry.get_capability_timeline(dcr_id)
    return render_template('capability.html', capability=dcr, timeline=timeline)

# ===== Replay a capability (API) =====
@app.route('/capability/<dcr_id>/replay')
def replay_capability(dcr_id):
    dcr = registry.get_dcr(dcr_id)
    if not dcr:
        return jsonify({"error": "Capability not found"}), 404

    traces = list(registry.traces.values())
    missed = 0
    required = {(a["agent"], a["action"]) for a in dcr.required_actions}
    for trace in traces:
        trace_actions = {(a["agent"], a["action"]) for a in trace.actions}
        if required.issubset(trace_actions):
            missed += 1

    registry.update_replay_stats(dcr_id, missed, 0.0)
    return jsonify({
        "dcr_id": dcr_id,
        "missed_incidents": missed,
        "total_traces": len(traces),
        "coverage_gain": 0.0
    })

@app.route('/report/<trace_id>')
def download_report(trace_id):
    """Generate and download PDF report for a specific trace."""
    report_gen = DCRReportGenerator(registry, output_dir=REPORTS_DIR)
    filename = report_gen.generate(trace_id)
    return send_file(filename, as_attachment=True)

@app.route('/api/timeline')
def coverage_timeline():
    timeline = registry.get_coverage_timeline()
    return jsonify(timeline)

@app.route('/api/gkai')
def gkai_report():
    report = registry.get_gkai_report()
    return jsonify(report)

# ===== Upload trace =====
@app.route('/upload', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'POST':
        try:
            trace_data = request.json or {}
            if 'actions' not in trace_data and 'trace' not in trace_data:
                return jsonify({"error": "Missing 'actions' or 'trace' field"}), 400

            if 'trace' in trace_data:
                raw_trace = trace_data['trace']
                framework = trace_data.get('framework', 'auto')
                actions = parse_trace(raw_trace, framework)
                if not actions:
                    return jsonify({"error": "Could not parse trace. Please provide a list of actions."}), 400
            else:
                actions = trace_data['actions']
                if not isinstance(actions, list):
                    return jsonify({"error": "'actions' must be a list"}), 400

            if len(actions) == 0:
                return jsonify({"error": "'actions' list cannot be empty"}), 400

            # Compute governance score
            score_result = score_engine.compute(actions)

            # Discover capabilities
            discovered = discovery.discover([actions])

            # Register DCRs for discovered capabilities
            registered_dcrs = []
            for cap_data in discovered:
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
                    occurrence_count=cap_data["occurrences"],
                    discovered_by="DecisionAssure"
                )
                dcr_id = registry.register_dcr(cap, trace_id=None)
                registered_dcrs.append({
                    "id": dcr_id,
                    "name": cap_data["name"],
                    "severity": cap_data["severity"],
                    "confidence": cap_data["confidence"],
                    "is_unknown": cap_data.get("is_unknown", False),
                    "early_warning": cap_data.get("early_warning", False)
                })

            # Match against registry
            matched = []
            for cap_data in discovered:
                for dcr in registry.get_all_dcrs():
                    required_actions_set = {(a["agent"], a["action"]) for a in dcr.required_actions}
                    trace_action_set = {(a["agent"], a["action"]) for a in actions}
                    if required_actions_set.issubset(trace_action_set):
                        if dcr.id not in matched:
                            matched.append(dcr.id)

            # Create trace record
            trace = TraceRecord(
                id="",
                trace_hash=hashlib.sha256(json.dumps(actions).encode()).hexdigest(),
                actions=actions,
                discovered_capabilities=matched,
                governance_score=score_result['score'],
                uploaded_by=trace_data.get('uploaded_by', 'anonymous'),
                status="pending" if not matched else "approved"
            )
            trace_id = registry.add_trace(trace)

            # ===== RECORD COVERAGE SNAPSHOT AFTER TRACE IS SAVED =====
            registry.record_coverage_snapshot()

            # Update affected traces for each DCR
            for dcr_id in matched:
                dcr = registry.get_dcr(dcr_id)
                if dcr and trace_id not in dcr.affected_traces:
                    dcr.affected_traces.append(trace_id)
                    dcr.occurrence_count += 1
                    registry._save_data()

            return jsonify({
                "trace_id": trace_id,
                "governance_score": score_result,
                "matched_capabilities": matched,
                "registered_dcrs": registered_dcrs,
                "status": trace.status,
                "dcr_count": len(registry.get_all_dcrs()),
                "early_warnings": [d for d in registered_dcrs if d.get("early_warning")]
            })

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            traceback.print_exc()
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    return render_template('upload.html')

# ===== API endpoints =====
@app.route('/api/capabilities')
def api_capabilities():
    query = request.args.get('q', '')
    severity = request.args.get('severity')
    caps = registry.search_capabilities(query, severity)
    return jsonify([dcr.model_dump() for dcr in caps])

@app.route('/api/capability/<dcr_id>')
def api_capability(dcr_id):
    dcr = registry.get_dcr(dcr_id)
    if not dcr:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dcr.model_dump())

@app.route('/api/stats')
def api_stats():
    stats = registry.get_stats()
    return jsonify(stats.model_dump(mode='json', exclude={'last_updated'}))

@app.route('/api/replay', methods=['POST'])
def api_replay():
    data = request.json
    trace_id = data.get('trace_id')
    dcr_id = data.get('capability_id')

    trace = registry.traces.get(trace_id)
    dcr = registry.get_dcr(dcr_id)

    if not trace or not dcr:
        return jsonify({"error": "Trace or capability not found"}), 404

    result = replay_engine.replay_trace(trace, dcr)
    return jsonify(result)

@app.route('/api/report')
def replay_report():
    report = registry.get_historical_replay_report()
    return jsonify(report)

# ===== Admin =====
@app.route('/admin')
def admin_page():
    pending = [t for t in registry.traces.values() if t.status == "pending"]
    dcrs = registry.get_all_dcrs(status="pending")
    return render_template('admin.html', pending=pending, dcrs=dcrs)

@app.route('/api/admin/approve', methods=['POST'])
def approve_capability():
    data = request.json
    trace_id = data.get('trace_id')
    name = data.get('name')
    severity = data.get('severity', 'medium')

    trace = registry.traces.get(trace_id)
    if not trace:
        return jsonify({"error": "Trace not found"}), 404

    cap = Capability(
        id="",
        name=name,
        description=f"Discovered from trace {trace_id}",
        severity=severity,
        required_actions=[{"agent": a["agent"], "action": a["action"]} for a in trace.actions[:3]],
        witness_hash=trace.trace_hash,
        counterfactual_verified=True,
        first_seen=datetime.now(),
        confidence=0.8,
        occurrence_count=1,
        discovered_by="DecisionAssure"
    )
    dcr_id = registry.register_dcr(cap, trace_id)
    registry.approve_dcr(dcr_id)

    trace.status = "approved"
    trace.discovered_capabilities.append(dcr_id)
    registry._save_data()

    # ===== RECORD COVERAGE SNAPSHOT AFTER APPROVAL =====
    registry.record_coverage_snapshot()

    return jsonify({"dcr_id": dcr_id, "status": "approved"})

@app.route('/api/admin/reject', methods=['POST'])
def reject_capability():
    data = request.json
    trace_id = data.get('trace_id')

    trace = registry.traces.get(trace_id)
    if not trace:
        return jsonify({"error": "Trace not found"}), 404

    trace.status = "rejected"
    registry._save_data()

    return jsonify({"status": "rejected"})

# ===== Pilot page =====
@app.route('/pilot')
def pilot_page():
    return render_template('pilot.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=port)