import logging
from datetime import datetime
from typing import Dict, Any, List
from core.data_sources import yfinanceWrapper
from core.schemas import FOScoutOutput

logger = logging.getLogger(__name__)

class FOScoutAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.fo_universe = config.get("fo_universe", {})

    def run(self, timeframe: str = "5m") -> List[FOScoutOutput]:
        logger.info(f"Running F&O High-Frequency Scout Agent ({timeframe} timeframe)...")
        candidates = []
        
        # 1. Screen Indices (NIFTY, BANKNIFTY) across fast timeframes
        indices_list = self.fo_universe.get("indices", [])
        for idx in indices_list:
            df = yfinanceWrapper.fetch_ohlcv(idx["ticker"], timeframe=timeframe, period="1d")
            if df.empty or len(df) < 5:
                df = yfinanceWrapper.fetch_ohlcv(idx["ticker"], timeframe="15m", period="5d")
            if df.empty or len(df) < 5:
                continue

            spot = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2]) if len(df) >= 2 else spot
            change_pct = ((spot - prev_close) / prev_close) * 100.0 if prev_close > 0 else 0.0
            
            # High frequency RVOL calculation
            vol_recent = df['Volume'].iloc[-3:].mean()
            vol_avg = df['Volume'].mean() if len(df) >= 5 else vol_recent
            rvol = float(vol_recent / vol_avg) if vol_avg > 0 else 1.0

            candidates.append(FOScoutOutput(
                ticker=idx["ticker"],
                symbol=idx["symbol"],
                is_index=True,
                spot_cmp=round(spot, 2),
                rvol=round(rvol, 2),
                price_change_pct=round(change_pct, 2),
                lot_size=idx["lot_size"],
                strike_step=idx["strike_step"],
                scout_rank=len(candidates) + 1,
                scout_modifier=0.6 if rvol >= 1.2 or abs(change_pct) >= 0.3 else 0.3
            ))

        # 2. Screen F&O Stock Universe across fast timeframes
        stocks_list = self.fo_universe.get("stocks", [])
        for stk in stocks_list:
            df = yfinanceWrapper.fetch_ohlcv(stk["ticker"], timeframe=timeframe, period="1d")
            if df.empty or len(df) < 5:
                df = yfinanceWrapper.fetch_ohlcv(stk["ticker"], timeframe="15m", period="5d")
            if df.empty or len(df) < 5:
                continue

            spot = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2]) if len(df) >= 2 else spot
            change_pct = ((spot - prev_close) / prev_close) * 100.0 if prev_close > 0 else 0.0
            
            vol_recent = df['Volume'].iloc[-3:].mean()
            vol_avg = df['Volume'].mean() if len(df) >= 5 else vol_recent
            rvol = float(vol_recent / vol_avg) if vol_avg > 0 else 1.0

            candidates.append(FOScoutOutput(
                ticker=stk["ticker"],
                symbol=stk["symbol"],
                is_index=False,
                spot_cmp=round(spot, 2),
                rvol=round(rvol, 2),
                price_change_pct=round(change_pct, 2),
                lot_size=stk["lot_size"],
                strike_step=stk["strike_step"],
                scout_rank=len(candidates) + 1,
                scout_modifier=0.5 if rvol >= 1.1 or abs(change_pct) >= 0.25 else 0.2
            ))

        logger.info(f"[High-Frequency Scout] Screened {len(candidates)} active F&O symbols on {timeframe} timeframe.")
        return candidates
