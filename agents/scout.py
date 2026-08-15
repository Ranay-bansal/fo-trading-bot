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
        self.fo_universe = get_fo_universe()
        indices_count = len(self.fo_universe.get("indices", []))
        stocks_count = len(self.fo_universe.get("stocks", []))
        logger.info(f"[Scout] F&O Universe loaded: {indices_count} indices + {stocks_count} stocks = {indices_count + stocks_count} total instruments.")

    def _batch_fetch(self, tickers: List[str], timeframe: str) -> Dict[str, pd.DataFrame]:
        """
        Fast batch download OHLCV for all tickers at once using yfinance group_by.
        Uses 5d period for intraday (1m, 5m, 15m) so weekend/holiday/after-hours runs always have data.
        """
        results: Dict[str, pd.DataFrame] = {}
        if not tickers:
            return results
        try:
            period = "5d" if timeframe in ("1m", "5m", "15m") else "1mo"
            raw = yf.download(
                tickers, period=period, interval=timeframe,
                group_by="ticker", progress=False, threads=True, timeout=25
            )
            for ticker in tickers:
                try:
                    if len(tickers) == 1:
                        df = raw.copy()
                    else:
                        if ticker in raw.columns.get_level_values(0):
                            df = raw[ticker].copy()
                        else:
                            df = pd.DataFrame()
                    if not df.empty:
                        df.columns = [c if isinstance(c, str) else c[0] for c in df.columns]
                        required_cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
                        if len(required_cols) == 5:
                            df = df[required_cols].dropna()
                            results[ticker] = df
                        else:
                            results[ticker] = pd.DataFrame()
                    else:
                        results[ticker] = pd.DataFrame()
                except Exception:
                    results[ticker] = pd.DataFrame()
        except Exception as e:
            logger.warning(f"[Scout] Batch download warning ({e}).")
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
                continue

            try:
                spot       = float(df["Close"].iloc[-1])
                prev_close = float(df["Close"].iloc[-2]) if len(df) >= 2 else spot
                change_pct = ((spot - prev_close) / prev_close) * 100.0 if prev_close > 0 else 0.0
                vol_recent = df["Volume"].iloc[-3:].mean() if "Volume" in df.columns else 1.0
                vol_avg    = df["Volume"].mean() if ("Volume" in df.columns and len(df) >= 5) else vol_recent
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
            except Exception as e:
                logger.debug(f"Index screen skip {ticker}: {e}")

        # 2. Screen All NSE F&O Stocks
        for stk in stocks_list:
            ticker = stk["ticker"]
            df = stock_data.get(ticker, pd.DataFrame())
            if df.empty or len(df) < 5:
                continue

            try:
                spot       = float(df["Close"].iloc[-1])
                prev_close = float(df["Close"].iloc[-2]) if len(df) >= 2 else spot
                change_pct = ((spot - prev_close) / prev_close) * 100.0 if prev_close > 0 else 0.0
                vol_recent = df["Volume"].iloc[-3:].mean() if "Volume" in df.columns else 1.0
                vol_avg    = df["Volume"].mean() if ("Volume" in df.columns and len(df) >= 5) else vol_recent
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
            except Exception as e:
                logger.debug(f"Stock screen skip {ticker}: {e}")

        logger.info(f"[F&O Scout] Screened {len(candidates)} active F&O instruments on {timeframe} timeframe.")
        return candidates
