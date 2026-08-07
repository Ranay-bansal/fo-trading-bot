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

    def run() -> List[FOScoutOutput]:
        logger.info("Running F&O Scout Agent across Indices & Stock F&O Universe...")
        candidates = []
        
        # 1. Screen Indices (NIFTY, BANKNIFTY)
        indices_list = self.fo_universe.get("indices", [])
        for idx in indices_list:
            df = yfinanceWrapper.fetch_ohlcv(idx["ticker"], timeframe="15m", period="5d")
            if df.empty or len(df) < 10:
                continue
            spot = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2])
            change_pct = ((spot - prev_close) / prev_close) * 100.0
            
            candidates.append(FOScoutOutput(
                ticker=idx["ticker"],
                symbol=idx["symbol"],
                is_index=True,
                spot_cmp=spot,
                rvol=1.5,
                price_change_pct=change_pct,
                lot_size=idx["lot_size"],
                strike_step=idx["strike_step"],
                scout_rank=len(candidates) + 1,
                scout_modifier=0.5 if abs(change_pct) > 0.5 else 0.0
            ))

        # 2. Screen F&O Stock Universe
        stocks_list = self.fo_universe.get("stocks", [])
        for stk in stocks_list:
            df = yfinanceWrapper.fetch_ohlcv(stk["ticker"], timeframe="15m", period="5d")
            if df.empty or len(df) < 10:
                continue
            spot = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2])
            change_pct = ((spot - prev_close) / prev_close) * 100.0
            
            # Simple RVOL proxy
            vol_recent = df['Volume'].iloc[-5:].mean()
            vol_20 = df['Volume'].iloc[-20:].mean() if len(df) >= 20 else vol_recent
            rvol = float(vol_recent / vol_20) if vol_20 > 0 else 1.0

            if abs(change_pct) >= 0.5 or rvol >= 1.2:
                candidates.append(FOScoutOutput(
                    ticker=stk["ticker"],
                    symbol=stk["symbol"],
                    is_index=False,
                    spot_cmp=spot,
                    rvol=round(rvol, 2),
                    price_change_pct=round(change_pct, 2),
                    lot_size=stk["lot_size"],
                    strike_step=stk["strike_step"],
                    scout_rank=len(candidates) + 1,
                    scout_modifier=0.5 if rvol >= 1.5 else 0.2
                ))

        logger.info(f"[F&O Scout] Found {len(candidates)} active F&O opportunity candidates.")
        return candidates
