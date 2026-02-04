from fastapi import APIRouter, Depends, HTTPException, status, Request
import yfinance as yf
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import verify_token
from app.services.stock_data import StockDataService
from app.services.ml_service import ml_analyzer

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/popular")
@limiter.limit("30/minute")
async def get_popular_stocks(request: Request):
    """Get popular stocks with recommendations"""
    try:
        stocks = StockDataService.get_popular_stocks()
        
        # Add ML recommendations
        for stock in stocks:
            try:
                analysis = ml_analyzer.analyze_stock(stock['symbol'])
                stock['recommendation'] = analysis['recommendation']
                stock['confidence'] = analysis['confidence']
            except Exception as e:
                print(f"Error analyzing {stock['symbol']}: {e}")
                continue
        
        return stocks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching stocks: {str(e)}"
        )

@router.get("/{symbol}")
@limiter.limit("30/minute")
async def get_stock(symbol: str, request: Request):
    """Get detailed stock information"""
    try:
        stock_info = StockDataService.get_stock_info(symbol.upper())
        
        # Get Fundamental Data (Robustly)
        try:
            fundamental = StockDataService.get_fundamental_data(symbol.upper())
            stock_info['fundamental'] = fundamental
        except Exception as e:
            print(f"Error fetching fundamentals: {e}")
            stock_info['fundamental'] = {}

        # Get ML analysis
        try:
            analysis = ml_analyzer.analyze_stock(symbol.upper())
            stock_info['recommendation'] = analysis['recommendation']
            stock_info['confidence'] = analysis['confidence']
            stock_info['reason'] = analysis['insights']
            
            # Get technical data
            stock_info['technical'] = {
                'rsi': analysis['rsi'],
                'macd': analysis['macd'],
                'movingAverage': analysis['movingAverage'],
            }
        except Exception as e:
            print(f"Error in ML analysis for {symbol}: {e}")
            stock_info['recommendation'] = 'HOLD'
            stock_info['confidence'] = 50
            stock_info['reason'] = "Analysis temporarily unavailable. Showing latest market data."
            stock_info['technical'] = {
                'rsi': 'N/A',
                'macd': 'N/A',
                'movingAverage': 'N/A',
            }
            
        # Get current situation (Always try to generate)
        try:
            currency = stock_info.get('currency', '$')
            situation = f"Current Price: {currency}{stock_info['price']:.2f}. "
            if stock_info.get('fundamental'):
                situation += f"Market Cap: {stock_info['fundamental'].get('marketCap', 'N/A')}. "
                situation += f"P/E Ratio: {stock_info['fundamental'].get('peRatio', 'N/A')}. "
            
            ticker = yf.Ticker(symbol.upper())
            news = ticker.news[:5] if hasattr(ticker, 'news') else []
            if news:
                situation += f"Recent news: {news[0].get('title', '')[:100]}..."
            stock_info['news'] = [
                {
                    "title": item.get("title", ""),
                    "publisher": item.get("publisher", ""),
                    "link": item.get("link", ""),
                    "providerPublishTime": item.get("providerPublishTime", None),
                }
                for item in news
            ]
            
            stock_info['currentSituation'] = situation
        except Exception as e:
            print(f"Error generating situation: {e}")
            stock_info['currentSituation'] = "Market data is currently loading. Please check back in a moment."
            stock_info['news'] = []
        
        return stock_info
        
        return stock_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock not found: {str(e)}"
        )

@router.get("/{symbol}/chart")
@limiter.limit("30/minute")
async def get_stock_chart(symbol: str, request: Request, period: str = "1mo"):
    """Get stock chart data"""
    try:
        chart_data = StockDataService.get_historical_data(symbol.upper(), period)
        return chart_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching chart data: {str(e)}"
        )
