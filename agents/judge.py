import math
import logging
from datetime import datetime, timezone
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

def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            return float(val)
        if isinstance(val, str):
            return float(val)
        return default
    except Exception:
        return default

class FOJudgeAgent:
    """
    F&O Judge Agent executing 3-Way Risk Committee Debate Protocol:
    Combines Scout, Technician, Newsdesk, Bull Debater, and Bear Debater stances
    into a Consensus Score, Fact-Checker Approval, and Risk Override status.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}
        self.options_engine = OptionsEngine()
        self.brokerage_fee = _safe_float(
            self.config.get("capital", {}).get("brokerage_per_order_inr", 20.0), 20.0
        )
        self.newsdesk = NewsdeskAgent(self.config)
        self.bull_debater = BullDebaterAgent(self.config)
        self.bear_debater = BearDebaterAgent(self.config)

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
        ticker = getattr(scout, "ticker", "UNKNOWN")
        symbol = getattr(scout, "symbol", "UNKNOWN")
        if not isinstance(ticker, str):
            ticker = "UNKNOWN"
        if not isinstance(symbol, str):
            symbol = "UNKNOWN"

        spot = _safe_float(getattr(scout, "spot_cmp", 0.0), 0.0)
        lot_size = int(_safe_float(getattr(scout, "lot_size", 1), 1))
        strike_step = _safe_float(getattr(scout, "strike_step", 50.0), 50.0)
        scout_mod = _safe_float(getattr(scout, "scout_modifier", 0.0), 0.0)

        tech_score_raw = _safe_float(getattr(tech, "technical_score", 0.0), 0.0)
        tech_stance = getattr(tech, "stance", "neutral")
        if not isinstance(tech_stance, str):
            tech_stance = "neutral"
        vix = _safe_float(getattr(tech, "vix", 14.5), 14.5)

        # 1. Obtain stances from Committee Debaters
        news_out = news or self.newsdesk.run(scout, vix_val=vix)
        bull_out = bull or self.bull_debater.run(scout, tech, news_out)
        bear_out = bear or self.bear_debater.run(scout, tech, news_out)

        scout_stance = "high_conviction" if scout_mod >= 0.5 else ("moderate" if scout_mod >= 0.3 else "neutral")
        news_stance = news_out.stance
        bull_stance = bull_out.stance
        bear_stance = bear_out.stance

        # 2. Consensus Score Calculation (0.0 to 10.0)
        scout_score = 5.0 + min(5.0, (scout_mod / 0.6) * 5.0) if scout_mod > 0 else 5.0
        
        if tech_stance == "bearish":
            directional_tech_score = 5.0 + (-tech_score_raw / 3.0) * 5.0
        else:
            directional_tech_score = 5.0 + (tech_score_raw / 3.0) * 5.0
        directional_tech_score = max(0.0, min(10.0, directional_tech_score))

        bull_part = bull_out.conviction_score if tech_stance != "bearish" else (10.0 - bear_out.bear_risk_score)
        bear_part = (10.0 - bear_out.bear_risk_score) if tech_stance != "bearish" else bear_out.bear_risk_score

        consensus_score = (
            0.20 * scout_score +
            0.40 * directional_tech_score +
            0.10 * news_out.news_sentiment_score +
            0.15 * bull_part +
            0.15 * bear_part
        )
        consensus_score = max(0.0, min(10.0, round(consensus_score, 2)))
        waterfall_score = consensus_score

        # 3. Fact-Checker Approval Protocol
        fact_checker_approved = True
        fact_check_reason = ""
        
        if spot <= 0 or lot_size <= 0:
            fact_checker_approved = False
            fact_check_reason = f"Invalid pricing data: spot={spot}, lot_size={lot_size}."
        
        sl_val = getattr(tech, "suggested_spot_sl", None)
        target_val = getattr(tech, "suggested_spot_target", None)
        rr_val = getattr(tech, "risk_reward_ratio", None)

        if sl_val is not None and not isinstance(sl_val, type(NotImplemented)):
            sl_num = _safe_float(sl_val, -1.0)
            target_num = _safe_float(target_val, -1.0)
            if sl_num == 0.0 or target_num == 0.0:
                fact_checker_approved = False
                fact_check_reason = f"Invalid SL/Target levels: SL={sl_num}, Target={target_num}."

        if rr_val is not None and not isinstance(rr_val, type(NotImplemented)):
            rr_num = _safe_float(rr_val, 1.5)
            if rr_num < 1.0 and fact_checker_approved:
                fact_checker_approved = False
                fact_check_reason = f"Risk-Reward Ratio too low: {rr_num:.2f} < 1.0."

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
            if tech_stance != "bearish" and bull_out.conviction_score >= bear_out.bear_risk_score:
                verdict = "SCALP_CE" if timeframe in ["1m", "5m"] else "BUY_CE"
            else:
                verdict = "SCALP_PE" if timeframe in ["1m", "5m"] else "BUY_PE"
            reasoning = f"Consensus Approved ({consensus_score}/10): Bull Conviction {bull_out.conviction_score:.1f} vs Bear Risk {bear_out.bear_risk_score:.1f}."
        elif tech_stance == "bearish" and (10.0 - bear_out.bear_risk_score) >= 4.0 and consensus_score >= (execute_thresh - 1.5):
            verdict = "SCALP_PE" if timeframe in ["1m", "5m"] else "BUY_PE"
            reasoning = f"Bearish Downside Consensus Approved ({consensus_score}/10)."
        else:
            verdict = "AVOID"
            reasoning = f"Consensus score {consensus_score}/10 below execution threshold {execute_thresh}."

        effective_state = state or {}
        pool_total = _safe_float(effective_state.get("pool_total", 500000.0), 500000.0)
        pool_avail = _safe_float(effective_state.get("pool_available", pool_total), pool_total)
        now_dt = datetime.now(timezone.utc)

        if verdict == "AVOID":
            dummy_contract = FOContractData(
                contract_type="NONE", symbol=symbol, strike_price=spot, expiry_dte=7,
                lot_size=lot_size, lots_qty=0, total_shares=0, option_premium=0.0,
                delta=0.5, gamma=0.0, theta_per_day=0.0, vega=0.0, premium_value_inr=0.0,
                estimated_total_cost_inr=0.0, spot_entry=round(spot, 2)
            )

            record = CommitteeDebateRecord(
                timestamp=now_dt.isoformat(), symbol=symbol, ticker=ticker,
                scout_stance=scout_stance, tech_stance=tech_stance, news_stance=news_stance,
                bull_stance=bull_stance, bear_stance=bear_stance, consensus_score=consensus_score,
                fact_checker_approved=fact_checker_approved, risk_override_status=risk_override_status,
                judge_verdict=verdict, reasoning=reasoning
            )
            append_to_committee_debate_log(record)

            return FOJudgeOutput(
                ticker=ticker, run_timestamp=now_dt, verdict="AVOID",
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
                timestamp=now_dt.isoformat(), symbol=symbol, ticker=ticker,
                scout_stance=scout_stance, tech_stance=tech_stance, news_stance=news_stance,
                bull_stance=bull_stance, bear_stance=bear_stance, consensus_score=consensus_score,
                fact_checker_approved=True, risk_override_status=risk_override_status,
                judge_verdict=verdict, reasoning=reasoning
            )
            append_to_committee_debate_log(record)

            return FOJudgeOutput(
                ticker=ticker, run_timestamp=now_dt, verdict="AVOID",
                waterfall_score=consensus_score, confidence=consensus_score,
                contract=dummy_contract, position_sizing_inr=0.0, reasoning=reasoning,
                consensus_score=consensus_score, fact_checker_approved=True,
                risk_override_status=risk_override_status, scout_stance=scout_stance,
                tech_stance=tech_stance, news_stance=news_stance, bull_stance=bull_stance,
                bear_stance=bear_stance
            )

        record = CommitteeDebateRecord(
            timestamp=now_dt.isoformat(),
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
            run_timestamp=now_dt,
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
