import math
import logging
from datetime import datetime
from typing import Dict, Any
from core.options_engine import OptionsEngine
from core.schemas import FOScoutOutput, FOTechnicianOutput, FOJudgeOutput, FOContractData

logger = logging.getLogger(__name__)

class FOJudgeAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.options_engine = OptionsEngine()
        self.brokerage_fee = config.get("capital", {}).get("brokerage_per_order_inr", 20.0)

    def run(self, scout: FOScoutOutput, tech: FOTechnicianOutput, state: Dict[str, Any]) -> FOJudgeOutput:
        ticker = scout.ticker
        symbol = scout.symbol
        spot = scout.spot_cmp
        lot_size = scout.lot_size
        strike_step = scout.strike_step
        vix = tech.vix

        # Waterfall Score
        base_score = 5.0
        scout_mod = float(scout.scout_modifier)
        tech_mod = float(tech.technical_score)
        
        waterfall_score = base_score + (scout_mod * 1.0) + (tech_mod * 1.8)
        waterfall_score = max(0.0, min(10.0, waterfall_score))

        pool_total = float(state.get("pool_total", 500000.0))
        pool_avail = float(state.get("pool_available", pool_total))
        risk_pct = float(self.config.get("risk", {}).get("risk_pct_per_trade", 2.0))
        risk_amount = pool_total * (risk_pct / 100.0)  # ₹10,000 max risk per trade

        # Verdict Determination
        execute_thresh = 8.0
        if waterfall_score >= execute_thresh:
            verdict = "BUY_CE" if tech.stance != "bearish" else "BUY_PE"
        elif waterfall_score <= (10.0 - execute_thresh) or tech.stance == "bearish":
            # For bearish stance, calculate short/put waterfall score
            short_waterfall = base_score - (scout_mod * 1.0) - (tech_mod * 1.8)
            short_waterfall = max(0.0, min(10.0, short_waterfall))
            if short_waterfall >= execute_thresh:
                verdict = "BUY_PE"
                waterfall_score = short_waterfall
            else:
                verdict = "AVOID"
        else:
            verdict = "AVOID"

        if verdict not in ["BUY_CE", "BUY_PE"]:
            dummy_contract = FOContractData(
                contract_type="NONE", symbol=symbol, strike_price=spot, expiry_dte=7,
                lot_size=lot_size, lots_qty=0, total_shares=0, option_premium=0.0,
                delta=0.5, gamma=0.0, theta_per_day=0.0, vega=0.0, premium_value_inr=0.0,
                estimated_total_cost_inr=0.0
            )
            return FOJudgeOutput(
                ticker=ticker, run_timestamp=datetime.utcnow(), verdict="AVOID",
                waterfall_score=round(waterfall_score, 2), confidence=round(waterfall_score, 2),
                contract=dummy_contract, position_sizing_inr=0.0, reasoning="Waterfall score below execution threshold (8.0)."
            )

        # F&O Strike Selection & Option Premium Calculation
        option_type = "CE" if verdict == "BUY_CE" else "PE"
        strike = self.options_engine.select_strike(spot, strike_step, stance="bullish" if option_type == "CE" else "bearish", itm_depth=1)
        dte = 7  # Standard 7 DTE near-month contract

        bs_res = self.options_engine.calculate_bs_price_and_greeks(spot, strike, dte, vix, option_type=option_type)
        premium = bs_res["price"]
        
        # Calculate Number of Lots based on ₹10,000 risk allocation
        cost_per_lot = premium * lot_size
        max_position_val = min(pool_avail * 0.20, pool_total * 0.20)  # Max 20% of pool per trade (₹1,00,000)
        
        lots = max(1, math.floor(max_position_val / cost_per_lot)) if cost_per_lot > 0 else 1
        total_shares = lots * lot_size
        total_premium_val = premium * total_shares

        # Cost Breakdown (Brokerage ₹20 flat + STT + Exchange fees)
        costs = self.options_engine.calculate_trade_costs(total_premium_val, is_sell=False, contract_type="OPTION")
        total_cost = costs["total_cost"]

        contract = FOContractData(
            contract_type=f"OPTION_{option_type}",
            symbol=symbol,
            strike_price=strike,
            expiry_dte=dte,
            lot_size=lot_size,
            lots_qty=lots,
            total_shares=total_shares,
            option_premium=premium,
            delta=bs_res["delta"],
            gamma=bs_res["gamma"],
            theta_per_day=bs_res["theta_per_day"],
            vega=bs_res["vega"],
            premium_value_inr=round(total_premium_val, 2),
            estimated_brokerage_inr=self.brokerage_fee,
            estimated_total_cost_inr=round(total_cost, 2)
        )

        return FOJudgeOutput(
            ticker=ticker,
            run_timestamp=datetime.utcnow(),
            verdict=verdict,
            waterfall_score=round(waterfall_score, 2),
            confidence=round(waterfall_score, 2),
            contract=contract,
            position_sizing_inr=round(total_premium_val + total_cost, 2),
            reasoning=f"Approved {verdict} for {symbol} {strike} {option_type} @ premium ₹{premium} ({lots} Lots, Brokerage ₹20)."
        )
