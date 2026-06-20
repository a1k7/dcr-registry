import pytest
from dcr.witness import WitnessEngine
from dcr.models import CapabilityWitness

def test_witness_generation():
    engine = WitnessEngine()
    actions = [
        {"agent": "alice", "action": "read_db"},
        {"agent": "bob", "action": "export"}
    ]
    witness = engine.generate(actions)
    assert witness.witness_hash is not None
    assert len(witness.required_actions) == 2
    assert len(witness.counterfactual_results) > 0

def test_witness_counterfactual():
    engine = WitnessEngine()
    actions = [
        {"agent": "a", "action": "x"},
        {"agent": "b", "action": "y"}
    ]
    witness = engine.generate(actions)
    cf = witness.counterfactual_results
    # Removing either agent should break the capability
    assert cf[0]["capability_still_exists"] is False
    assert cf[1]["capability_still_exists"] is False

def test_witness_verify():
    engine = WitnessEngine()
    actions = [
        {"agent": "alice", "action": "read_db"},
        {"agent": "bob", "action": "export"}
    ]
    witness = engine.generate(actions)
    # Manually set capability_id for testing
    witness.capability_id = "test-001"
    is_valid = engine.verify(witness)
    assert is_valid is True
    
    # Tamper with witness hash
    witness.witness_hash = "tampered"
    is_valid = engine.verify(witness)
    assert is_valid is False