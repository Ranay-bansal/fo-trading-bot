import logging
from typing import Dict, Any, List
from core.schemas import FOScoutOutput, FOTechnicianOutput, NewsdeskOutput, BullDebaterOutput

logger = logging.getLogger(__name__)

def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            return float(val)
        if isinstance(val, str):
            return float(val)
        return default
    except Exception:
        return default

class BullDebaterAgent:
    """
    Bull Debater Agent formulating upside arguments, conviction score, target rationale, and key catalysts.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}

    def run(self, scout: FOScoutOutput, tech: FOTechnicianOutput, news: NewsdeskOutput) -> BullDebaterOutput:
        ticker = getattr(scout, "ticker", "UNKNOWN")
        symbol = getattr(scout, "symbol", "UNKNOWN")
        if not isinstance(ticker, str):
            ticker = "UNKNOWN"
        if not isinstance(symbol, str):
            symbol = "UNKNOWN"

        scout_mod = _safe_float(getattr(scout, "scout_modifier", 0.0), 0.0)
        rvol = _safe_float(getattr(scout, "rvol", 1.0), 1.0)
        price_change_pct = _safe_float(getattr(scout, "price_change_pct", 0.0), 0.0)

        tech_score = _safe_float(getattr(tech, "technical_score", 0.0), 0.0)
        target_spot = _safe_float(getattr(tech, "suggested_spot_target", 0.0), 0.0)
        rr_ratio = _safe_float(getattr(tech, "risk_reward_ratio", 1.5), 1.5)

        rsi = 50.0
        if hasattr(tech, "momentum"):
            rsi = _safe_float(getattr(tech.momentum, "rsi", 50.0), 50.0)

        patterns = getattr(tech, "patterns_detected", [])
        if not isinstance(patterns, list):
            patterns = []

        news_sentiment = _safe_float(getattr(news, "news_sentiment_score", 5.0), 5.0)
        market_regime = getattr(news, "market_regime", "rangebound")
        if not isinstance(market_regime, str):
            market_regime = "rangebound"

        news_catalysts = getattr(news, "catalyst_events", [])
        if not isinstance(news_catalysts, list):
            news_catalysts = []

        args: List[str] = []

        if rvol >= 1.2:
            args.append(f"High Relative Volume spike (RVOL {rvol:.2f}x) indicating institutional accumulation.")
        if price_change_pct > 0:
            args.append(f"Positive momentum change (+{price_change_pct:.2f}% spot price move).")

        if tech_score > 0:
            args.append(f"Bullish technical score (+{tech_score:.2f}) with EMA/Supertrend alignment.")
        if 45 < rsi < 70:
            args.append(f"RSI in healthy bullish expansion zone ({rsi:.1f}).")
        
        for p in patterns:
            if isinstance(p, str) and any(w in p for w in ["Bullish", "Morning", "Soldiers", "Breakout", "Hammer", "Engulfing"]):
                args.append(f"Chart Pattern: {p}")

        if news_sentiment > 5.0:
            args.append(f"Positive news sentiment ({news_sentiment:.1f}/10).")
        if market_regime == "bullish":
            args.append("Macro regime favors risk-on upside expansion.")

        if not args:
            args.append("Base upside continuation potential.")

        scout_part = max(0.0, min(10.0, 5.0 + (scout_mod * 5.0)))
        tech_part = max(0.0, min(10.0, 5.0 + (tech_score * 1.8)))
        news_part = max(0.0, min(10.0, news_sentiment))

        conviction = round((scout_part * 0.30) + (tech_part * 0.50) + (news_part * 0.20), 2)
        conviction = max(0.0, min(10.0, conviction))

        target_rationale = (
            f"Target projected at ₹{target_spot:.2f} based on technical pattern expansion "
            f"and R:R ratio {rr_ratio:.2f}:1."
        ) if target_spot > 0 else "Target projected at upside ATR expansion level."

        catalysts = list(news_catalysts) if news_catalysts else ["Upcoming earnings / momentum breakout"]
        stance = "strong_bullish" if conviction >= 7.5 else ("bullish" if conviction >= 5.5 else "cautious_bullish")

        return BullDebaterOutput(
            ticker=ticker,
            symbol=symbol,
            conviction_score=conviction,
            upside_arguments=args,
            target_rationale=target_rationale,
            key_catalysts=catalysts,
            suggested_target_multiplier=1.05,
            stance=stance
        )
