# DecisionAssure Capability Registry (DCR)

**The CVE Database for AI Agents.**

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