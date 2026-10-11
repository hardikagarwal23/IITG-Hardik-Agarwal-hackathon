import os, json
import pandas as pd
from src.schemas import ExposureAssessment, NLPEventExtraction

class ExposureMapper:
    def __init__(self, registry_path: str = "data/entity_registry.json"):
        self.registry = {
            "entities": {
                "NVIDIA Corp": {"positions": ["BOND-002", "LOAN-007"]},
                "Boeing Co": {"positions": ["LOAN-001", "BOND-008"]},
                "Apple Inc": {"positions": ["BOND-003"]},
                "JPMorgan Chase": {"positions": ["SWAP-001", "SWAP-002"]},
            },
            "sectors": {
                "Semiconductors": ["BOND-002", "LOAN-007"],
                "Aerospace & Defense": ["LOAN-001", "BOND-008"],
                "Financials": ["SWAP-001", "SWAP-002"],
            }
        }

    def assess_exposure(self, nlp_data: NLPEventExtraction, portfolio_df: pd.DataFrame) -> ExposureAssessment:
        if nlp_data.extracted_entity and nlp_data.extracted_entity in self.registry["entities"]:
            matched = self.registry["entities"][nlp_data.extracted_entity]["positions"]
            return ExposureAssessment(mapping_status="DIRECT", matched_position_ids=matched, mapping_rationale=f"Direct match for '{nlp_data.extracted_entity}'.", applicable_scenario_id="DIRECT_ISSUER_SHOCK")
        if nlp_data.extracted_sector and nlp_data.extracted_sector in self.registry["sectors"]:
            matched = self.registry["sectors"][nlp_data.extracted_sector]
            return ExposureAssessment(mapping_status="SECTOR", matched_position_ids=matched, mapping_rationale=f"Sector match for '{nlp_data.extracted_sector}'.", applicable_scenario_id="SECTOR_SUPPLY_SHOCK")
        if nlp_data.event_category == "Macroeconomic":
            return ExposureAssessment(mapping_status="MACRO", matched_position_ids=portfolio_df["position_id"].tolist(), mapping_rationale="Macro shift impacting active book.", applicable_scenario_id="MACRO_RATE_SHOCK")
        return ExposureAssessment(mapping_status="NO_MAPPED_EXPOSURE", matched_position_ids=[], mapping_rationale="No direct/indirect exposure.", applicable_scenario_id="NO_SHOCK")