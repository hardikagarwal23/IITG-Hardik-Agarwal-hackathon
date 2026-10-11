from typing import List
from src.schemas import UnifiedAnalysisResult

class RunStorage:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RunStorage, cls).__new__(cls)
            cls._instance.history: List[UnifiedAnalysisResult] = []
        return cls._instance

    def record_run(self, result: UnifiedAnalysisResult):
        self.history.insert(0, result)
        if len(self.history) > 100:
            self.history = self.history[:100]

    def get_recent_runs(self, limit: int = 10) -> List[UnifiedAnalysisResult]:
        return self.history[:limit]