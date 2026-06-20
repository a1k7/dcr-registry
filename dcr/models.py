from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import hashlib
import json

class Capability(BaseModel):
    id: str
    name: str
    description: str
    severity: str
    required_actions: List[Dict[str, str]]
    optional_actions: List[Dict[str, str]] = []
    witness_hash: str
    counterfactual_verified: bool = False
    governance_decision: str = "DENY"
    known_variants: int = 1
    first_seen: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    discovered_by: str = "DecisionAssure"
    affected_frameworks: List[str] = []
    references: List[str] = []
    confidence: float = 0.0
    severity_score: int = 0
    occurrence_count: int = 1
    affected_traces: List[str] = []
    status: str = "approved"

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(mode='json')

class DCRRecord(BaseModel):
    id: str
    name: str
    description: str
    severity: str
    required_actions: List[Dict[str, str]]
    witness_hash: str
    counterfactual_verified: bool
    governance_decision: str
    confidence: float
    occurrence_count: int
    first_seen: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    affected_traces: List[str] = []
    discovered_by: str = "DecisionAssure"
    affected_frameworks: List[str] = []
    references: List[str] = []
    status: str = "pending"
    

    # ===== NEW FIELDS =====
    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    historical_replay_count: int = 0
    previously_missed_incidents: int = 0
    coverage_gain: float = 0.0

class CapabilityWitness(BaseModel):
    capability_id: str
    witness_hash: str
    required_actions: List[Dict[str, str]]
    counterfactual_results: List[Dict[str, Any]]
    created_at: datetime = Field(default_factory=datetime.now)
    verified: bool = False
    verifier_signature: Optional[str] = None

class TraceRecord(BaseModel):
    id: str
    trace_hash: str
    actions: List[Dict[str, Any]]
    discovered_capabilities: List[str]
    governance_score: float
    timestamp: datetime = Field(default_factory=datetime.now)
    uploaded_by: str = "anonymous"
    status: str = "pending"

class RegistryStats(BaseModel):
    total_capabilities: int
    critical_severity: int
    high_severity: int
    medium_severity: int
    low_severity: int
    total_traces: int
    unknown_capabilities: int
    last_updated: datetime = Field(default_factory=datetime.now)
    gkai: float = 0.0
    coverage_timeline: List[Dict[str, Any]] = Field(default_factory=list)