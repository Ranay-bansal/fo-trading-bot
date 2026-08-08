import logging
from typing import Dict, Any, List
from core.schemas import FOScoutOutput, FOTechnicianOutput, NewsdeskOutput, BearDebaterOutput

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

class BearDebaterAgent:
    """
    Bear Debater Agent formulating downside counter-arguments, bear risk score, stop-loss risks, and market headwinds.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}

    def run(self, scout: FOScoutOutput, tech: FOTechnicianOutput, news: NewsdeskOutput) -> BearDebaterOutput:
        ticker = getattr(scout, "ticker", "UNKNOWN")
        symbol = getattr(scout, "symbol", "UNKNOWN")
        if not isinstance(ticker, str):
            ticker = "UNKNOWN"
        if not isinstance(symbol, str):
            symbol = "UNKNOWN"

        tech_score = _safe_float(getattr(tech, "technical_score", 0.0), 0.0)
        entry_spot = _safe_float(getattr(tech, "suggested_spot_entry", 0.0), 0.0)
        sl_spot = _safe_float(getattr(tech, "suggested_spot_sl", 0.0), 0.0)
        support = _safe_float(getattr(tech, "support", 0.0), 0.0)
        vix = _safe_float(getattr(tech, "vix", 14.5), 14.5)

        rsi = 50.0
        if hasattr(tech, "momentum"):
            rsi = _safe_float(getattr(tech.momentum, "rsi", 50.0), 50.0)

        atr = 0.0
        if hasattr(tech, "volatility"):
            atr = _safe_float(getattr(tech.volatility, "atr", 0.0), 0.0)

        catalyst_risk = _safe_float(getattr(news, "catalyst_risk_score", 3.0), 3.0)
        macro_risk = _safe_float(getattr(news, "macro_risk_score", 4.0), 4.0)
        news_sentiment = _safe_float(getattr(news, "news_sentiment_score", 5.0), 5.0)

        downside_args: List[str] = []
        headwinds: List[str] = []

        if rsi > 70:
            downside_args.append(f"Overbought RSI ({rsi:.1f}) vulnerable to sharp mean reversion.")
        if tech_score < 0:
            downside_args.append(f"Bearish technical alignment ({tech_score:.2f}) with Supertrend breakdown.")
        if entry_spot > 0 and support > 0 and entry_spot < support * 1.01:
            downside_args.append("Trading dangerously close to primary support level with breakdown risk.")

        if catalyst_risk >= 6.0:
            headwinds.append(f"High catalyst risk ({catalyst_risk:.1f}/10) ahead of market events.")
        if macro_risk >= 6.0:
            headwinds.append(f"Elevated macro risk score ({macro_risk:.1f}/10) and VIX volatility ({vix:.1f}).")
        if news_sentiment < 5.0:
            downside_args.append(f"Negative news sentiment bias ({news_sentiment:.1f}/10).")

        if not downside_args:
            downside_args.append("Standard intraday market slippage and volatility risk.")

        tech_bear = max(0.0, (-tech_score / 3.0) * 10.0)
        news_bear = 10.0 - news_sentiment
        cat_bear = catalyst_risk

        bear_risk = round((tech_bear * 0.40) + (news_bear * 0.30) + (cat_bear * 0.30), 2)
        bear_risk = max(0.0, min(10.0, bear_risk))

        stop_loss_risks = (
            f"Stop-loss set at ₹{sl_spot:.2f}. "
            f"Risk of stop hunting / slippage if volatility surges beyond ATR {atr:.2f}."
        ) if sl_spot > 0 else "Standard stop-loss risk from volatility expansion."

        stance = "high_bear_risk" if bear_risk >= 7.0 else ("moderate_risk" if bear_risk >= 4.0 else "low_risk")

        return BearDebaterOutput(
            ticker=ticker,
            symbol=symbol,
            bear_risk_score=bear_risk,
            downside_arguments=downside_args,
            stop_loss_risks=stop_loss_risks,
            market_headwinds=headwinds or ["General market volatility"],
            suggested_sl_buffer_pct=0.015,
            stance=stance
        )
