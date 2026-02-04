from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime
from typing import List

from app.database import get_db
from app.core.security import verify_token
from app.services.ml_service import ml_analyzer
from app.schemas.analysis import AnalyzeRequest, AnalysisResponse

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.post("/analyze", response_model=AnalysisResponse)
@limiter.limit("20/minute")
async def analyze_stock(
    request: Request,
    request_data: AnalyzeRequest,
    current_user: dict = Depends(verify_token)
):
    """Perform AI analysis on a stock"""
    try:
        analysis = ml_analyzer.analyze_stock(request_data.symbol.upper())
        return AnalysisResponse(**analysis)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing stock: {str(e)}"
        )

@router.get("/recent")
@limiter.limit("30/minute")
async def get_recent_analyses(
    request: Request,
    current_user: dict = Depends(verify_token)
):
    """Get recent stock analyses"""
    # Indian market leaders
    recent_symbols = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "SBIN.NS"]
    recent_analyses = []
    
    for symbol in recent_symbols:
        try:
            analysis = ml_analyzer.analyze_stock(symbol)
            recent_analyses.append({
                "symbol": symbol,
                "recommendation": analysis['recommendation'],
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
        except:
            continue
    
    return recent_analyses[:5]
