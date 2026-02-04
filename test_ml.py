import sys
import os

# Add the project directory to sys.path
sys.path.append('/Users/apple/Desktop/Stock-App/server')

from app.services.ml_service import ml_analyzer
from app.services.stock_data import StockDataService

def test_analysis(symbol):
    try:
        print(f"--- Testing AI Analysis for '{symbol}' ---")
        result = ml_analyzer.analyze_stock(symbol)
        print(f"SUCCESS: Found {result['symbol']} - Rec: {result['recommendation']}")
    except Exception as e:
        print(f"FAILED for {symbol}: {str(e)}")

def test_stock_info(symbol):
    try:
        print(f"--- Testing Stock Info for '{symbol}' ---")
        result = StockDataService.get_stock_info(symbol)
        print(f"SUCCESS: Found {result['symbol']} - Price: {result['currency']}{result['price']}")
    except Exception as e:
        print(f"FAILED for {symbol}: {str(e)}")

if __name__ == "__main__":
    # Test auto-suffixing
    test_analysis("RELIANCE")
    test_stock_info("SBIN")
    
    # Test corrected symbols
    test_stock_info("LT.NS")
    
    # Test currently flaking/missing symbol
    test_stock_info("TATAMOTORS.NS")
