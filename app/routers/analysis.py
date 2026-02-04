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
    return recent_analyses[:5]

@router.post("/portfolio")
@limiter.limit("10/minute")
async def analyze_portfolio(
    request: Request,
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Analyze entire portfolio with AI"""
    try:
        from app.models.portfolio import Portfolio
        
        user_id = int(current_user['user_id'])
        portfolios = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
        
        if not portfolios:
            return {
                "overallSentiment": "Neutral",
                "projectedChange": "Stable",
                "riskProfile": {"Low": 0, "Moderate": 0, "High": 0},
                "opportunities": [],
                "details": []
            }
            
        details = []
        sentiment_score = 0
        risk_counts = {"Low": 0, "Moderate": 0, "High": 0}
        opportunities = []
        
        for item in portfolios:
            try:
                analysis = ml_analyzer.analyze_stock(item.symbol)
                analysis['shares'] = item.shares
                details.append(analysis)
                
                # Sentiment scoring
                if analysis['recommendation'] == 'BUY':
                    sentiment_score += 1
                elif analysis['recommendation'] == 'SELL':
                    sentiment_score -= 1
                    
                # Risk profiling
                risk = analysis.get('riskLevel', 'Moderate Risk')
                if 'Low' in risk: risk_counts['Low'] += 1
                elif 'High' in risk: risk_counts['High'] += 1
                else: risk_counts['Moderate'] += 1
                
                # Identify opportunities (High confidence BUYs)
                if analysis['recommendation'] == 'BUY' and analysis['confidence'] > 75:
                    opportunities.append(analysis)
                    
            except Exception as e:
                print(f"Failed to analyze {item.symbol}: {e}")
                continue
                
        # Determine overall sentiment
        if sentiment_score > len(portfolios) / 3:
            overall_sentiment = "Bullish"
            projected_change = "Positive"
        elif sentiment_score < -len(portfolios) / 3:
            overall_sentiment = "Bearish"
            projected_change = "Negative"
        else:
            overall_sentiment = "Neutral"
            projected_change = "Stable"
            
        return {
            "overallSentiment": overall_sentiment,
            "projectedChange": projected_change,
            "riskProfile": risk_counts,
            "opportunities": opportunities,
            "details": details
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Portfolio analysis failed: {str(e)}"
        )
