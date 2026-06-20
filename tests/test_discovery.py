import pytest
from dcr.discovery import CapabilityDiscovery

def test_discovery_basic():
    discovery = CapabilityDiscovery(min_samples=2, eps=0.5)
    traces = [
        [{"agent": "a", "action": "read"}, {"agent": "b", "action": "write"}],
        [{"agent": "a", "action": "read"}, {"agent": "b", "action": "write"}],
        [{"agent": "c", "action": "delete"}],
        [{"agent": "a", "action": "read"}]
    ]
    results = discovery.discover(traces)
    # Should find at least one cluster (the repeated pattern)
    assert len(results) > 0
    # Check that required actions are extracted
    req_actions = results[0]["required_actions"]
    assert len(req_actions) >= 2

def test_discovery_min_samples():
    discovery = CapabilityDiscovery(min_samples=3, eps=0.5)
    traces = [
        [{"agent": "a", "action": "read"}],
        [{"agent": "a", "action": "read"}]
    ]
    results = discovery.discover(traces)
    assert len(results) == 0

def test_discovery_signature_extraction():
    discovery = CapabilityDiscovery()
    traces = [
        [{"agent": "alice", "action": "read"}, {"agent": "bob", "action": "write"}],
        [{"agent": "alice", "action": "read"}]
    ]
    sigs = discovery._extract_signatures(traces)
    assert len(sigs) == 2
    assert "alice:read" in sigs[0]
    assert "bob:write" in sigs[0]