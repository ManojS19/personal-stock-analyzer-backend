import yfinance as yf
import sys

def check_symbol(symbol):
    print(f"Checking {symbol}...")
    try:
        ticker = yf.Ticker(symbol)
        # Try to get 1 day of history to see if it exists
        hist = ticker.history(period="1d")
        if hist.empty:
            print(f"FAILED: {symbol} returned empty history.")
            # Check info as fallback
            # info = ticker.info # info can be slow or fail
            # print(f"Info for {symbol}: {info.get('longName', 'No Name Found')}")
        else:
            print(f"SUCCESS: {symbol} price is {hist['Close'].iloc[-1]}")
    except Exception as e:
        print(f"ERROR for {symbol}: {str(e)}")

if __name__ == "__main__":
    test_symbols = [
        "RELIANCE.NS", 
        "TCS.NS", 
        "HDFCBANK.NS", 
        "INFY.NS", 
        "SBIN.NS", # Correct symbol for SBI
        "SBI.NS",  # Incorrect symbol for SBI
        "TATAMOTORS.NS",
        "ASIANPAINT.NS",
        "ITC.NS",
        "BHARTIARTL.NS"
    ]
    for sym in test_symbols:
        check_symbol(sym)
