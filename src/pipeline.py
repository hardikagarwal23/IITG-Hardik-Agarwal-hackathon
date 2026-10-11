import os, uuid
import pandas as pd
from src.exposure_mapper import ExposureMapper
from src.risk_engine import RiskEngine
from src.schemas import RiskSignal, UnifiedAnalysisResult
from src.storage import RunStorage
from src.stress_engine import StressEngine

class RiskLensPipeline:
    def __init__(self):
        self.risk_engine = RiskEngine()
        self.exposure_mapper = ExposureMapper()
        self.stress_engine = StressEngine()
        self.storage = RunStorage()
        self.portfolio_df = pd.DataFrame([
            {"position_id": "LOAN-001", "asset_type": "LOAN", "counterparty_name": "Boeing Co", "sector": "Aerospace & Defense", "carrying_value_usd": 15000000, "ead_usd": 15000000, "base_pd": 0.02, "base_lgd": 0.40},
            {"position_id": "BOND-002", "asset_type": "BOND", "counterparty_name": "NVIDIA Corp", "sector": "Semiconductors", "carrying_value_usd": 10000000, "rate_duration": 4.5, "spread_duration": 4.2},
            {"position_id": "BOND-003", "asset_type": "BOND", "counterparty_name": "Apple Inc", "sector": "Technology Hardware", "carrying_value_usd": 12000000, "rate_duration": 5.1, "spread_duration": 4.8},
            {"position_id": "SWAP-001", "asset_type": "SWAP", "counterparty_name": "JPMorgan Chase", "sector": "Financials", "carrying_value_usd": 1000000, "signed_dv01": 250.0},
        ])

    def get_demo_cases(self) -> pd.DataFrame:
        return pd.DataFrame([
            {"headline": "Boeing faces renewed regulatory scrutiny following production halts.", "expected_tier": "DIRECT", "focus_entity": "Boeing Co"},
            {"headline": "Semiconductor export bans tighten across East Asian manufacturing corridors.", "expected_tier": "SECTOR", "focus_entity": "Semiconductors"},
            {"headline": "Federal Reserve announces unexpected 50 bps policy rate increase.", "expected_tier": "MACRO", "focus_entity": "Systemic"},
        ])

    def process_text(self, text: str, source: str = "Input Stream") -> dict:
        nlp_out = self.risk_engine.extract_event_and_entities(text, source)
        assessment = self.exposure_mapper.assess_exposure(nlp_out, self.portfolio_df)
        is_trigger = nlp_out.severity_score >= 6 and assessment.mapping_status != "NO_MAPPED_EXPOSURE"
        
        signal = RiskSignal(
            event_id=nlp_out.event_id, headline=text, source=source, sentiment_score=nlp_out.sentiment_score, 
            event_category=nlp_out.event_category, event_subtype=nlp_out.event_subtype, severity_score=nlp_out.severity_score, 
            evidence_quote=nlp_out.evidence_quote, extracted_entity=nlp_out.extracted_entity, 
            extracted_sector=nlp_out.extracted_sector, model_used=nlp_out.model_used, is_stress_trigger=is_trigger
        )
        
        stress_result = self.stress_engine.run_stress_test(portfolio_df=self.portfolio_df, assessment=assessment, severity_score=nlp_out.severity_score)
        payload = UnifiedAnalysisResult(signal=signal, assessment=assessment, stress_result=stress_result)
        self.storage.record_run(payload)
        
        return {"signal": signal, "assessment": assessment, "stress_result": stress_result, "export_payload": payload}