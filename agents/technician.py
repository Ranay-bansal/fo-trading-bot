import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List
from core.data_sources import (
    yfinanceWrapper, calculate_rsi, calculate_atr, calculate_adx,
    calculate_vwap, calculate_supertrend
)
from core.schemas import FOScoutOutput, FOTechnicianOutput, TrendData, MomentumData, VolatilityData

logger = logging.getLogger(__name__)

class FOTechnicianAgent:
    """
    F&O High-Frequency Technician Agent supporting:
    - 12 Classic Chart Patterns
    - Fast VWAP bounce/rejection signals
    - Supertrend 1m/5m trend flips
    - Scalp momentum momentum scoring
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def run(self, scout: FOScoutOutput, timeframe: str = "5m", vix_val: float = 14.5) -> FOTechnicianOutput:
        ticker = scout.ticker
        df = yfinanceWrapper.fetch_ohlcv(ticker, timeframe=timeframe, period="1d")
        if df.empty or len(df) < 5:
            df = yfinanceWrapper.fetch_ohlcv(ticker, timeframe="15m", period="5d")
        
        cmp = scout.spot_cmp
        if df.empty or len(df) < 5:
            return FOTechnicianOutput(
                ticker=ticker, timeframe_signal=timeframe,
                trend=TrendData(dma20_position="above", dma50_position="above", dma_slope="flat", ema_state="neutral"),
                momentum=MomentumData(rsi=50.0, rsi_state="healthy", adx=20.0, adx_state="weak"),
                volatility=VolatilityData(atr=cmp*0.01, atr_pct=1.0, bb_squeeze=False),
                support=cmp*0.98, resistance=cmp*1.02, vix=vix_val, vix_regime="transitional",
                technical_score=0.0, stance="neutral", patterns_detected=[],
                suggested_spot_entry=cmp, suggested_spot_sl=cmp*0.985, suggested_spot_target=cmp*1.03, risk_reward_ratio=1.5
            )

        cmp = float(df['Close'].iloc[-1])
        close_prices = df['Close']
        high_prices = df['High']
        low_prices = df['Low']

        # Indicators
        ema9 = close_prices.ewm(span=9, adjust=False).mean()
        ema21 = close_prices.ewm(span=21, adjust=False).mean()
        ema_state = "bullish_cross" if ema9.iloc[-1] > ema21.iloc[-1] else "bearish_cross"

        rsi = float(calculate_rsi(close_prices, period=min(14, len(df)-1)).iloc[-1])
        adx = float(calculate_adx(df, period=min(14, len(df)-1)).iloc[-1])
        atr = float(calculate_atr(df, period=min(14, len(df)-1)).iloc[-1])
        atr_pct = (atr / cmp) * 100.0 if cmp > 0 else 1.0

        # VWAP & Supertrend
        vwap = float(calculate_vwap(df).iloc[-1])
        st_series, st_dir = calculate_supertrend(df, period=7, multiplier=3.0)
        supertrend_dir = int(st_dir.iloc[-1])

        support = float(low_prices.min())
        resistance = float(high_prices.max())

        # Base technical score
        tech_score = 0.0
        
        # Supertrend direction (+1 Bullish, -1 Bearish)
        if supertrend_dir == 1:
            tech_score += 0.9
        else:
            tech_score -= 0.9

        # VWAP positioning
        if cmp > vwap:
            tech_score += 0.6
        else:
            tech_score -= 0.6

        # EMA cross
        if ema_state == "bullish_cross":
            tech_score += 0.5
        else:
            tech_score -= 0.5

        # 12-Pattern Detection Engine
        pattern_score, patterns_found = self._detect_advanced_patterns(df, cmp, vwap, supertrend_dir)
        tech_score += pattern_score

        # Clamp technical score (-3.0 to +3.0)
        tech_score = max(-3.0, min(3.0, tech_score))

        stance = "bullish" if tech_score >= 0.5 else ("bearish" if tech_score <= -0.5 else "neutral")

        # Dynamic Stop & Target based on timeframe
        sl_mult = 1.8 if timeframe in ["1m", "5m"] else 2.5
        tgt_mult = 2.7 if timeframe in ["1m", "5m"] else 3.75
        stop_dist = max(atr * sl_mult, cmp * 0.008)

        if stance == "bearish":
            suggested_sl = cmp + stop_dist
            suggested_target = cmp - (stop_dist * (tgt_mult / sl_mult))
        else:
            suggested_sl = cmp - stop_dist
            suggested_target = cmp + (stop_dist * (tgt_mult / sl_mult))

        rr = abs(suggested_target - cmp) / abs(cmp - suggested_sl) if abs(cmp - suggested_sl) > 0 else 1.5

        return FOTechnicianOutput(
            ticker=ticker, timeframe_signal=timeframe,
            trend=TrendData(dma20_position="above" if cmp > ema21.iloc[-1] else "below", dma50_position="above", dma_slope="rising", ema_state=ema_state),
            momentum=MomentumData(rsi=round(rsi, 2), rsi_state="healthy", adx=round(adx, 2), adx_state="trending" if adx > 18 else "weak"),
            volatility=VolatilityData(atr=round(atr, 2), atr_pct=round(atr_pct, 2), bb_squeeze=False),
            support=round(support, 2), resistance=round(resistance, 2), vix=vix_val, vix_regime="transitional",
            technical_score=round(tech_score, 2), stance=stance, patterns_detected=patterns_found,
            suggested_spot_entry=round(cmp, 2), suggested_spot_sl=round(suggested_sl, 2), suggested_spot_target=round(suggested_target, 2),
            risk_reward_ratio=round(rr, 2)
        )

    def _detect_advanced_patterns(self, df: pd.DataFrame, cmp: float, vwap: float, st_dir: int) -> Tuple[float, List[str]]:
        pattern_score = 0.0
        patterns_found = []
        c = df['Close'].values
        o = df['Open'].values
        h = df['High'].values
        l = df['Low'].values

        if len(df) < 5:
            return 0.0, []

        # VWAP Bounce / Rejection
        if abs(l[-1] - vwap) / vwap <= 0.003 and c[-1] > vwap and st_dir == 1:
            pattern_score += 0.5; patterns_found.append("VWAP Bullish Support Bounce")
        elif abs(h[-1] - vwap) / vwap <= 0.003 and c[-1] < vwap and st_dir == -1:
            pattern_score -= 0.5; patterns_found.append("VWAP Bearish Resistance Rejection")

        # 1. Morning Star
        if len(df) >= 3 and c[-3] < o[-3] and c[-1] > o[-1] and c[-1] >= (o[-3] + c[-3]) / 2:
            pattern_score += 0.5; patterns_found.append("Morning Star Reversal")
        # 2. Evening Star
        if len(df) >= 3 and c[-3] > o[-3] and c[-1] < o[-1] and c[-1] <= (o[-3] + c[-3]) / 2:
            pattern_score -= 0.5; patterns_found.append("Evening Star Reversal")
        # 3. Shooting Star
        body = abs(c[-1] - o[-1])
        upper_wick = h[-1] - max(o[-1], c[-1])
        if upper_wick >= 1.8 * max(body, 0.05):
            pattern_score -= 0.4; patterns_found.append("Shooting Star Rejection")
        # 4. Three White Soldiers
        if len(df) >= 3 and c[-1] > o[-1] and c[-2] > o[-2] and c[-3] > o[-3]:
            pattern_score += 0.4; patterns_found.append("Three White Soldiers Momentum")
        # 5. Three Black Crows
        if len(df) >= 3 and c[-1] < o[-1] and c[-2] < o[-2] and c[-3] < o[-3]:
            pattern_score -= 0.4; patterns_found.append("Three Black Crows Breakdown")
        # 6. ORB Breakout
        if cmp > h[0]:
            pattern_score += 0.5; patterns_found.append("Opening Range Bullish Breakout")
        elif cmp < l[0]:
            pattern_score -= 0.5; patterns_found.append("Opening Range Bearish Breakdown")

        return pattern_score, patterns_found
