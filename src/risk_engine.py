import re
import uuid
from typing import List, Optional, Tuple
from src.schemas import NLPEventExtraction

class RiskEngine:
    def __init__(self, use_gpu: bool = False):
        self.lexicon_positive = {"surge", "gain", "profit", "outperform", "growth", "boost", "upgrade", "recovery", "soared", "beat"}
        self.lexicon_negative = {"default", "downgrade", "loss", "investigation", "hike", "cut", "sanction", "slump", "crisis", "outage", "ban", "recession", "breach", "fine", "fraud", "bankruptcy"}

    def analyze_sentiment(self, text: str) -> Tuple[float, str]:
        tokens = re.findall(r"\b[a-z]+\b", text.lower())
        pos_hits = sum(1 for t in tokens if t in self.lexicon_positive)
        neg_hits = sum(1 for t in tokens if t in self.lexicon_negative)
        total = pos_hits + neg_hits
        return (pos_hits - neg_hits) / total if total > 0 else 0.0, "Lexicon Model"

    def _extract_evidence(self, text: str) -> str:
        sentences = [s.strip() for s in re.split(r"[.!?\n]", text) if s.strip()]
        for s in sentences:
            if any(w in s.lower() for w in ["default", "rate", "hike", "probe", "sanction", "cut", "ban", "loss", "guidance"]): return s
        return sentences[0] if sentences else text[:120]

    def _match(self, text: str, keywords: List[str]) -> bool:
        return bool(re.search(r'\b(?:' + '|'.join(map(re.escape, keywords)) + r')\b', text))

    def _classify(self, text: str) -> Tuple[str, str, int]:
        lowered = text.lower()
        if self._match(lowered, ["missed payment", "default", "bankruptcy"]): return "Credit Event", "borrower_default", 9
        if self._match(lowered, ["rate hike", "interest rate", "tightening"]): return "Macroeconomic", "policy_rates_up", 8
        if self._match(lowered, ["rate cut", "monetary easing"]): return "Macroeconomic", "policy_rates_down", 6
        if self._match(lowered, ["inflation", "recession"]): return "Macroeconomic", "macro_headwind", 7
        if self._match(lowered, ["sanction", "export control"]): return "Geopolitical", "trade_sanctions", 8
        if self._match(lowered, ["war", "missile", "military"]): return "Geopolitical", "military_escalation", 9
        if self._match(lowered, ["probe", "investigation", "antitrust"]): return "Regulatory", "compliance_enforcement", 6
        if self._match(lowered, ["cyberattack", "outage"]): return "Cyber/Operational Risk", "operational_disruption", 7
        if self._match(lowered, ["quarterly revenue", "guidance"]): return "Earnings/Financial Results", "financial_filing", 5
        return "Other", "general_market_news", 3

    def _entities(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        lowered = text.lower()
        if self._match(lowered, ["nvidia", "nvda"]): return "NVIDIA Corp", "Semiconductors"
        if self._match(lowered, ["boeing", "ba"]): return "Boeing Co", "Aerospace & Defense"
        if self._match(lowered, ["apple", "aapl"]): return "Apple Inc", "Technology Hardware"
        if self._match(lowered, ["jpmorgan", "jpm", "chase"]): return "JPMorgan Chase", "Financials"
        if self._match(lowered, ["semiconductor", "chipmaker"]): return None, "Semiconductors"
        return None, None

    def extract_event_and_entities(self, text: str, source: str = "API") -> NLPEventExtraction:
        s_score, m_used = self.analyze_sentiment(text)
        cat, sub, sev = self._classify(text)
        ent, sec = self._entities(text)
        return NLPEventExtraction(
            event_id=str(uuid.uuid4())[:8], headline=text, source=source, sentiment_score=s_score, 
            event_category=cat, event_subtype=sub, severity_score=sev, evidence_quote=self._extract_evidence(text), 
            extracted_entity=ent, extracted_sector=sec, model_used=m_used
        )