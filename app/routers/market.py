from fastapi import APIRouter, Depends, Request
import yfinance as yf
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.services.stock_data import StockDataService
from app.services.ml_service import ml_analyzer

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
                items = ticker.news
                
                items = items[:5] if items else []
                for item in items:
                    # Handle nested structure from yfinance
                    content = item.get('content', {})
                    if not content:
                        # Fallback for old structure or direct keys
                        content = item
                        
                    title = content.get("title", "")
                    if not title or title in seen:
                        continue
                    seen.add(title)
                    
                    # Extract publisher
                    provider = content.get("provider", {})
                    publisher = provider.get("displayName", "") if isinstance(provider, dict) else ""
                    
                    # Extract link
                    canonical = content.get("canonicalUrl", {})
                    link = canonical.get("url", "") if isinstance(canonical, dict) else ""
                    if not link:
                        click_through = content.get("clickThroughUrl", {})
                        link = click_through.get("url", "") if isinstance(click_through, dict) else ""
                    
                    # Extract Image URL
                    thumbnail = content.get("thumbnail", {})
                    image_url = ""
                    if isinstance(thumbnail, dict):
                        image_url = thumbnail.get("originalUrl", "")
                        if not image_url:
                            resolutions = thumbnail.get("resolutions", [])
                            if resolutions and isinstance(resolutions, list):
                                image_url = resolutions[0].get("url", "")

                    # AI Analysis
                    analysis = ml_analyzer.analyze_news_sentiment(title)

                    news_items.append({
                        "title": title,
                        "publisher": publisher,
                        "link": link,
                        "imageUrl": image_url,
                        "providerPublishTime": content.get("pubDate", content.get("providerPublishTime")),
                        "symbol": symbol,
                        "aiAnalysis": analysis
                    })
                    if len(news_items) >= 10:
                        break
            except Exception as e:
                continue

        return news_items
    except Exception as e:
        return []
