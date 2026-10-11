import os
import pandas as pd
from typing import List
from src.deduplication import DeduplicationIndex
from src.pipeline import RiskLensPipeline

class FeedProcessor:
    def __init__(self, sample_news_path: str = "data/sample_news.csv"):
        self.sample_news_path = sample_news_path
        self.dedup = DeduplicationIndex()
        self.pipeline = RiskLensPipeline()

    def get_feed_items(self) -> pd.DataFrame:
        if os.path.exists(self.sample_news_path):
            df = pd.read_csv(self.sample_news_path)
            if "headline" in df.columns:
                return df
        return pd.DataFrame([
            {"headline": "Boeing faces credit review following supply chain disruptions.", "source": "Reuters"},
            {"headline": "Semiconductor shortages trigger broad warnings across hardware sector.", "source": "Bloomberg"},
            {"headline": "Federal Reserve maintains tight policy stance amid persistent wage growth.", "source": "FT"},
        ])

    def process_pending_feed(self) -> List[dict]:
        df = self.get_feed_items()
        results = []
        for _, row in df.iterrows():
            text = row.get("headline", "")
            source = row.get("source", "Feed Replay")
            
            # Exact Deduplication Check
            if not self.dedup.is_duplicate(text):
                self.dedup.register(text)
                res = self.pipeline.process_text(text, source=source)
                results.append(res)
        return results