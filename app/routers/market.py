from fastapi import APIRouter, Depends, Request
import yfinance as yf
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.services.stock_data import StockDataService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/overview")
@limiter.limit("30/minute")
async def get_market_overview(request: Request):
    """Get market overview statistics"""
    try:
        stocks = StockDataService.get_popular_stocks()
        
        total_stocks = len(stocks)
        positive_stocks = sum(1 for s in stocks if s.get('change', 0) >= 0)
        negative_stocks = total_stocks - positive_stocks
        
        # Add Indices
        indices = []
        for index_sym, name in [("^NSEI", "NIFTY 50"), ("^BSESN", "SENSEX")]:
            try:
                ticker = yf.Ticker(index_sym)
                hist = ticker.history(period="1d")
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    prev = ticker.info.get('previousClose', current)
                    change = ((current - prev) / prev * 100) if prev > 0 else 0
                    indices.append({
                        "name": name,
                        "value": float(current),
                        "change": float(change),
                        "symbol": index_sym
                    })
            except:
                continue
        
        return {
            "totalStocks": total_stocks,
            "positiveStocks": positive_stocks,
            "negativeStocks": negative_stocks,
            "indices": indices
        }
    except Exception as e:
        return {
            "totalStocks": 0,
            "positiveStocks": 0,
            "negativeStocks": 0,
        }

@router.get("/news")
@limiter.limit("20/minute")
async def get_market_news(request: Request):
    """Get market news headlines from popular tickers"""
    try:
        stocks = StockDataService.get_popular_stocks()
        symbols = [s.get("symbol") for s in stocks if s.get("symbol")][:6]
        seen = set()
        news_items = []

        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                items = ticker.news[:5] if hasattr(ticker, "news") else []
                for item in items:
                    title = item.get("title", "")
                    if not title or title in seen:
                        continue
                    seen.add(title)
                    news_items.append({
                        "title": title,
                        "publisher": item.get("publisher", ""),
                        "link": item.get("link", ""),
                        "providerPublishTime": item.get("providerPublishTime", None),
                        "symbol": symbol,
                    })
                    if len(news_items) >= 10:
                        break
            except Exception:
                continue

        return news_items
    except Exception:
        return []
