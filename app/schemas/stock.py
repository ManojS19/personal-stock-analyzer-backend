from pydantic import BaseModel
from typing import Optional, Dict, List

class StockInfo(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    changeAmount: float
    recommendation: Optional[str] = None
    confidence: Optional[float] = None

class StockDetail(StockInfo):
    previousClose: float
    volume: int
    marketCap: float
    peRatio: float
    eps: float
    dividendYield: float
    fundamental: Optional[Dict] = None
    technical: Optional[Dict] = None
    currentSituation: Optional[str] = None
    reason: Optional[str] = None

class ChartData(BaseModel):
    labels: List[str]
    values: List[float]
