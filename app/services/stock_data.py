import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from app.core.config import settings

class StockDataService:
    """Service for fetching and processing stock data"""
    
    @staticmethod
    def get_stock_info(symbol: str) -> Dict:
        """Get comprehensive stock information"""
        # Try auto-suffixing for Indian stocks if no exchange is specified
        search_symbols = [symbol.upper()]
        if "." not in symbol:
            search_symbols.append(f"{symbol.upper()}.NS")
            search_symbols.append(f"{symbol.upper()}.BO")
        
        last_error = None
        for sym in search_symbols:
            try:
                ticker = yf.Ticker(sym)
                # Check for existence with history
                hist = ticker.history(period="1d")
                if hist.empty:
                    continue
                    
                info = ticker.info
                current_price = hist['Close'].iloc[-1]
                
                # Get previous close
                prev_close = info.get('previousClose', current_price)
                change = current_price - prev_close
                change_percent = (change / prev_close * 100) if prev_close > 0 else 0
                
                # Determine currency based on actual sym found
                currency = "₹" if sym.endswith((".NS", ".BO")) else "$"
                
                return {
                    "symbol": sym,
                    "name": info.get('longName', sym),
                    "price": float(current_price),
                    "currency": currency,
                    "change": float(change_percent),
                    "changeAmount": float(change),
                    "previousClose": float(prev_close),
                    "volume": int(info.get('volume', 0)),
                    "marketCap": info.get('marketCap', 0),
                    "peRatio": info.get('trailingPE', 0),
                    "eps": info.get('trailingEps', 0),
                    "dividendYield": info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                    "52WeekHigh": info.get('fiftyTwoWeekHigh', 0),
                    "52WeekLow": info.get('fiftyTwoWeekLow', 0),
                }
            except Exception as e:
                last_error = e
                continue
                
        raise Exception(f"Error fetching stock data for {symbol}: {str(last_error) if last_error else 'Symbol not found'}")
    
    @staticmethod
    def get_historical_data(symbol: str, period: str = "1mo") -> Dict:
        """Get historical price data for charts"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return {"labels": [], "values": []}
            
            # Format data for chart
            dates = hist.index.strftime('%m/%d').tolist()
            raw_dates = hist.index.astype(np.int64) // 10**9 # Convert to unix timestamps
            closes = hist['Close'].tolist()
            
            return {
                "labels": dates,
                "values": closes,
                "timestamps": raw_dates.tolist()
            }
        except Exception as e:
            raise Exception(f"Error fetching historical data: {str(e)}")
    
    @staticmethod
    def get_fundamental_data(symbol: str) -> Dict:
        """Get fundamental analysis data"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            # Determine currency
            currency = "₹" if symbol.endswith((".NS", ".BO")) else "$"
            
            return {
                "marketCap": f"{currency}{info.get('marketCap', 0):,.0f}" if info.get('marketCap') else "N/A",
                "peRatio": f"{info.get('trailingPE', 0):.2f}" if info.get('trailingPE') else "N/A",
                "eps": f"{currency}{info.get('trailingEps', 0):.2f}" if info.get('trailingEps') else "N/A",
                "dividendYield": f"{info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') else "0%",
                "revenue": f"{currency}{info.get('totalRevenue', 0):,.0f}" if info.get('totalRevenue') else "N/A",
                "profitMargin": f"{info.get('profitMargins', 0) * 100:.2f}%" if info.get('profitMargins') else "N/A",
            }
        except Exception as e:
            raise Exception(f"Error fetching fundamental data: {str(e)}")
    
    @staticmethod
    def get_popular_stocks() -> List[Dict]:
        """Get list of popular stocks with recommendations"""
        # Indian market leaders
        popular_symbols = [
            "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
            "LT.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "ASIANPAINT.NS"
        ]
        stocks = []
        
        for symbol in popular_symbols:
            try:
                stock_info = StockDataService.get_stock_info(symbol)
                # Add mock recommendation (will be replaced by ML model)
                stock_info.update({
                    "recommendation": "BUY",  # Will be from ML model
                    "confidence": 85,  # Will be from ML model
                })
                stocks.append(stock_info)
            except Exception as e:
                print(f"Error fetching {symbol}: {str(e)}")
                continue
        
        return stocks
