from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import datetime

from src.pipeline import RiskLensPipeline
from src.schemas import RiskSignal, UnifiedAnalysisResult

app = FastAPI(
    title="Signal2Stress Risk Engine API",
    description="Unified API for financial sentiment extraction and wholesale portfolio stress testing.",
    version="1.0.0",
)

pipeline = RiskLensPipeline()

class AnalyzeRequest(BaseModel):
    text: str = Field(..., description="Raw text headline or news article.")
    source: str = Field(default="API Client", description="Identifier for data provenance.")

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()}

@app.post("/api/v1/analyze", response_model=UnifiedAnalysisResult)
def analyze_headline(req: AnalyzeRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text field cannot be empty.")
    try:
        res = pipeline.process_text(req.text, source=req.source)
        return res["export_payload"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/risk-feed", response_model=List[UnifiedAnalysisResult])
def get_risk_feed(limit: int = Query(default=10, ge=1, le=50)):
    records = pipeline.storage.get_recent_runs(limit=limit)
    return records