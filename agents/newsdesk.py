import logging
from typing import Dict, Any, List, Optional
import yfinance as yf
from core.schemas import FOScoutOutput, NewsdeskOutput

logger = logging.getLogger(__name__)

class NewsdeskAgent:
    """
    Newsdesk Agent calculating news sentiment, catalyst risk, market regime, and macro risk scores (0.0 to 10.0) with fallback.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}

    def run(self, candidate: FOScoutOutput, vix_val: float = 14.5) -> NewsdeskOutput:
        ticker = getattr(candidate, "ticker", "UNKNOWN")
        symbol = getattr(candidate, "symbol", "UNKNOWN")
        price_change = float(getattr(candidate, "price_change_pct", 0.0))
        
        sentiment_score = 5.0
        catalyst_risk = 3.0
        macro_risk = 4.0
        market_regime = "rangebound"
        headlines: List[str] = []
        catalysts: List[str] = []

        try:
            # Macro risk & Market regime evaluation via VIX & spot price change
            vix_num = float(vix_val) if isinstance(vix_val, (int, float)) else 14.5
            if vix_num >= 22.0:
                market_regime = "volatile"
                macro_risk = 7.5
                catalyst_risk = 6.5
            elif vix_num <= 12.0:
                market_regime = "bullish"
                macro_risk = 2.5
                catalyst_risk = 2.0
            elif price_change >= 1.0:
                market_regime = "bullish"
                macro_risk = 3.5
            elif price_change <= -1.0:
                market_regime = "bearish"
                macro_risk = 6.0
            else:
                market_regime = "rangebound"

            # Fetch news items safely
            yf_ticker = yf.Ticker(ticker)
            news_items = getattr(yf_ticker, "news", [])
            
            if news_items and isinstance(news_items, list):
                pos_words = {"profit", "surge", "growth", "bull", "upgrade", "record", "beat", "rally", "gain", "high"}
                neg_words = {"loss", "drop", "fall", "bear", "downgrade", "slash", "miss", "plunge", "risk", "penalty"}
                
                bull_count = 0
                bear_count = 0
                
                for item in news_items[:5]:
                    title = ""
                    if isinstance(item, dict):
                        title = item.get("title", "") or item.get("headline", "")
                    elif isinstance(item, str):
                        title = item
                    
                    if title:
                        title_lower = title.lower()
                        headlines.append(title[:80])
                        for w in pos_words:
                            if w in title_lower:
                                bull_count += 1
                        for w in neg_words:
                            if w in title_lower:
                                bear_count += 1
                
                total_hits = bull_count + bear_count
                if total_hits > 0:
                    sentiment_score = round(5.0 + ((bull_count - bear_count) / total_hits) * 3.0, 2)
                    sentiment_score = max(0.0, min(10.0, sentiment_score))
                
                if bear_count > bull_count:
                    catalysts.append(f"Negative news bias detected ({bear_count} risk headlines)")
                    catalyst_risk += 1.5

        except Exception as e:
            logger.warning(f"[NewsdeskAgent] Fallback applied for {symbol}: {e}")
            headlines = [f"Standard market scan for {symbol} (News fallback active)"]

        overall_news_score = round((sentiment_score * 0.5) + ((10.0 - catalyst_risk) * 0.3) + ((10.0 - macro_risk) * 0.2), 2)
        overall_news_score = max(0.0, min(10.0, overall_news_score))

        stance = "bullish" if sentiment_score >= 6.0 and catalyst_risk < 6.0 else (
            "bearish" if sentiment_score <= 4.0 or catalyst_risk >= 7.0 else "neutral"
        )

        return NewsdeskOutput(
            ticker=ticker,
            symbol=symbol,
            news_sentiment_score=sentiment_score,
            catalyst_risk_score=round(catalyst_risk, 2),
            market_regime=market_regime,
            macro_risk_score=round(macro_risk, 2),
            overall_news_score=overall_news_score,
            stance=stance,
            headline_summaries=headlines[:3],
            catalyst_events=catalysts
        )
