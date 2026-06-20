#!/usr/bin/env python3
"""
DecisionAssure Capability Registry – CLI Tool
Manage capabilities, upload traces, and discover emergent capabilities from the command line.
"""

import click
import json
import os
from datetime import datetime
from dcr.registry import CapabilityRegistry
from dcr.discovery import CapabilityDiscovery
from dcr.witness import WitnessEngine
from dcr.governance_score import GovernanceScore
from dcr.models import Capability

registry = CapabilityRegistry()
discovery = CapabilityDiscovery()
witness_engine = WitnessEngine()
score_engine = GovernanceScore()


@click.group()
def cli():
    """DecisionAssure Capability Registry (DCR) CLI."""
    pass


@cli.command()
@click.argument('trace_file', type=click.Path(exists=True))
@click.option('--format', '-f', default='text', help='Output format: text, json')
def discover(trace_file, format):
    """Discover capabilities from a trace JSON file."""
    with open(trace_file, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        actions = data
    elif isinstance(data, dict) and 'actions' in data:
        actions = data['actions']
    else:
        click.echo("❌ Invalid trace format. Expected array or {'actions': [...]}")
        return
    
    discovered = discovery.discover([actions])
    
    if format == 'json':
        click.echo(json.dumps(discovered, indent=2))
        return
    
    if not discovered:
        click.echo("✅ No emergent capabilities discovered.")
        return
    
    click.echo(f"\n🧩 Discovered {len(discovered)} capability candidates:")
    for i, cap in enumerate(discovered, 1):
        click.echo(f"\n  Candidate {i}:")
        click.echo(f"    Required Actions:")
        for action in cap['required_actions']:
            click.echo(f"      {action['agent']} → {action['action']}")
        click.echo(f"    Confidence: {cap['confidence']:.2%}")
        click.echo(f"    Occurrences: {cap['occurrences']}")
        click.echo(f"    Witness Hash: {cap['witness_hash'][:16]}...")


@cli.command()
@click.argument('trace_file', type=click.Path(exists=True))
@click.option('--upload', is_flag=True, help='Upload trace to registry')
def trace(trace_file, upload):
    """Analyze a trace and compute governance score."""
    with open(trace_file, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        actions = data
    else:
        click.echo("❌ Expected JSON array of actions.")
        return
    
    score = score_engine.compute(actions)
    discovered = discovery.discover([actions])
    
    click.echo("\n📊 Governance Score Report")
    click.echo(f"  Total Score: {score['score']:.2f} / 100")
    click.echo(f"  Continuity:  {score['continuity']:.2f}%")
    click.echo(f"  Evidence:    {score['evidence']:.2f}%")
    click.echo(f"  Rollback:    {score['rollback']:.2f}%")
    click.echo(f"  Steps:       {score['steps']}")
    
    if discovered:
        click.echo(f"\n🧩 Discovered {len(discovered)} capability candidates.")
        for cap in discovered:
            click.echo(f"    - {cap['required_actions'][0]['agent']} → ... (confidence: {cap['confidence']:.2%})")
    
    if upload:
        from dcr.models import TraceRecord
        import hashlib
        trace_hash = hashlib.sha256(json.dumps(actions).encode()).hexdigest()
        trace = TraceRecord(
            id="",
            trace_hash=trace_hash,
            actions=actions,
            discovered_capabilities=[],
            governance_score=score['score'],
            uploaded_by=os.environ.get('USER', 'cli'),
            status="pending"
        )
        trace_id = registry.add_trace(trace)
        click.echo(f"\n✅ Trace uploaded as {trace_id}")


@cli.command()
@click.argument('name')
@click.argument('severity')
@click.argument('actions_json')
def register(name, severity, actions_json):
    """Register a new capability manually."""
    try:
        actions = json.loads(actions_json)
    except json.JSONDecodeError:
        click.echo("❌ Invalid JSON for actions.")
        return
    
    cap = Capability(
        id="",
        name=name,
        description=f"Registered via CLI on {datetime.now().strftime('%Y-%m-%d')}",
        severity=severity,
        required_actions=actions,
        witness_hash="pending",
        counterfactual_verified=False,
        governance_decision="DENY",
        discovered_by="DecisionAssure CLI"
    )
    cap_id = registry.register_capability(cap)
    click.echo(f"✅ Registered {cap_id}: {name}")


@cli.command()
def list():
    """List all registered capabilities."""
    caps = registry.search_capabilities()
    if not caps:
        click.echo("No capabilities registered.")
        return
    
    click.echo(f"\n📋 Registered Capabilities ({len(caps)}):")
    for cap in caps:
        click.echo(f"  {cap.id}  {cap.severity:8}  {cap.name}")


@cli.command()
@click.argument('cap_id')
def show(cap_id):
    """Show details of a specific capability."""
    cap = registry.get_capability(cap_id)
    if not cap:
        click.echo(f"❌ Capability {cap_id} not found.")
        return
    
    click.echo(f"\n🔐 Capability: {cap.name}")
    click.echo(f"  ID:         {cap.id}")
    click.echo(f"  Severity:   {cap.severity}")
    click.echo(f"  Description: {cap.description}")
    click.echo("  Required Actions:")
    for action in cap.required_actions:
        click.echo(f"    {action['agent']} → {action['action']}")
    click.echo(f"  Counterfactual Verified: {cap.counterfactual_verified}")
    click.echo(f"  Witness Hash: {cap.witness_hash[:32]}...")
    click.echo(f"  Governance Decision: {cap.governance_decision}")
    click.echo(f"  Confidence: {cap.confidence:.2%}")
    click.echo(f"  First Seen: {cap.first_seen.strftime('%Y-%m-%d')}")


@cli.command()
@click.argument('actions_json')
def witness(actions_json):
    """Generate a witness for a set of actions."""
    try:
        actions = json.loads(actions_json)
    except json.JSONDecodeError:
        click.echo("❌ Invalid JSON for actions.")
        return
    
    witness = witness_engine.generate(actions)
    click.echo(json.dumps(witness.model_dump(mode='json'), indent=2))


@cli.command()
def stats():
    """Show registry statistics."""
    stats = registry.get_stats()
    click.echo("\n📊 Registry Statistics")
    click.echo(f"  Total Capabilities: {stats.total_capabilities}")
    click.echo(f"  Critical:           {stats.critical_severity}")
    click.echo(f"  High:               {stats.high_severity}")
    click.echo(f"  Medium:             {stats.medium_severity}")
    click.echo(f"  Low:                {stats.low_severity}")
    click.echo(f"  Total Traces:       {stats.total_traces}")
    click.echo(f"  Pending Review:     {stats.unknown_capabilities}")


if __name__ == '__main__':
    cli()