# DecisionAssure Capability Registry (DCR)

**The CVE Database for AI Agents.**

# DecisionAssure DCR

Discover unknown AI agent capabilities before they become incidents.

DecisionAssure DCR is an open-source governance system that discovers emergent capabilities from agent traces, verifies them through counterfactual analysis, replays historical execution logs, and measures governance coverage over time.

## Why?

Most governance systems answer:

"Did the agent violate a known policy?"

DecisionAssure answers:

"What capabilities exist that governance doesn't know about yet?"

## Core Workflow

Discover
↓
Verify
↓
Review
↓
Learn
↓
Replay
↓
Govern

## Features

- Capability Discovery
- Counterfactual Verification
- Human Review Queue
- Governance Learning
- Historical Replay
- Governance Coverage Metrics
- Capability Registry
- Governance Gap Assessment

## Example Discoveries

- Credential Exfiltration
- Unauthorized Model Export
- Cross-Agent Leakage
- Evidence Suppression
- Shadow Planning

## Governance Coverage

Governance Coverage =
Governed Capabilities ÷ Observed Capabilities × 100

This metric provides a measurable view of governance maturity and learning over time.

## Status

Experimental open-source research prototype.

A public registry for emergent AI agent capabilities. Every discovered capability gets a DCR ID, severity rating, witness hash, and governance guidance.

## Quick Start

```bash
git clone https://github.com/a1k7/dcr-registry.git
cd dcr-registry
pip install -r requirements.txt
python run.py

Open http://localhost:5000

What DCR Does

Discovers emergent capabilities from agent traces
Verifies capabilities with counterfactual replay
Tracks capabilities with unique DCR IDs
Provides governance guidance for each capability
Architecture

text
Traces → Discovery → Witness → Registry → Web Interface
License

MIT

Contact

Akhilesh Warik — warikakhilesh319@gmail.com
