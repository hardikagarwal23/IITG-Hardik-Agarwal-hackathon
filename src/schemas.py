from pydantic import BaseModel
from typing import List, Optional, Dict

class NLPEventExtraction(BaseModel):
    event_id: str
    headline: str
    source: str
    sentiment_score: float
    event_category: str
    event_subtype: str
    severity_score: int
    evidence_quote: str
    extracted_entity: Optional[str] = None
    extracted_sector: Optional[str] = None
    model_used: str

class ExposureAssessment(BaseModel):
    mapping_status: str
    matched_position_ids: List[str]
    mapping_rationale: str
    applicable_scenario_id: str

class PositionStressDetail(BaseModel):
    position_id: str
    asset_type: str
    counterparty_name: str
    sector: str
    carrying_value_usd: float
    stress_loss_usd: float
    loss_pct: float
    calculation_detail: str

class ScenarioSpecification(BaseModel):
    scenario_id: str
    name: str
    description: str
    shocks: Dict[str, float]

class StressTestResult(BaseModel):
    scenario_applied: ScenarioSpecification
    total_loss_usd: float
    incremental_ecl_usd: float
    bond_loss_usd: float
    swap_loss_usd: float
    positions: List[PositionStressDetail]

class RiskSignal(BaseModel):
    event_id: str
    headline: str
    source: str
    sentiment_score: float
    event_category: str
    event_subtype: str
    severity_score: int
    evidence_quote: str
    extracted_entity: Optional[str] = None
    extracted_sector: Optional[str] = None
    model_used: str
    is_stress_trigger: bool

class UnifiedAnalysisResult(BaseModel):
    signal: RiskSignal
    assessment: ExposureAssessment
    stress_result: StressTestResult