import yfinance as yf
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class yfinanceWrapper:
    @staticmethod
    def fetch_ohlcv(ticker: str, timeframe: str = "5m", period: str = "1d") -> pd.DataFrame:
        try:
            data = yf.download(ticker, period=period, interval=timeframe, progress=False)
            if data.empty:
                # Fallback to 5d period if 1d fails or is off-hours
                data = yf.download(ticker, period="5d", interval=timeframe, progress=False)
            if data.empty:
                return pd.DataFrame()
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = [col[0] for col in data.columns]
            return data[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
        except Exception as e:
            logger.error(f"yfinance fetch error for {ticker} ({timeframe}): {e}")
            return pd.DataFrame()

    @staticmethod
    def fetch_vix() -> float:
        try:
            vix_df = yf.download("^INDIAVIX", period="5d", interval="5m", progress=False)
            if not vix_df.empty:
                if isinstance(vix_df.columns, pd.MultiIndex):
                    vix_df.columns = [col[0] for col in vix_df.columns]
                return float(vix_df['Close'].iloc[-1])
        except Exception as e:
            logger.error(f"VIX fetch error: {e}")
        return 14.5  # Neutral fallback

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df['High']
    low = df['Low']
    close = df['Close'].shift(1)
    tr = pd.concat([high - low, (high - close).abs(), (low - close).abs()], axis=1).max(axis=1)
    return tr.rolling(window=period).mean().fillna(0.0)

def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df['High']
    low = df['Low']
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    tr = calculate_atr(df, period)
    plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(period).mean() / tr.replace(0, np.nan))
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(period).mean() / tr.replace(0, np.nan))
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.rolling(period).mean().fillna(20.0)

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """Calculates Volume Weighted Average Price (VWAP) for fast scalping."""
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3.0
    vwap = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum().replace(0, np.nan)
    return vwap.fillna(df['Close'])

def calculate_supertrend(df: pd.DataFrame, period: int = 7, multiplier: float = 3.0) -> Tuple[pd.Series, pd.Series]:
    """Calculates Supertrend indicator for high-frequency trend flips."""
    atr = calculate_atr(df, period)
    hl2 = (df['High'] + df['Low']) / 2.0
    basic_upper = hl2 + (multiplier * atr)
    basic_lower = hl2 - (multiplier * atr)
    
    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)
    
    st_val = hl2.iloc[0]
    dir_val = 1
    
    for i in range(len(df)):
        if i == 0:
            supertrend.iloc[i] = st_val
            direction.iloc[i] = dir_val
            continue
        
        close_curr = df['Close'].iloc[i]
        close_prev = df['Close'].iloc[i-1]
        
        if close_curr > basic_upper.iloc[i-1]:
            dir_val = 1
        elif close_curr < basic_lower.iloc[i-1]:
            dir_val = -1
            
        st_val = basic_lower.iloc[i] if dir_val == 1 else basic_upper.iloc[i]
        supertrend.iloc[i] = st_val
        direction.iloc[i] = dir_val
        
    return supertrend, direction
