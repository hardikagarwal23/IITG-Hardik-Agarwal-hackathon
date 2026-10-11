import pandas as pd
from typing import List
from src.schemas import ExposureAssessment, PositionStressDetail, ScenarioSpecification, StressTestResult

class StressEngine:
    def run_stress_test(self, portfolio_df: pd.DataFrame, assessment: ExposureAssessment, severity_score: int) -> StressTestResult:
        scenario = self._build_scenario(assessment.applicable_scenario_id, severity_score)
        position_details: List[PositionStressDetail] = []
        tot_loss = ecl_loss = bond_loss = swap_loss = 0.0
        target_ids = set(assessment.matched_position_ids)

        for _, row in portfolio_df.iterrows():
            pos_id, asset_type, carrying_val = row["position_id"], row["asset_type"], float(row["carrying_value_usd"])
            if assessment.mapping_status != "NO_MAPPED_EXPOSURE" and pos_id in target_ids:
                loss, detail = self._calculate_position_loss(row, scenario)
            else:
                loss, detail = 0.0, "No mapped shock applied."
            
            tot_loss += loss
            if asset_type == "LOAN": ecl_loss += loss
            elif asset_type == "BOND": bond_loss += loss
            elif asset_type == "SWAP": swap_loss += loss

            loss_pct = (loss / carrying_val * 100) if carrying_val else 0.0
            position_details.append(PositionStressDetail(position_id=pos_id, asset_type=asset_type, counterparty_name=row.get("counterparty_name", "Unknown"), sector=row.get("sector", "General"), carrying_value_usd=carrying_val, stress_loss_usd=loss, loss_pct=loss_pct, calculation_detail=detail))
        
        return StressTestResult(scenario_applied=scenario, total_loss_usd=tot_loss, incremental_ecl_usd=ecl_loss, bond_loss_usd=bond_loss, swap_loss_usd=swap_loss, positions=position_details)

    def _calculate_position_loss(self, row: pd.Series, scenario: ScenarioSpecification) -> tuple[float, str]:
        asset_type, val, shocks = row["asset_type"], float(row["carrying_value_usd"]), scenario.shocks
        if asset_type == "LOAN":
            ead, base_pd, base_lgd = float(row.get("ead_usd", val)), float(row.get("base_pd", 0.02)), float(row.get("base_lgd", 0.40))
            stressed_pd, stressed_lgd = min(1.0, base_pd * shocks.get("pd_multiplier", 1.0)), min(1.0, base_lgd + shocks.get("lgd_additive", 0.0))
            return ead * (stressed_pd * stressed_lgd - base_pd * base_lgd), f"ΔECL: PD {base_pd:.2%}->{stressed_pd:.2%}, LGD {base_lgd:.2%}->{stressed_lgd:.2%}"
        elif asset_type == "BOND":
            dr, ds = shocks.get("rate_shock_decimal", 0.0), shocks.get("spread_shock_decimal", 0.0)
            return val * (float(row.get("rate_duration", 5.0)) * dr + float(row.get("spread_duration", 4.5)) * ds), f"Duration shock: Δr={dr*10000:.0f}bps, Δs={ds*10000:.0f}bps"
        elif asset_type == "SWAP":
            dr_bps, dv01 = shocks.get("rate_shock_decimal", 0.0) * 10000, float(row.get("signed_dv01", 100.0))
            return -1.0 * (dv01 * dr_bps), f"Swap mark: DV01={dv01}, Δr={dr_bps:.0f}bps"
        return 0.0, "Unrecognized asset type."

    def _build_scenario(self, scenario_id: str, severity: int) -> ScenarioSpecification:
        sev_factor = severity / 10.0
        if scenario_id == "DIRECT_ISSUER_SHOCK": return ScenarioSpecification(scenario_id=scenario_id, name="Direct Entity Stress", description="Immediate credit deterioration.", shocks={"pd_multiplier": 1.0 + 2.5 * sev_factor, "lgd_additive": 0.15 * sev_factor, "spread_shock_decimal": 0.02 * sev_factor})
        if scenario_id == "SECTOR_SUPPLY_SHOCK": return ScenarioSpecification(scenario_id=scenario_id, name="Sectoral Transmission Stress", description="Industry-wide disruption.", shocks={"pd_multiplier": 1.0 + 1.2 * sev_factor, "lgd_additive": 0.05 * sev_factor, "spread_shock_decimal": 0.008 * sev_factor})
        if scenario_id == "MACRO_RATE_SHOCK": return ScenarioSpecification(scenario_id=scenario_id, name="Systemic Rate Shift", description="Macroeconomic adjustment.", shocks={"rate_shock_decimal": 0.0075 * sev_factor, "spread_shock_decimal": 0.0050 * sev_factor, "pd_multiplier": 1.0 + 0.3 * sev_factor})
        return ScenarioSpecification(scenario_id="NO_SHOCK", name="Neutral Scenario", description="No direct or systematic shock applied.", shocks={})