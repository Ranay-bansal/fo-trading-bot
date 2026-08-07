import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List
from core.data_sources import yfinanceWrapper, calculate_rsi, calculate_atr, calculate_adx
from core.schemas import FOScoutOutput, FOTechnicianOutput, TrendData, MomentumData, VolatilityData

logger = logging.getLogger(__name__)

class FOTechnicianAgent:
    """
    F&O Technician Agent with 12 Chart Patterns:
    - W/M Patterns, Bull/Bear Flags, Morning/Evening Stars, Shooting Star,
      3 Soldiers/Crows, ORB-15m, Ascending/Descending Triangles.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def run(self, scout: FOScoutOutput, vix_val: float = 14.5) -> FOTechnicianOutput:
        ticker = scout.ticker
        df = yfinanceWrapper.fetch_ohlcv(ticker, timeframe="15m", period="5d")
        if df.empty or len(df) < 15:
            cmp = scout.spot_cmp
            return FOTechnicianOutput(
                ticker=ticker, timeframe_signal="15m",
                trend=TrendData(dma20_position="above", dma50_position="above", dma_slope="flat", ema_state="neutral"),
                momentum=MomentumData(rsi=50.0, rsi_state="healthy", adx=20.0, adx_state="weak"),
                volatility=VolatilityData(atr=cmp*0.015, atr_pct=1.5, bb_squeeze=False),
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

        rsi = float(calculate_rsi(close_prices).iloc[-1])
        adx = float(calculate_adx(df).iloc[-1])
        atr = float(calculate_atr(df).iloc[-1])
        atr_pct = (atr / cmp) * 100.0

        support = float(low_prices.iloc[-20:].min())
        resistance = float(high_prices.iloc[-20:].max())

        # Base technical score
        tech_score = 0.0
        if cmp > ema21.iloc[-1] and ema_state == "bullish_cross":
            tech_score += 0.8
        elif cmp < ema21.iloc[-1] and ema_state == "bearish_cross":
            tech_score -= 0.8

        if 40 <= rsi <= 70:
            tech_score += 0.4 if ema_state == "bullish_cross" else -0.4

        if adx > 20:
            tech_score += 0.5 if ema_state == "bullish_cross" else -0.5

        # Run 12-Pattern Detection Engine
        pattern_score, patterns_found = self._detect_advanced_patterns(df, cmp)
        tech_score += pattern_score

        # Clamp technical score
        tech_score = max(-3.0, min(3.0, tech_score))

        stance = "bullish" if tech_score >= 0.5 else ("bearish" if tech_score <= -0.5 else "neutral")

        # Stop distance calculation
        sl_mult = 2.5
        tgt_mult = 3.75
        stop_dist = max(atr * sl_mult, cmp * 0.015)

        if stance == "bearish":
            suggested_sl = cmp + stop_dist
            suggested_target = cmp - (stop_dist * (tgt_mult / sl_mult))
        else:
            suggested_sl = cmp - stop_dist
            suggested_target = cmp + (stop_dist * (tgt_mult / sl_mult))

        rr = abs(suggested_target - cmp) / abs(cmp - suggested_sl) if abs(cmp - suggested_sl) > 0 else 1.0

        return FOTechnicianOutput(
            ticker=ticker, timeframe_signal="15m",
            trend=TrendData(dma20_position="above" if cmp > ema21.iloc[-1] else "below", dma50_position="above", dma_slope="rising", ema_state=ema_state),
            momentum=MomentumData(rsi=round(rsi, 2), rsi_state="healthy", adx=round(adx, 2), adx_state="trending" if adx > 20 else "weak"),
            volatility=VolatilityData(atr=round(atr, 2), atr_pct=round(atr_pct, 2), bb_squeeze=False),
            support=round(support, 2), resistance=round(resistance, 2), vix=vix_val, vix_regime="transitional",
            technical_score=round(tech_score, 2), stance=stance, patterns_detected=patterns_found,
            suggested_spot_entry=cmp, suggested_spot_sl=round(suggested_sl, 2), suggested_spot_target=round(suggested_target, 2),
            risk_reward_ratio=round(rr, 2)
        )

    def _detect_advanced_patterns(self, df: pd.DataFrame, cmp: float) -> Tuple[float, List[str]]:
        pattern_score = 0.0
        patterns_found = []
        c = df['Close'].values
        o = df['Open'].values
        h = df['High'].values
        l = df['Low'].values

        if len(df) < 15:
            return 0.0, []

        # 1. Morning Star
        if c[-3] < o[-3] and abs(c[-2] - o[-2]) < abs(c[-3] - o[-3]) * 0.35 and c[-1] > o[-1] and c[-1] >= (o[-3] + c[-3]) / 2:
            pattern_score += 0.5; patterns_found.append("Morning Star")
        # 2. Evening Star
        if c[-3] > o[-3] and abs(c[-2] - o[-2]) < abs(c[-3] - o[-3]) * 0.35 and c[-1] < o[-1] and c[-1] <= (o[-3] + c[-3]) / 2:
            pattern_score -= 0.5; patterns_found.append("Evening Star")
        # 3. Shooting Star
        body = abs(c[-1] - o[-1])
        upper_wick = h[-1] - max(o[-1], c[-1])
        if upper_wick >= 2.0 * max(body, 0.05):
            pattern_score -= 0.4; patterns_found.append("Shooting Star")
        # 4. Three White Soldiers
        if c[-1] > o[-1] and c[-2] > o[-2] and c[-3] > o[-3] and c[-1] > c[-2] > c[-3]:
            pattern_score += 0.4; patterns_found.append("Three White Soldiers")
        # 5. Three Black Crows
        if c[-1] < o[-1] and c[-2] < o[-2] and c[-3] < o[-3] and c[-1] < c[-2] < c[-3]:
            pattern_score -= 0.4; patterns_found.append("Three Black Crows")
        # 6. Double Bottom (W)
        min1, min2 = np.min(l[-20:-10]), np.min(l[-10:])
        if abs(min1 - min2) / min1 <= 0.015 and cmp > np.max(h[-15:-5]):
            pattern_score += 0.5; patterns_found.append("Double Bottom (W-Pattern)")
        # 7. Double Top (M)
        max1, max2 = np.max(h[-20:-10]), np.max(h[-10:])
        if abs(max1 - max2) / max1 <= 0.015 and cmp < np.min(l[-15:-5]):
            pattern_score -= 0.5; patterns_found.append("Double Top (M-Pattern)")
        # 8. Bull Flag
        if (h[-15] - l[-20]) / max(1.0, l[-20]) > 0.02 and cmp > np.max(h[-5:-1]):
            pattern_score += 0.5; patterns_found.append("Bull Flag Breakout")
        # 9. Bear Flag
        if (h[-20] - l[-15]) / max(1.0, h[-20]) > 0.02 and cmp < np.min(l[-5:-1]):
            pattern_score -= 0.5; patterns_found.append("Bear Flag Breakdown")
        # 10. Ascending Triangle
        if np.std(h[-15:]) / max(1.0, np.mean(h[-15:])) < 0.008 and (l[-1] - l[-15]) > 0:
            pattern_score += 0.4; patterns_found.append("Ascending Triangle")
        # 11. Descending Triangle
        if np.std(l[-15:]) / max(1.0, np.mean(l[-15:])) < 0.008 and (h[-1] - h[-15]) < 0:
            pattern_score -= 0.4; patterns_found.append("Descending Triangle")
        # 12. ORB-15
        if cmp > h[0]:
            pattern_score += 0.5; patterns_found.append("ORB-15 Bullish Breakout")
        elif cmp < l[0]:
            pattern_score -= 0.5; patterns_found.append("ORB-15 Bearish Breakdown")

        return pattern_score, patterns_found
