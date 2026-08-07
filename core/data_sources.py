import yfinance as yf
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class yfinanceWrapper:
    @staticmethod
    def fetch_ohlcv(ticker: str, timeframe: str = "15m", period: str = "5d") -> pd.DataFrame:
        try:
            data = yf.download(ticker, period=period, interval=timeframe, progress=False)
            if data.empty:
                return pd.DataFrame()
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = [col[0] for col in data.columns]
            return data[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
        except Exception as e:
            logger.error(f"yfinance fetch error for {ticker}: {e}")
            return pd.DataFrame()

    @staticmethod
    def fetch_vix() -> float:
        try:
            vix_df = yf.download("^INDIAVIX", period="5d", interval="1d", progress=False)
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
