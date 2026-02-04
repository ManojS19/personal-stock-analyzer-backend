import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import yfinance as yf
import ta
import pickle
import os
from typing import Dict, Tuple
from datetime import datetime, timedelta

class MLStockAnalyzer:
    """Machine Learning service for stock analysis and recommendations"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = "./models/stock_predictor.pkl"
        self._load_or_train_model()
    
    def _load_or_train_model(self):
        """Load existing model or train a new one"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    
                # Support both old format (direct model) and new format (dict)
                if isinstance(data, dict):
                    self.model = data.get('model')
                    self.scaler = data.get('scaler')
                    print("Model and Scaler loaded successfully")
                else:
                    self.model = data
                    print("Model loaded successfully (legacy format)")
                    
            except Exception as e:
                print(f"Error loading model: {e}. Training new model...")
                self._train_model()
        else:
            self._train_model()
    
    def _train_model(self):
        """Train ML model on historical stock data"""
        print("Training ML model...")
        
        # Indian market leaders for training
        symbols = [
            "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
            "LT.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "ASIANPAINT.NS",
            "HINDUNILVR.NS", "LT.NS", "KOTAKBANK.NS", "AXISBANK.NS", "ADANIENT.NS"
        ]
        
        features_list = []
        targets_list = []
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2y")
                
                if len(hist) < 100:
                    continue
                
                # Calculate technical indicators
                df = self._calculate_indicators(hist)
                
                # Create features
                feature_cols = ['RSI', 'MACD', 'MACD_signal', 'BB_upper', 'BB_lower', 
                               'SMA_20', 'SMA_50', 'EMA_12', 'EMA_26', 'ATR',
                               'volume_ratio', 'price_change', 'volatility']
                
                # Prepare features and targets
                for i in range(50, len(df) - 1):
                    features = df[feature_cols].iloc[i].values
                    # Target: 1 if price goes up next day, 0 otherwise
                    target = 1 if df['Close'].iloc[i+1] > df['Close'].iloc[i] else 0
                    
                    if not np.isnan(features).any():
                        features_list.append(features)
                        targets_list.append(target)
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                continue
        
        if len(features_list) < 100:
            print("Not enough training data. Using default model.")
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            return
        
        # Train model
        X = np.array(features_list)
        y = np.array(targets_list)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Save model and scaler
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler
            }, f)
        
        accuracy = self.model.score(X_test_scaled, y_test)
        print(f"Model trained with accuracy: {accuracy:.2%}")
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        df = df.copy()
        
        # RSI
        df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
        
        # MACD
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(df['Close'])
        df['BB_upper'] = bb.bollinger_hband()
        df['BB_lower'] = bb.bollinger_lband()
        
        # Moving Averages
        df['SMA_20'] = ta.trend.SMAIndicator(df['Close'], window=20).sma_indicator()
        df['SMA_50'] = ta.trend.SMAIndicator(df['Close'], window=50).sma_indicator()
        df['EMA_12'] = ta.trend.EMAIndicator(df['Close'], window=12).ema_indicator()
        df['EMA_26'] = ta.trend.EMAIndicator(df['Close'], window=26).ema_indicator()
        
        # ATR
        df['ATR'] = ta.volatility.AverageTrueRange(
            df['High'], df['Low'], df['Close']
        ).average_true_range()
        
        # Volume ratio
        df['volume_ratio'] = df['Volume'] / df['Volume'].rolling(20).mean()
        
        # Price change
        df['price_change'] = df['Close'].pct_change()
        
        # Volatility
        df['volatility'] = df['Close'].rolling(20).std()
        
        return df.bfill().fillna(0)
    
    def _convert_numpy(self, obj):
        """Convert numpy types to native Python types for JSON compatibility"""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    def analyze_stock(self, symbol: str) -> Dict:
        """Analyze a stock and provide recommendation"""
        # Try auto-suffixing for Indian stocks if no exchange is specified
        search_symbols = [symbol.upper()]
        if "." not in symbol:
            search_symbols.append(f"{symbol.upper()}.NS")
            search_symbols.append(f"{symbol.upper()}.BO")
        
        last_error = None
        for sym in search_symbols:
            try:
                ticker = yf.Ticker(sym)
                hist = ticker.history(period="6mo")
                info = ticker.info
                
                if hist.empty:
                    continue
                
                # Calculate indicators
                df = self._calculate_indicators(hist)
                
                # Get latest features
                feature_cols = ['RSI', 'MACD', 'MACD_signal', 'BB_upper', 'BB_lower', 
                               'SMA_20', 'SMA_50', 'EMA_12', 'EMA_26', 'ATR',
                               'volume_ratio', 'price_change', 'volatility']
                
                latest_features = df[feature_cols].iloc[-1].values.reshape(1, -1)
                latest_features_scaled = self.scaler.transform(latest_features)
                
                # Predict
                prediction = self.model.predict(latest_features_scaled)[0]
                probabilities = self.model.predict_proba(latest_features_scaled)[0]
                confidence = max(probabilities) * 100
                
                # Calculate scores
                fundamental_score = self._calculate_fundamental_score(info)
                technical_score = self._calculate_technical_score(df)
                
                # Determine recommendation
                if prediction == 1 and confidence > 60:
                    recommendation = "BUY"
                elif prediction == 0 and confidence > 60:
                    recommendation = "SELL"
                else:
                    recommendation = "HOLD"
                
                # Generate insights
                insights = self._generate_insights(df, info, recommendation, sym)
                
                # Risk assessment
                risk_level = self._assess_risk(df, info)
                
                return {
                    "symbol": sym,
                    "recommendation": recommendation,
                    "confidence": round(confidence, 2),
                    "fundamentalScore": round(fundamental_score, 2),
                    "technicalScore": round(technical_score, 2),
                    "insights": insights,
                    "riskLevel": risk_level,
                    "rsi": self._convert_numpy(df['RSI'].iloc[-1]),
                    "macd": self._convert_numpy(df['MACD'].iloc[-1]),
                    "movingAverage": f"{'₹' if sym.endswith(('.NS', '.BO')) else '$'}{df['SMA_20'].iloc[-1]:.2f}",
                }
            except Exception as e:
                # Re-throw StandardScaler error to be caught by the outer loop
                if "StandardScaler instance is not fitted" in str(e):
                    raise e
                last_error = e
                continue
        
        # If we get here, all syms failed
        if last_error and "StandardScaler instance is not fitted" in str(last_error):
            # Outer retry logic handles this
            raise last_error
            
        try: # This try-except block was originally outside the analyze_stock method, now it wraps the entire logic
            raise Exception(f"AI Analysis failed for {symbol}: {str(last_error) if last_error else 'No historical data available'}")
        except Exception as e:
            if "StandardScaler instance is not fitted" in str(e):
                # Fallback if scaler hasn't been loaded yet
                print("Scaler not fitted. Retraining...")
                self._train_model()
                return self.analyze_stock(symbol)
            raise Exception(f"AI Analysis failed: {str(e)}")
    
    def _calculate_fundamental_score(self, info: Dict) -> float:
        """Calculate fundamental analysis score (0-100)"""
        score = 50  # Base score
        
        # P/E Ratio (lower is better, but not too low)
        pe = info.get('trailingPE', 0)
        if pe and 10 < pe < 25:
            score += 10
        elif pe and (pe < 10 or pe > 30):
            score -= 10
        
        # Profit margin
        profit_margin = info.get('profitMargins', 0)
        if profit_margin:
            score += profit_margin * 100 * 2
        
        # Revenue growth
        revenue_growth = info.get('revenueGrowth', 0)
        if revenue_growth:
            score += revenue_growth * 50
        
        # Debt to equity
        debt_to_equity = info.get('debtToEquity', 0)
        if debt_to_equity and debt_to_equity < 50:
            score += 10
        
        return max(0, min(100, score))
    
    def _calculate_technical_score(self, df: pd.DataFrame) -> float:
        """Calculate technical analysis score (0-100)"""
        score = 50  # Base score
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # RSI
        rsi = latest['RSI']
        if 30 < rsi < 70:
            score += 10
        elif rsi < 30:  # Oversold
            score += 15
        elif rsi > 70:  # Overbought
            score -= 10
        
        # MACD
        if latest['MACD'] > latest['MACD_signal']:
            score += 10
        
        # Price vs Moving Averages
        if latest['Close'] > latest['SMA_20']:
            score += 10
        if latest['Close'] > latest['SMA_50']:
            score += 10
        
        # Trend
        if latest['Close'] > prev['Close']:
            score += 5
        
        return max(0, min(100, score))
    
    def _generate_insights(self, df: pd.DataFrame, info: Dict, recommendation: str, symbol: str) -> str:
        """Generate AI insights about the stock"""
        # Use dynamic currency symbol
        currency = "₹" if symbol.endswith((".NS", ".BO")) else "$"
        
        # Trend Analysis
        twenty_day_change = ((df['Close'].iloc[-1] - df['Close'].iloc[-20]) / df['Close'].iloc[-20]) * 100
        trend = "bullish" if twenty_day_change > 0 else "bearish"
        
        # Indicator Insights
        rsi = df['RSI'].iloc[-1]
        rsi_insight = "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral"
        
        macd = df['MACD'].iloc[-1]
        macd_signal = df['MACD_signal'].iloc[-1]
        macd_insight = "bullish crossover" if macd > macd_signal else "bearish momentum"
        
        # Fundamental Insights
        pe = info.get('trailingPE', 0)
        valuation = "undervalued" if pe > 0 and pe < 15 else "overvalued" if pe > 30 else "fairly valued"
        
        insights = f"AI analysis for {symbol} suggests a {recommendation.lower()} stance. "
        insights += f"The 20-day trend is {trend} ({twenty_day_change:+.2f}%). "
        insights += f"Technical indicators show RSI is {rsi_insight} at {rsi:.1f}, with {macd_insight} on the MACD. "
        
        if pe > 0:
            insights += f"Fundamentally, the stock is currently {valuation} with a P/E ratio of {pe:.1f}. "
        
        current_price = df['Close'].iloc[-1]
        insights += f"Support is expected around {currency}{current_price * 0.95:.2f}."
        
        return insights
    
    def _assess_risk(self, df: pd.DataFrame, info: Dict) -> str:
        """Assess investment risk level"""
        volatility = df['Close'].rolling(20).std().iloc[-1] / df['Close'].iloc[-1] * 100
        
        risk_factors = 0
        
        if volatility > 3:
            risk_factors += 1
        if info.get('beta', 1) > 1.5:
            risk_factors += 1
        if info.get('debtToEquity', 0) > 100:
            risk_factors += 1
        
        if risk_factors == 0:
            return "Low Risk"
        elif risk_factors == 1:
            return "Moderate Risk"
        else:
            return "High Risk"

# Global instance
ml_analyzer = MLStockAnalyzer()
