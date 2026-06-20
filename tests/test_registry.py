import pytest
import json
import tempfile
import os
from datetime import datetime
from dcr.registry import CapabilityRegistry
from dcr.models import Capability

@pytest.fixture
def temp_registry():
    """Create a temporary registry for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry = CapabilityRegistry(db_path=tmpdir)
        yield registry

def test_register_capability(temp_registry):
    cap = Capability(
        id="",
        name="Test Capability",
        description="A test capability",
        severity="high",
        required_actions=[{"agent": "alice", "action": "read_db"}],
        witness_hash="abc123",
        counterfactual_verified=False,
        governance_decision="DENY"
    )
    cap_id = temp_registry.register_capability(cap)
    assert cap_id.startswith("DCR-")
    assert len(temp_registry.capabilities) == 1
    assert temp_registry.get_capability(cap_id) is not None

def test_search_capabilities(temp_registry):
    cap1 = Capability(
        id="",
        name="Credential Exfiltration",
        description="Gather and export credentials",
        severity="critical",
        required_actions=[{"agent": "alice", "action": "read_creds"}],
        witness_hash="def456"
    )
    cap2 = Capability(
        id="",
        name="Model Exfiltration",
        description="Export AI models",
        severity="high",
        required_actions=[{"agent": "bob", "action": "export_model"}],
        witness_hash="ghi789"
    )
    temp_registry.register_capability(cap1)
    temp_registry.register_capability(cap2)
    
    results = temp_registry.search_capabilities(query="credential")
    assert len(results) == 1
    assert results[0].name == "Credential Exfiltration"
    
    results = temp_registry.search_capabilities(severity="high")
    assert len(results) == 1
    assert results[0].name == "Model Exfiltration"

def test_stats(temp_registry):
    cap1 = Capability(
        id="",
        name="Cap1",
        description="desc",
        severity="critical",
        required_actions=[],
        witness_hash="a"
    )
    cap2 = Capability(
        id="",
        name="Cap2",
        description="desc",
        severity="high",
        required_actions=[],
        witness_hash="b"
    )
    temp_registry.register_capability(cap1)
    temp_registry.register_capability(cap2)
    stats = temp_registry.get_stats()
    assert stats.total_capabilities == 2
    assert stats.critical_severity == 1
    assert stats.high_severity == 1