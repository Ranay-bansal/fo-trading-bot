import yfinance as yf
import pandas as pd
import numpy as np
import logging
from datetime import datetime
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


from pydantic import BaseModel
from typing import List, Generator

class BarEvent(BaseModel):
    ticker: str
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    rolling_df: pd.DataFrame

    class Config:
        arbitrary_types_allowed = True

class StreamingTickSimulator:
    """
    Zero-Latency Streaming Bar & Tick Simulator.
    Preloads market data and streams OHLCV bar events sequentially
    without lookahead bias.
    """
    def __init__(
        self,
        tickers: List[str],
        timeframes: List[str] = ["5m", "1m"],
        period: str = "1d",
        simulate_live: bool = False,
        delay_seconds: float = 0.0
    ):
        self.tickers = tickers
        self.timeframes = timeframes
        self.period = period
        self.simulate_live = simulate_live
        self.delay_seconds = delay_seconds
        self.data_cache: Dict[str, Dict[str, pd.DataFrame]] = {}
        self.latest_prices: Dict[str, float] = {}

    def preload(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """Preloads historical OHLCV data for all tickers and timeframes."""
        for ticker in self.tickers:
            self.data_cache[ticker] = {}
            for tf in self.timeframes:
                df = yfinanceWrapper.fetch_ohlcv(ticker, timeframe=tf, period=self.period)
                if not df.empty:
                    self.data_cache[ticker][tf] = df
        return self.data_cache

    def stream_bars(self, timeframe: str = "5m") -> Generator[BarEvent, None, None]:
        """
        Yields BarEvent objects in strict chronological order across tickers.
        """
        all_timestamps = set()
        for ticker, tf_map in self.data_cache.items():
            if timeframe in tf_map and not tf_map[timeframe].empty:
                all_timestamps.update(tf_map[timeframe].index)

        sorted_timestamps = sorted(list(all_timestamps))

        for ts in sorted_timestamps:
            for ticker in self.tickers:
                tf_map = self.data_cache.get(ticker, {})
                if timeframe in tf_map:
                    df = tf_map[timeframe]
                    if ts in df.index:
                        idx = df.index.get_loc(ts)
                        rolling_df = df.iloc[:idx + 1]
                        row = df.loc[ts]
                        close_price = float(row['Close'])
                        self.latest_prices[ticker] = close_price

                        symbol = ticker.replace(".NS", "").replace("^", "")

                        bar_evt = BarEvent(
                            ticker=ticker,
                            symbol=symbol,
                            timeframe=timeframe,
                            timestamp=ts if isinstance(ts, datetime) else pd.to_datetime(ts),
                            open=float(row['Open']),
                            high=float(row['High']),
                            low=float(row['Low']),
                            close=close_price,
                            volume=float(row['Volume']),
                            rolling_df=rolling_df
                        )
                        yield bar_evt

    def get_latest_price(self, ticker: str) -> Optional[float]:
        return self.latest_prices.get(ticker)

