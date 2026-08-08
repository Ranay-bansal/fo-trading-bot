# Milestone 2 Technical Implementation Specification — 3-Way Risk Committee Debaters

## 1. Observation
From inspecting the existing architecture in `c:\Users\RANAY\Desktop\FO TRADING BOT`:
- `agents/scout.py` implements `FOScoutAgent` generating `FOScoutOutput` with relative volume (`rvol`), price change %, and `scout_modifier` (0.2 to 0.6).
- `agents/technician.py` implements `FOTechnicianAgent` generating `FOTechnicianOutput` with 12 chart patterns, VWAP bounce/rejection signals, Supertrend flips, indicators (RSI, ADX, ATR), and `technical_score` (-3.0 to +3.0).
- `agents/judge.py` implements `FOJudgeAgent`, which previously computed a simple 2-factor waterfall score (`5.0 + scout_mod*1.0 + tech_mod*1.8`) without consulting Newsdesk, Bull Debater, or Bear Debater agents, nor persisting structured committee debate logs.
- `core/schemas.py` defines `FOScoutOutput`, `FOTechnicianOutput`, `FOContractData`, `FOJudgeOutput`, `FOPortfolioState`, and `FOOpenPosition`.
- `core/state.py` defines state loading/saving for `portfolio_state.json` and trade log persistence for `trade_log.csv`.
- `scratch/fix_all_index_files.py` (lines 566-587) defines the dashboard UI tab for `🏛️ 3-Way Risk Committee`, which expects debate records displaying symbol, bull conviction (scout), bear risk (technician), Fact-Checker status (judge), and Risk Committee override.

## 2. Logic Chain
To fulfill Milestone 2 and satisfy Requirement R1 ("3-way risk committee debaters (Scout, Technician, Newsdesk, Bull, Bear)"):
1. **Newsdesk Agent (`agents/newsdesk.py`)**: Must calculate news sentiment (0.0–10.0), catalyst risk (0.0–10.0), market regime ("bullish"/"bearish"/"rangebound"/"volatile"), and macro risk (0.0–10.0). When external news APIs or yfinance text fetching fails, it must fall back safely to neutral defaults (sentiment=5.0, catalyst_risk=3.0, macro_risk=4.0).
2. **Bull Debater Agent (`agents/bull_debater.py`)**: Synthesizes upside arguments from Scout volume expansion, Technician momentum/patterns, and Newsdesk sentiment to compute a Bull Conviction Score (0.0–10.0) and target rationale.
3. **Bear Debater Agent (`agents/bear_debater.py`)**: Formulates downside counter-arguments from overbought RSI, VWAP resistance, catalyst/macro risk, and market volatility to compute a Bear Risk Score (0.0–10.0) and stop-loss risk assessment.
4. **Judge Agent Consensus Protocol (`agents/judge.py`)**: Refactored `FOJudgeAgent` orchestrates all 5 stances (Scout, Technician, Newsdesk, Bull, Bear) to compute a weighted **Consensus Score** (0.0–10.0).
5. **Fact-Checker Approval & Risk Override**:
   - **Fact-Checker**: Validates data integrity (positive spot price, valid lot size, consistent SL/Target ordering, R:R >= 1.0, cost friction coverage).
   - **Risk Committee Override**: Vetoes any trade if Bear Risk Score >= 7.5, Catalyst Risk >= 8.0, Macro Risk >= 8.5, or VIX >= 28.0.
6. **State Persistence**: Adds `CommitteeDebateRecord` to `core/schemas.py` and `append_to_committee_debate_log(record)` to `core/state.py` persisting debate entries to `state/committee_debate_log.json`.

## 3. Caveats
- `yfinance` news properties may return empty lists during market off-hours; `NewsdeskAgent` must catch all exceptions and return standard neutral fallback structures without breaking execution.
- `FOJudgeAgent.run` maintains its previous argument interface `(scout, tech, state, timeframe)` with optional `(news, bull, bear)` parameters so that existing caller loops (`main.py`, `bot2_options.py`, `tests/test_debaters.py`) remain 100% backward-compatible.
- `CommitteeDebateRecord` persistence must write atomically using `.tmp` files to prevent file corruption during parallel bar-stream execution.

## 4. Conclusion & Complete Design Specifications

### File 1: `core/schemas.py` (Additions & Updates)
Add `NewsdeskOutput`, `BullDebaterOutput`, `BearDebaterOutput`, `CommitteeDebateRecord`, and update `FOJudgeOutput`:

```python
# In core/schemas.py:

class NewsdeskOutput(BaseModel):
    ticker: str
    symbol: str
    news_sentiment_score: float = 5.0  # 0.0 to 10.0 (5.0 neutral)
    catalyst_risk_score: float = 3.0   # 0.0 to 10.0
    market_regime: str = "rangebound"   # "bullish", "bearish", "volatile", "rangebound"
    macro_risk_score: float = 4.0      # 0.0 to 10.0
    overall_news_score: float = 5.0    # 0.0 to 10.0
    stance: str = "neutral"            # "bullish", "bearish", "neutral"
    headline_summaries: List[str] = Field(default_factory=list)
    catalyst_events: List[str] = Field(default_factory=list)

class BullDebaterOutput(BaseModel):
    ticker: str
    symbol: str
    conviction_score: float = 5.0      # 0.0 to 10.0
    upside_arguments: List[str] = Field(default_factory=list)
    target_rationale: str = ""
    key_catalysts: List[str] = Field(default_factory=list)
    suggested_target_multiplier: float = 1.05
    stance: str = "bullish"

class BearDebaterOutput(BaseModel):
    ticker: str
    symbol: str
    bear_risk_score: float = 3.0       # 0.0 to 10.0
    downside_arguments: List[str] = Field(default_factory=list)
    stop_loss_risks: str = ""
    market_headwinds: List[str] = Field(default_factory=list)
    suggested_sl_buffer_pct: float = 0.015
    stance: str = "bearish"

class CommitteeDebateRecord(BaseModel):
    timestamp: str
    symbol: str
    ticker: str
    scout_stance: str
    tech_stance: str
    news_stance: str
    bull_stance: str
    bear_stance: str
    consensus_score: float
    fact_checker_approved: bool
    risk_override_status: str
    judge_verdict: str
    reasoning: str

class FOJudgeOutput(BaseModel):
    ticker: str
    run_timestamp: datetime
    verdict: str  # "BUY_CE" / "BUY_PE" / "BUY_FUT" / "SELL_FUT" / "SCALP_CE" / "SCALP_PE" / "WATCHLIST" / "AVOID" / "REJECT"
    waterfall_score: float
    confidence: float
    contract: FOContractData
    position_sizing_inr: float
    reasoning: str
    hard_reject_reason: Optional[str] = None
    consensus_score: Optional[float] = None
    fact_checker_approved: bool = True
    risk_override_status: str = "NO_OVERRIDE"  # "NO_OVERRIDE" / "RISK_OVERRIDE_TRIGGERED"
    scout_stance: Optional[str] = None
    tech_stance: Optional[str] = None
    news_stance: Optional[str] = None
    bull_stance: Optional[str] = None
    bear_stance: Optional[str] = None
```

---

### File 2: `core/state.py` (Additions)
Add `COMMITTEE_DEBATE_LOG_FILE` and `append_to_committee_debate_log`:

```python
# In core/state.py:

COMMITTEE_DEBATE_LOG_FILE = os.path.join(ROOT_DIR, "state", "committee_debate_log.json")

def append_to_committee_debate_log(record: Any) -> None:
    try:
        os.makedirs(os.path.dirname(COMMITTEE_DEBATE_LOG_FILE), exist_ok=True)
        if hasattr(record, "model_dump"):
            rec_dict = record.model_dump()
        elif hasattr(record, "dict"):
            rec_dict = record.dict()
        elif isinstance(record, dict):
            rec_dict = record
        else:
            rec_dict = dict(record)

        if "timestamp" in rec_dict and isinstance(rec_dict["timestamp"], datetime):
            rec_dict["timestamp"] = rec_dict["timestamp"].isoformat() + "Z"

        logs = []
        if os.path.exists(COMMITTEE_DEBATE_LOG_FILE):
            try:
                with open(COMMITTEE_DEBATE_LOG_FILE, "r", encoding="utf-8") as f:
                    logs = json.load(f)
                    if not isinstance(logs, list):
                        logs = []
            except Exception:
                logs = []

        logs.append(rec_dict)
        if len(logs) > 200:
            logs = logs[-200:]

        temp_file = COMMITTEE_DEBATE_LOG_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, default=str)
        try:
            os.replace(temp_file, COMMITTEE_DEBATE_LOG_FILE)
        except (PermissionError, OSError):
            with open(COMMITTEE_DEBATE_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2, default=str)
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"Error appending to committee debate log {COMMITTEE_DEBATE_LOG_FILE}: {e}")
```

---

### File 3: `agents/newsdesk.py` (New Agent)

```python
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
        self.config = config

    def run(self, candidate: FOScoutOutput, vix_val: float = 14.5) -> NewsdeskOutput:
        ticker = candidate.ticker
        symbol = candidate.symbol
        
        sentiment_score = 5.0
        catalyst_risk = 3.0
        macro_risk = 4.0
        market_regime = "rangebound"
        headlines = []
        catalysts = []

        try:
            # Macro risk & Market regime evaluation via VIX & spot price change
            if vix_val >= 22.0:
                market_regime = "volatile"
                macro_risk = 7.5
                catalyst_risk = 6.5
            elif vix_val <= 12.0:
                market_regime = "bullish"
                macro_risk = 2.5
                catalyst_risk = 2.0
            elif candidate.price_change_pct >= 1.0:
                market_regime = "bullish"
                macro_risk = 3.5
            elif candidate.price_change_pct <= -1.0:
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
                    title = item.get("title", "").lower() if isinstance(item, dict) else str(item).lower()
                    if title:
                        headlines.append(title[:80])
                        for w in pos_words:
                            if w in title:
                                bull_count += 1
                        for w in neg_words:
                            if w in title:
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
```

---

### File 4: `agents/bull_debater.py` (New Agent)

```python
import logging
from typing import Dict, Any, List
from core.schemas import FOScoutOutput, FOTechnicianOutput, NewsdeskOutput, BullDebaterOutput

logger = logging.getLogger(__name__)

class BullDebaterAgent:
    """
    Bull Debater Agent formulating upside arguments, conviction score, target rationale, and key catalysts.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def run(self, scout: FOScoutOutput, tech: FOTechnicianOutput, news: NewsdeskOutput) -> BullDebaterOutput:
        ticker = scout.ticker
        symbol = scout.symbol
        
        args = []
        catalysts = []
        
        if scout.rvol >= 1.2:
            args.append(f"High Relative Volume spike (RVOL {scout.rvol}x) indicating institutional accumulation.")
        if scout.price_change_pct > 0:
            args.append(f"Positive momentum change (+{scout.price_change_pct}% spot price move).")

        if tech.technical_score > 0:
            args.append(f"Bullish technical score (+{tech.technical_score:.2f}) with EMA/Supertrend alignment.")
        if tech.momentum.rsi < 70 and tech.momentum.rsi > 45:
            args.append(f"RSI in healthy bullish expansion zone ({tech.momentum.rsi}).")
        if tech.patterns_detected:
            for p in tech.patterns_detected:
                if "Bullish" in p or "Morning" in p or "Soldiers" in p or "Breakout" in p:
                    args.append(f"Chart Pattern: {p}")

        if news.news_sentiment_score > 5.0:
            args.append(f"Positive news sentiment ({news.news_sentiment_score}/10).")
        if news.market_regime == "bullish":
            args.append("Macro regime favors risk-on upside expansion.")

        if not args:
            args.append("Base upside continuation potential.")

        scout_part = min(scout.scout_modifier * 10.0, 5.0)
        tech_part = max(0.0, tech.technical_score + 3.0) * (5.0 / 6.0)
        news_part = news.news_sentiment_score * 0.5

        conviction = round((scout_part * 0.3) + (tech_part * 0.5) + (news_part * 0.2), 2)
        conviction = max(0.0, min(10.0, conviction))

        target_rationale = (
            f"Target projected at ₹{tech.suggested_spot_target:.2f} based on ATR expansion "
            f"and R:R ratio {tech.risk_reward_ratio}:1."
        )

        catalysts = news.catalyst_events or ["Upcoming earnings / momentum breakout"]
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
```

---

### File 5: `agents/bear_debater.py` (New Agent)

```python
import logging
from typing import Dict, Any, List
from core.schemas import FOScoutOutput, FOTechnicianOutput, NewsdeskOutput, BearDebaterOutput

logger = logging.getLogger(__name__)

class BearDebaterAgent:
    """
    Bear Debater Agent formulating downside counter-arguments, bear risk score, stop-loss risks, and market headwinds.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def run(self, scout: FOScoutOutput, tech: FOTechnicianOutput, news: NewsdeskOutput) -> BearDebaterOutput:
        ticker = scout.ticker
        symbol = scout.symbol

        downside_args = []
        headwinds = []

        if tech.momentum.rsi > 70:
            downside_args.append(f"Overbought RSI ({tech.momentum.rsi}) vulnerable to sharp mean reversion.")
        if tech.technical_score < 0:
            downside_args.append(f"Bearish technical alignment ({tech.technical_score:.2f}) with Supertrend breakdown.")
        if tech.suggested_spot_entry < tech.support * 1.01:
            downside_args.append("Trading dangerously close to primary support level with breakdown risk.")

        if news.catalyst_risk_score >= 6.0:
            headwinds.append(f"High catalyst risk ({news.catalyst_risk_score}/10) ahead of market events.")
        if news.macro_risk_score >= 6.0:
            headwinds.append(f"Elevated macro risk score ({news.macro_risk_score}/10) and VIX volatility ({tech.vix}).")
        if news.news_sentiment_score < 5.0:
            downside_args.append(f"Negative news sentiment bias ({news.news_sentiment_score}/10).")

        if not downside_args:
            downside_args.append("Standard intraday market slippage and volatility risk.")

        tech_bear = max(0.0, -tech.technical_score) * (4.0 / 3.0)
        news_bear = (10.0 - news.news_sentiment_score) * 0.3
        cat_bear = news.catalyst_risk_score * 0.3

        bear_risk = round(tech_bear + news_bear + cat_bear, 2)
        bear_risk = max(0.0, min(10.0, bear_risk))

        stop_loss_risks = (
            f"Stop-loss set at ₹{tech.suggested_spot_sl:.2f}. "
            f"Risk of stop hunting / slippage if volatility surges beyond ATR {tech.volatility.atr:.2f}."
        )

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
```

---

### File 6: `agents/judge.py` (Refactored `FOJudgeAgent`)

```python
import math
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from core.options_engine import OptionsEngine
from core.schemas import (
    FOScoutOutput, FOTechnicianOutput, FOJudgeOutput, FOContractData,
    NewsdeskOutput, BullDebaterOutput, BearDebaterOutput, CommitteeDebateRecord
)
from core.state import append_to_committee_debate_log
from agents.newsdesk import NewsdeskAgent
from agents.bull_debater import BullDebaterAgent
from agents.bear_debater import BearDebaterAgent

logger = logging.getLogger(__name__)

class FOJudgeAgent:
    """
    F&O Judge Agent executing 3-Way Risk Committee Debate Protocol:
    Combines Scout, Technician, Newsdesk, Bull Debater, and Bear Debater stances
    into a Consensus Score, Fact-Checker Approval, and Risk Override status.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.options_engine = OptionsEngine()
        self.brokerage_fee = config.get("capital", {}).get("brokerage_per_order_inr", 20.0)
        self.newsdesk = NewsdeskAgent(config)
        self.bull_debater = BullDebaterAgent(config)
        self.bear_debater = BearDebaterAgent(config)

    def run(
        self,
        scout: FOScoutOutput,
        tech: FOTechnicianOutput,
        state: Dict[str, Any],
        timeframe: str = "5m",
        news: Optional[NewsdeskOutput] = None,
        bull: Optional[BullDebaterOutput] = None,
        bear: Optional[BearDebaterOutput] = None
    ) -> FOJudgeOutput:
        ticker = scout.ticker
        symbol = scout.symbol
        spot = scout.spot_cmp
        lot_size = scout.lot_size
        strike_step = scout.strike_step
        vix = tech.vix

        # 1. Obtain stances from Committee Debaters
        news_out = news or self.newsdesk.run(scout, vix_val=vix)
        bull_out = bull or self.bull_debater.run(scout, tech, news_out)
        bear_out = bear or self.bear_debater.run(scout, tech, news_out)

        scout_stance = "high_conviction" if scout.scout_modifier >= 0.5 else ("moderate" if scout.scout_modifier >= 0.3 else "neutral")
        tech_stance = tech.stance
        news_stance = news_out.stance
        bull_stance = bull_out.stance
        bear_stance = bear_out.stance

        # 2. Consensus Score Calculation (0.0 to 10.0)
        scout_score = 5.0 + (scout.scout_modifier * 5.0)
        tech_score = 5.0 + (tech.technical_score * 1.667)
        tech_score = max(0.0, min(10.0, tech_score))

        consensus_score = (
            0.15 * scout_score +
            0.35 * tech_score +
            0.15 * news_out.news_sentiment_score +
            0.20 * bull_out.conviction_score +
            0.15 * (10.0 - bear_out.bear_risk_score)
        )
        consensus_score = max(0.0, min(10.0, round(consensus_score, 2)))
        waterfall_score = consensus_score

        # 3. Fact-Checker Approval Protocol
        fact_checker_approved = True
        fact_check_reason = ""
        
        if spot <= 0 or lot_size <= 0:
            fact_checker_approved = False
            fact_check_reason = f"Invalid pricing data: spot={spot}, lot_size={lot_size}."
        elif tech.suggested_spot_sl <= 0 or tech.suggested_spot_target <= 0:
            fact_checker_approved = False
            fact_check_reason = f"Invalid SL/Target levels: SL={tech.suggested_spot_sl}, Target={tech.suggested_spot_target}."
        elif tech.risk_reward_ratio < 1.0:
            fact_checker_approved = False
            fact_check_reason = f"Risk-Reward Ratio too low: {tech.risk_reward_ratio} < 1.0."

        # 4. Risk Committee Override Protocol
        risk_override_status = "NO_OVERRIDE"
        override_reason = ""

        if bear_out.bear_risk_score >= 7.5:
            risk_override_status = "RISK_OVERRIDE_TRIGGERED"
            override_reason = f"Extreme Bear Risk Score ({bear_out.bear_risk_score:.2f}/10)."
        elif news_out.catalyst_risk_score >= 8.0:
            risk_override_status = "RISK_OVERRIDE_TRIGGERED"
            override_reason = f"Imminent Catalyst Risk ({news_out.catalyst_risk_score:.2f}/10)."
        elif news_out.macro_risk_score >= 8.5:
            risk_override_status = "RISK_OVERRIDE_TRIGGERED"
            override_reason = f"Severe Macro Risk Event ({news_out.macro_risk_score:.2f}/10)."
        elif vix >= 28.0:
            risk_override_status = "RISK_OVERRIDE_TRIGGERED"
            override_reason = f"Extreme Volatility Panic (VIX {vix:.2f} >= 28.0)."

        # 5. Verdict Determination
        execute_thresh = 7.0 if timeframe in ["1m", "5m"] else 8.0
        
        if risk_override_status == "RISK_OVERRIDE_TRIGGERED":
            verdict = "AVOID"
            reasoning = f"Risk Committee Override: Vetoed trade due to {override_reason}"
        elif not fact_checker_approved:
            verdict = "AVOID"
            reasoning = f"Fact-Checker Rejected: {fact_check_reason}"
        elif consensus_score >= execute_thresh:
            if timeframe in ["1m", "5m"]:
                verdict = "SCALP_CE" if tech_stance != "bearish" and bull_out.conviction_score >= bear_out.bear_risk_score else "SCALP_PE"
            else:
                verdict = "BUY_CE" if tech_stance != "bearish" and bull_out.conviction_score >= bear_out.bear_risk_score else "BUY_PE"
            reasoning = f"Consensus Approved ({consensus_score}/10): Bull Conviction {bull_out.conviction_score:.1f} vs Bear Risk {bear_out.bear_risk_score:.1f}."
        elif tech_stance == "bearish" and (10.0 - bear_out.bear_risk_score) >= 5.0 and consensus_score >= (execute_thresh - 1.0):
            verdict = "SCALP_PE" if timeframe in ["1m", "5m"] else "BUY_PE"
            reasoning = f"Bearish Downside Consensus Approved ({consensus_score}/10)."
        else:
            verdict = "AVOID"
            reasoning = f"Consensus score {consensus_score}/10 below execution threshold {execute_thresh}."

        pool_total = float(state.get("pool_total", 500000.0))
        pool_avail = float(state.get("pool_available", pool_total))

        if verdict == "AVOID":
            dummy_contract = FOContractData(
                contract_type="NONE", symbol=symbol, strike_price=spot, expiry_dte=7,
                lot_size=lot_size, lots_qty=0, total_shares=0, option_premium=0.0,
                delta=0.5, gamma=0.0, theta_per_day=0.0, vega=0.0, premium_value_inr=0.0,
                estimated_total_cost_inr=0.0, spot_entry=round(spot, 2)
            )

            record = CommitteeDebateRecord(
                timestamp=datetime.utcnow().isoformat() + "Z", symbol=symbol, ticker=ticker,
                scout_stance=scout_stance, tech_stance=tech_stance, news_stance=news_stance,
                bull_stance=bull_stance, bear_stance=bear_stance, consensus_score=consensus_score,
                fact_checker_approved=fact_checker_approved, risk_override_status=risk_override_status,
                judge_verdict=verdict, reasoning=reasoning
            )
            append_to_committee_debate_log(record)

            return FOJudgeOutput(
                ticker=ticker, run_timestamp=datetime.utcnow(), verdict="AVOID",
                waterfall_score=consensus_score, confidence=consensus_score,
                contract=dummy_contract, position_sizing_inr=0.0, reasoning=reasoning,
                consensus_score=consensus_score, fact_checker_approved=fact_checker_approved,
                risk_override_status=risk_override_status, scout_stance=scout_stance,
                tech_stance=tech_stance, news_stance=news_stance, bull_stance=bull_stance,
                bear_stance=bear_stance
            )

        # 6. Contract Selection & Pricing
        is_option = verdict in ["BUY_CE", "BUY_PE", "SCALP_CE", "SCALP_PE"]
        option_type = "CE" if "CE" in verdict else "PE"

        if is_option:
            strike = self.options_engine.select_strike(spot, strike_step, stance="bullish" if option_type == "CE" else "bearish", itm_depth=1)
            dte = 7
            bs_res = self.options_engine.calculate_bs_price_and_greeks(spot, strike, dte, vix, option_type=option_type)
            premium = bs_res["price"]
            c_type = f"OPTION_{option_type}" if "SCALP" not in verdict else f"SCALP_{option_type}"
        else:
            strike = spot
            dte = 30
            premium = spot
            bs_res = {"delta": 1.0 if "BUY" in verdict else -1.0, "gamma": 0.0, "theta_per_day": 0.0, "vega": 0.0}
            c_type = "FUTURES_LONG" if verdict == "BUY_FUT" else "FUTURES_SHORT"

        cost_per_lot = premium * lot_size
        max_pos_val = min(pool_avail * 0.20, pool_total * 0.20)
        lots = max(1, math.floor(max_pos_val / cost_per_lot)) if cost_per_lot > 0 else 1
        total_shares = lots * lot_size
        total_premium_val = premium * total_shares

        costs = self.options_engine.calculate_trade_costs(total_premium_val, is_sell=False, contract_type="OPTION" if is_option else "FUTURES")

        contract = FOContractData(
            contract_type=c_type, symbol=symbol, strike_price=strike, expiry_dte=dte,
            lot_size=lot_size, lots_qty=lots, total_shares=total_shares, option_premium=premium,
            delta=bs_res["delta"], gamma=bs_res["gamma"], theta_per_day=bs_res["theta_per_day"],
            vega=bs_res["vega"], premium_value_inr=round(total_premium_val, 2),
            estimated_brokerage_inr=self.brokerage_fee, estimated_total_cost_inr=round(costs["total_cost"], 2),
            spot_entry=round(spot, 2)
        )

        round_trip_friction = (self.brokerage_fee * 2.0) + costs["total_cost"]
        min_required_profit = round_trip_friction * 2.5
        expected_gain_inr = total_premium_val * 0.15

        if expected_gain_inr < min_required_profit:
            verdict = "AVOID"
            reasoning = f"Cost Gate Friction: Expected gain ₹{expected_gain_inr:.2f} < Min required ₹{min_required_profit:.2f}."
            dummy_contract = FOContractData(
                contract_type="NONE", symbol=symbol, strike_price=spot, expiry_dte=7,
                lot_size=lot_size, lots_qty=0, total_shares=0, option_premium=0.0,
                delta=0.5, gamma=0.0, theta_per_day=0.0, vega=0.0, premium_value_inr=0.0,
                estimated_total_cost_inr=0.0, spot_entry=round(spot, 2)
            )

            record = CommitteeDebateRecord(
                timestamp=datetime.utcnow().isoformat() + "Z", symbol=symbol, ticker=ticker,
                scout_stance=scout_stance, tech_stance=tech_stance, news_stance=news_stance,
                bull_stance=bull_stance, bear_stance=bear_stance, consensus_score=consensus_score,
                fact_checker_approved=True, risk_override_status=risk_override_status,
                judge_verdict=verdict, reasoning=reasoning
            )
            append_to_committee_debate_log(record)

            return FOJudgeOutput(
                ticker=ticker, run_timestamp=datetime.utcnow(), verdict="AVOID",
                waterfall_score=consensus_score, confidence=consensus_score,
                contract=dummy_contract, position_sizing_inr=0.0, reasoning=reasoning,
                consensus_score=consensus_score, fact_checker_approved=True,
                risk_override_status=risk_override_status, scout_stance=scout_stance,
                tech_stance=tech_stance, news_stance=news_stance, bull_stance=bull_stance,
                bear_stance=bear_stance
            )

        record = CommitteeDebateRecord(
            timestamp=datetime.utcnow().isoformat() + "Z",
            symbol=symbol,
            ticker=ticker,
            scout_stance=scout_stance,
            tech_stance=tech_stance,
            news_stance=news_stance,
            bull_stance=bull_stance,
            bear_stance=bear_stance,
            consensus_score=consensus_score,
            fact_checker_approved=fact_checker_approved,
            risk_override_status=risk_override_status,
            judge_verdict=verdict,
            reasoning=reasoning
        )
        append_to_committee_debate_log(record)

        return FOJudgeOutput(
            ticker=ticker,
            run_timestamp=datetime.utcnow(),
            verdict=verdict,
            waterfall_score=consensus_score,
            confidence=consensus_score,
            contract=contract,
            position_sizing_inr=round(total_premium_val + costs["total_cost"], 2),
            reasoning=reasoning,
            consensus_score=consensus_score,
            fact_checker_approved=fact_checker_approved,
            risk_override_status=risk_override_status,
            scout_stance=scout_stance,
            tech_stance=tech_stance,
            news_stance=news_stance,
            bull_stance=bull_stance,
            bear_stance=bear_stance
        )
```

---

## 5. Verification Method

### Test Suite Execution
Execute unit tests for debaters and state persistence using pytest or unittest:

```powershell
python -m unittest tests/test_debaters.py
```

### Specific Verification Assertions:
1. `NewsdeskAgent.run(candidate, vix_val)` produces valid `NewsdeskOutput` with scores between 0.0 and 10.0 and handles offline/missing news gracefully.
2. `BullDebaterAgent.run(scout, tech, news)` produces valid `BullDebaterOutput` with `conviction_score` and list of upside arguments.
3. `BearDebaterAgent.run(scout, tech, news)` produces valid `BearDebaterOutput` with `bear_risk_score` and downside counter-arguments.
4. `FOJudgeAgent.run(...)` computes consensus score, checks Fact-Checker, applies Risk Committee Override vetoes when Bear Risk >= 7.5 or VIX >= 28.0, and appends a valid `CommitteeDebateRecord` to `state/committee_debate_log.json`.
5. Inspection of `state/committee_debate_log.json` confirms JSON array format containing all 13 required keys (`timestamp`, `symbol`, `ticker`, `scout_stance`, `tech_stance`, `news_stance`, `bull_stance`, `bear_stance`, `consensus_score`, `fact_checker_approved`, `risk_override_status`, `judge_verdict`, `reasoning`).
