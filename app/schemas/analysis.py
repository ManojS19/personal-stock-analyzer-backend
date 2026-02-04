from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    symbol: str

class AnalysisResponse(BaseModel):
    symbol: str
    recommendation: str
    confidence: float
    fundamentalScore: float
    technicalScore: float
    insights: str
    riskLevel: str
    rsi: float
    macd: float
    movingAverage: str
