import logging
import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
from core.data_sources import yfinanceWrapper
from core.schemas import FOScoutOutput
from core.fo_universe_loader import get_fo_universe

logger = logging.getLogger(__name__)

class FOScoutAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # Load dynamic full F&O universe (200+ stocks) instead of hardcoded 12
        self.fo_universe = get_fo_universe()
        indices_count = len(self.fo_universe.get("indices", []))
        stocks_count = len(self.fo_universe.get("stocks", []))
        logger.info(f"[Scout] F&O Universe loaded: {indices_count} indices + {stocks_count} stocks = {indices_count + stocks_count} total instruments.")

    def _batch_fetch(self, tickers: List[str], timeframe: str) -> Dict[str, pd.DataFrame]:
        """
        Batch-download OHLCV for all tickers at once using yfinance group_by.
        Much faster than N individual HTTP calls for a 200-stock universe.
        """
        results: Dict[str, pd.DataFrame] = {}
        if not tickers:
            return results
        try:
            period = "1d" if timeframe in ("1m", "5m", "15m") else "5d"
            raw = yf.download(
                tickers, period=period, interval=timeframe,
                group_by="ticker", progress=False, threads=True, timeout=30
            )
            for ticker in tickers:
                try:
                    if len(tickers) == 1:
                        df = raw.copy()
                    else:
                        df = raw[ticker].copy() if ticker in raw.columns.get_level_values(0) else pd.DataFrame()
                    df.columns = [c if isinstance(c, str) else c[0] for c in df.columns]
                    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
                    results[ticker] = df
                except Exception:
                    results[ticker] = pd.DataFrame()
        except Exception as e:
            logger.warning(f"[Scout] Batch download failed ({e}), falling back to individual fetches.")
            for ticker in tickers:
                results[ticker] = yfinanceWrapper.fetch_ohlcv(ticker, timeframe=timeframe, period="1d")
        return results

    def run(self, timeframe: str = "5m") -> List[FOScoutOutput]:
        logger.info(f"[F&O Scout] Scanning full universe on {timeframe} timeframe...")
        candidates = []

        indices_list = self.fo_universe.get("indices", [])
        stocks_list  = self.fo_universe.get("stocks", [])

        # Batch download all tickers at once
        all_index_tickers = [idx["ticker"] for idx in indices_list]
        all_stock_tickers = [stk["ticker"] for stk in stocks_list]

        index_data = self._batch_fetch(all_index_tickers, timeframe)
        stock_data = self._batch_fetch(all_stock_tickers, timeframe)

        # 1. Screen Indices
        for idx in indices_list:
            ticker = idx["ticker"]
            df = index_data.get(ticker, pd.DataFrame())
            if df.empty or len(df) < 5:
                df = yfinanceWrapper.fetch_ohlcv(ticker, timeframe="15m", period="5d")
            if df.empty or len(df) < 5:
                continue

            spot       = float(df["Close"].iloc[-1])
            prev_close = float(df["Close"].iloc[-2]) if len(df) >= 2 else spot
            change_pct = ((spot - prev_close) / prev_close) * 100.0 if prev_close > 0 else 0.0
            vol_recent = df["Volume"].iloc[-3:].mean()
            vol_avg    = df["Volume"].mean() if len(df) >= 5 else vol_recent
            rvol       = float(vol_recent / vol_avg) if vol_avg > 0 else 1.0

            candidates.append(FOScoutOutput(
                ticker=ticker,
                symbol=idx["symbol"],
                is_index=True,
                spot_cmp=round(spot, 2),
                rvol=round(rvol, 2),
                price_change_pct=round(change_pct, 2),
                lot_size=idx["lot_size"],
                strike_step=idx["strike_step"],
                scout_rank=len(candidates) + 1,
                scout_modifier=0.6 if rvol >= 1.2 or abs(change_pct) >= 0.3 else 0.3,
            ))

        # 2. Screen All NSE F&O Stocks
        for stk in stocks_list:
            ticker = stk["ticker"]
            df = stock_data.get(ticker, pd.DataFrame())
            if df.empty or len(df) < 5:
                df = yfinanceWrapper.fetch_ohlcv(ticker, timeframe="15m", period="5d")
            if df.empty or len(df) < 5:
                continue

            spot       = float(df["Close"].iloc[-1])
            prev_close = float(df["Close"].iloc[-2]) if len(df) >= 2 else spot
            change_pct = ((spot - prev_close) / prev_close) * 100.0 if prev_close > 0 else 0.0
            vol_recent = df["Volume"].iloc[-3:].mean()
            vol_avg    = df["Volume"].mean() if len(df) >= 5 else vol_recent
            rvol       = float(vol_recent / vol_avg) if vol_avg > 0 else 1.0

            strike_step = stk.get("strike_step") or (
                2.5 if spot < 100 else 5.0 if spot < 500 else 10.0 if spot < 1000
                else 25.0 if spot < 2500 else 50.0 if spot < 5000 else 100.0
            )

            candidates.append(FOScoutOutput(
                ticker=ticker,
                symbol=stk["symbol"],
                is_index=False,
                spot_cmp=round(spot, 2),
                rvol=round(rvol, 2),
                price_change_pct=round(change_pct, 2),
                lot_size=stk["lot_size"],
                strike_step=strike_step,
                scout_rank=len(candidates) + 1,
                scout_modifier=0.5 if rvol >= 1.1 or abs(change_pct) >= 0.25 else 0.2,
            ))

        logger.info(f"[F&O Scout] Screened {len(candidates)} active F&O instruments on {timeframe} timeframe.")
        return candidates
