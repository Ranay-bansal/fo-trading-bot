import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from core.data_sources import yfinanceWrapper
from core.state import save_fo_state, append_to_fo_trade_log
from core.schemas import FOJudgeOutput
from core.options_engine import OptionsEngine

logger = logging.getLogger(__name__)

class FOExecutorAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.options_engine = OptionsEngine()
        self.brokerage_per_order = config.get("capital", {}).get("brokerage_per_order_inr", 20.0)

    def execute(self, verdict: FOJudgeOutput, state: Dict[str, Any]) -> bool:
        if verdict.verdict == "AVOID":
            return False

        contract = verdict.contract
        ticker = verdict.ticker
        symbol = contract.symbol
        c_type = contract.contract_type
        strike = contract.strike_price
        lots = contract.lots_qty
        total_shares = contract.total_shares
        premium = contract.option_premium
        premium_val = contract.premium_value_inr
        brokerage = contract.estimated_brokerage_inr
        total_cost = contract.estimated_total_cost_inr

        total_cash_required = premium_val + total_cost
        if state["pool_available"] < total_cash_required:
            logger.warning(f"[F&O Executor] Insufficient funds for {ticker} {c_type}: Required ₹{total_cash_required:.2f}, Avail ₹{state['pool_available']:.2f}")
            return False

        logger.info(f"[F&O EXECUTOR] Executing {verdict.verdict} ({c_type}) for {symbol} {strike}: {lots} Lots ({total_shares} shares) @ Premium ₹{premium}. Brokerage: ₹{brokerage}")

        # Deduct capital & brokerage fee
        state["pool_available"] -= total_cash_required
        state["pool_deployed"] += premium_val
        state["total_brokerage_paid_inr"] += brokerage
        state["trades_today"] += 1

        run_id = f"{symbol}_{c_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        new_position = {
            "ticker": ticker,
            "contract_type": c_type,
            "symbol": symbol,
            "strike_price": strike,
            "lots": lots,
            "total_shares": total_shares,
            "entry_premium": premium,
            "entry_spot": verdict.position_sizing_inr,
            "sl_spot": verdict.position_sizing_inr * 0.985,
            "target_spot": verdict.position_sizing_inr * 1.03,
            "entered_at": datetime.utcnow().isoformat() + "Z",
            "megabull_order_id": run_id,
            "brokerage_paid_inr": brokerage
        }
        state["open_positions"].append(new_position)
        save_fo_state(state)

        # Append to F&O CSV Trade Log
        log_row = {
            "run_id": run_id,
            "ticker": ticker,
            "symbol": symbol,
            "verdict": verdict.verdict,
            "contract_type": c_type,
            "strike_price": strike,
            "lots": lots,
            "total_shares": total_shares,
            "spot_entry": verdict.position_sizing_inr,
            "option_premium": premium,
            "spot_sl": round(verdict.position_sizing_inr * 0.985, 2),
            "spot_target": round(verdict.position_sizing_inr * 1.03, 2),
            "waterfall_score": verdict.waterfall_score,
            "position_value_inr": premium_val,
            "brokerage_fee_inr": brokerage,
            "total_cost_inr": total_cost,
            "executed_at": datetime.utcnow().isoformat() + "Z"
        }
        append_to_fo_trade_log(log_row)
        return True

    def monitor_positions(self, state: Dict[str, Any]) -> None:
        open_positions = state.get("open_positions", [])
        if not open_positions:
            return

        ist_tz = timezone(timedelta(hours=5, minutes=30))
        now_ist = datetime.now(ist_tz)
        if now_ist.weekday() < 5 and (now_ist.hour > 15 or (now_ist.hour == 15 and now_ist.minute >= 15)):
            logger.info("[F&O Executor] 3:15 PM IST Auto Square-Off triggered. Closing all open F&O positions...")
            self.squareoff_all(state)

    def squareoff_all(self, state: Dict[str, Any]) -> None:
        open_positions = state.get("open_positions", [])
        if not open_positions:
            return

        for pos in open_positions:
            symbol = pos["symbol"]
            c_type = pos["contract_type"]
            total_shares = int(pos["total_shares"])
            entry_premium = float(pos["entry_premium"])
            
            exit_premium = round(entry_premium * 1.03, 2)
            exit_val = exit_premium * total_shares
            entry_val = entry_premium * total_shares
            
            exit_brokerage = self.brokerage_per_order
            gross_pnl = exit_val - entry_val
            net_pnl = gross_pnl - exit_brokerage
            pnl_pct = (net_pnl / entry_val) * 100.0 if entry_val > 0 else 0.0

            state["pool_deployed"] -= entry_val
            state["pool_available"] += entry_val + net_pnl
            state["daily_pnl_inr"] += net_pnl
            state["total_brokerage_paid_inr"] += exit_brokerage

            logger.info(f"[F&O Executor] Square-Off {symbol} {c_type}: Net P&L ₹{net_pnl:.2f} ({pnl_pct:.2f}%). Brokerage paid: ₹{exit_brokerage}")

        state["open_positions"] = []
        save_fo_state(state)
