import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union
from core.data_sources import yfinanceWrapper, BarEvent
from core.state import save_fo_state, append_to_fo_trade_log
from core.schemas import FOJudgeOutput, Bot1Signal
from core.options_engine import OptionsEngine

logger = logging.getLogger(__name__)

class FOExecutorAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.options_engine = OptionsEngine()
        self.brokerage_per_order = config.get("capital", {}).get("brokerage_per_order_inr", 20.0)

    def execute(self, verdict: FOJudgeOutput, state: Dict[str, Any], spot_price: Optional[float] = None) -> bool:
        if verdict.verdict in ["AVOID", "REJECT", "WATCHLIST"]:
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

        # Determine spot entry price
        spot_entry = spot_price or getattr(contract, "spot_entry", 0.0)
        if spot_entry <= 0.0:
            spot_entry = contract.strike_price if contract.strike_price > 0 else 100.0

        # Directional Stop-Loss and Target calculation
        is_bullish = ("CE" in c_type) or (c_type == "FUTURES_LONG")
        if is_bullish:
            sl_spot = round(spot_entry * 0.985, 2)    # -1.5% stop loss
            target_spot = round(spot_entry * 1.03, 2)  # +3.0% target gain
        else:
            sl_spot = round(spot_entry * 1.015, 2)    # +1.5% stop loss for PE / short
            target_spot = round(spot_entry * 0.97, 2)  # -3.0% target gain for PE / short

        logger.info(f"[F&O EXECUTOR] Executing {verdict.verdict} ({c_type}) for {symbol} {strike}: {lots} Lots ({total_shares} shares) @ Premium ₹{premium}. Spot: ₹{spot_entry}, SL: ₹{sl_spot}, TP: ₹{target_spot}")

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
            "entry_spot": spot_entry,
            "sl_spot": sl_spot,
            "target_spot": target_spot,
            "entered_at": datetime.utcnow().isoformat() + "Z",
            "megabull_order_id": run_id,
            "brokerage_paid_inr": brokerage,
            "delta": getattr(contract, "delta", 0.5),
            "expiry_dte": getattr(contract, "expiry_dte", 7),
            "verdict": verdict.verdict,
            "waterfall_score": verdict.waterfall_score
        }
        state["open_positions"].append(new_position)
        save_fo_state(state)

        log_row = {
            "run_id": run_id,
            "ticker": ticker,
            "symbol": symbol,
            "verdict": verdict.verdict,
            "contract_type": c_type,
            "strike_price": strike,
            "lots": lots,
            "total_shares": total_shares,
            "spot_entry": spot_entry,
            "option_premium": premium,
            "spot_sl": sl_spot,
            "spot_target": target_spot,
            "waterfall_score": verdict.waterfall_score,
            "position_value_inr": round(premium_val, 2),
            "brokerage_fee_inr": round(brokerage, 2),
            "total_cost_inr": round(total_cost, 2),
            "executed_at": datetime.utcnow().isoformat() + "Z"
        }
        append_to_fo_trade_log(log_row)
        return True

    def execute_cash(self, signal: Bot1Signal, state: Dict[str, Any]) -> bool:
        if signal.side == "AVOID" or signal.quantity <= 0:
            return False

        ticker = signal.ticker
        symbol = signal.symbol
        side = signal.side
        qty = signal.quantity
        cmp = signal.spot_cmp
        pos_val = signal.position_value_inr
        brokerage = signal.estimated_brokerage_inr
        total_cash_required = pos_val + brokerage

        if state["pool_available"] < total_cash_required:
            logger.warning(f"[Bot 1 Cash Executor] Insufficient available cash for {symbol}: Required ₹{total_cash_required:.2f}, Avail ₹{state['pool_available']:.2f}")
            return False

        max_cash_pos = self.config.get("bot1_equity", {}).get("max_open_positions", 5)
        cash_open_count = sum(1 for p in state.get("open_positions", []) if p.get("contract_type") == "EQUITY_CASH")
        if cash_open_count >= max_cash_pos:
            logger.warning(f"[Bot 1 Cash Executor] Max cash open positions limit ({max_cash_pos}) reached. Skipping {symbol}.")
            return False

        logger.info(f"[BOT 1 EXECUTOR] Executing Cash {side} for {symbol}: {qty} shares @ ₹{cmp:.2f}. Total Value: ₹{pos_val:.2f}, Brokerage: ₹{brokerage}")

        state["pool_available"] -= total_cash_required
        state["pool_deployed"] += pos_val
        state["total_brokerage_paid_inr"] += brokerage
        state["trades_today"] += 1

        run_id = f"{symbol}_CASH_{side}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        new_position = {
            "ticker": ticker,
            "contract_type": "EQUITY_CASH",
            "symbol": symbol,
            "strike_price": 0.0,
            "lots": 1,
            "total_shares": qty,
            "entry_premium": cmp,
            "entry_spot": cmp,
            "sl_spot": signal.suggested_sl,
            "target_spot": signal.suggested_target,
            "entered_at": datetime.utcnow().isoformat() + "Z",
            "megabull_order_id": run_id,
            "brokerage_paid_inr": brokerage,
            "side": side,
            "waterfall_score": signal.signal_score
        }
        state["open_positions"].append(new_position)
        save_fo_state(state)

        log_row = {
            "run_id": run_id,
            "ticker": ticker,
            "symbol": symbol,
            "verdict": f"CASH_{side}",
            "contract_type": "EQUITY_CASH",
            "strike_price": 0.0,
            "lots": 1,
            "total_shares": qty,
            "spot_entry": cmp,
            "option_premium": cmp,
            "spot_sl": signal.suggested_sl,
            "spot_target": signal.suggested_target,
            "waterfall_score": signal.signal_score,
            "position_value_inr": pos_val,
            "brokerage_fee_inr": brokerage,
            "total_cost_inr": pos_val + brokerage,
            "executed_at": datetime.utcnow().isoformat() + "Z"
        }
        append_to_fo_trade_log(log_row)
        return True

    def _get_live_spot(self, ticker: str, bar_data: Optional[Any] = None) -> Optional[float]:
        if bar_data:
            if isinstance(bar_data, BarEvent):
                if bar_data.ticker == ticker:
                    return bar_data.close
            elif isinstance(bar_data, dict):
                if ticker in bar_data:
                    val = bar_data[ticker]
                    if isinstance(val, (int, float)): return float(val)
                    if isinstance(val, dict) and "close" in val: return float(val["close"])
                    if isinstance(val, dict) and "Close" in val: return float(val["Close"])
                for k, v in bar_data.items():
                    if k in ticker or ticker in k:
                        if isinstance(v, (int, float)): return float(v)
                        if isinstance(v, dict) and "close" in v: return float(v["close"])

        try:
            df = yfinanceWrapper.fetch_ohlcv(ticker, timeframe="1m", period="1d")
            if not df.empty and 'Close' in df.columns:
                return float(df['Close'].iloc[-1])
        except Exception as e:
            logger.error(f"[F&O Executor] Error fetching live spot for {ticker}: {e}")
        return None

    def exit_position(self, pos: Dict[str, Any], state: Dict[str, Any], current_spot: float, exit_reason: str) -> Dict[str, Any]:
        symbol = pos["symbol"]
        c_type = pos["contract_type"]
        total_shares = int(pos["total_shares"])
        entry_premium = float(pos["entry_premium"])
        entry_spot = float(pos["entry_spot"])
        strike = float(pos["strike_price"])
        dte = int(pos.get("expiry_dte", 7))
        delta = float(pos.get("delta", 0.5))

        is_cash = (c_type == "EQUITY_CASH")
        is_option = ("OPTION" in c_type) or ("SCALP" in c_type)

        if is_cash:
            exit_premium = round(current_spot, 2)
            exit_val = exit_premium * total_shares
            entry_val = entry_premium * total_shares
            exit_cost = self.brokerage_per_order
            side = pos.get("side", "BUY")
            if side == "SELL":
                gross_pnl = entry_val - exit_val
            else:
                gross_pnl = exit_val - entry_val
        elif is_option:
            opt_type = "CE" if "CE" in c_type else "PE"
            try:
                vix = yfinanceWrapper.fetch_vix()
                bs_res = self.options_engine.calculate_bs_price_and_greeks(
                    spot=current_spot, strike=strike, dte=dte, iv_pct=vix, option_type=opt_type
                )
                exit_premium = bs_res["price"]
            except Exception:
                spot_change = (current_spot - entry_spot) if opt_type == "CE" else (entry_spot - current_spot)
                approx_change = spot_change * abs(delta)
                exit_premium = max(0.50, round(entry_premium + approx_change, 2))
            
            exit_val = exit_premium * total_shares
            entry_val = entry_premium * total_shares
            costs = self.options_engine.calculate_trade_costs(
                turnover_inr=exit_val, is_sell=True, contract_type="OPTION"
            )
            exit_cost = costs["total_cost"]
            gross_pnl = exit_val - entry_val
        else:
            # FUTURES
            exit_premium = round(current_spot, 2)
            exit_val = exit_premium * total_shares
            entry_val = entry_premium * total_shares
            costs = self.options_engine.calculate_trade_costs(
                turnover_inr=exit_val, is_sell=True, contract_type="FUTURES"
            )
            exit_cost = costs["total_cost"]
            if "SHORT" in c_type:
                gross_pnl = (entry_spot - current_spot) * total_shares
            else:
                gross_pnl = (current_spot - entry_spot) * total_shares

        entry_brokerage = float(pos.get("brokerage_paid_inr", self.brokerage_per_order))
        net_pnl = gross_pnl - exit_cost
        pnl_pct = (net_pnl / entry_val) * 100.0 if entry_val > 0 else 0.0

        # Update Portfolio State
        state["pool_deployed"] = max(0.0, state["pool_deployed"] - entry_val)
        state["pool_available"] += (entry_val + net_pnl)
        state["daily_pnl_inr"] += net_pnl
        state["pool_total"] = state["pool_available"] + state["pool_deployed"]
        state["daily_pnl_pct"] = round((state["daily_pnl_inr"] / 500000.0) * 100.0, 2)
        state["total_brokerage_paid_inr"] += exit_cost

        logger.info(f"[Executor] Exited {symbol} {c_type} ({exit_reason}) @ Spot ₹{current_spot:.2f}, Price ₹{exit_premium:.2f}. Net P&L: ₹{net_pnl:.2f} ({pnl_pct:.2f}%)")

        trade_log_row = {
            "run_id": pos.get("megabull_order_id", f"{symbol}_{c_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"),
            "ticker": pos["ticker"],
            "symbol": symbol,
            "verdict": pos.get("verdict", c_type),
            "contract_type": c_type,
            "strike_price": strike,
            "lots": pos["lots"],
            "total_shares": total_shares,
            "spot_entry": entry_spot,
            "option_premium": entry_premium,
            "spot_sl": pos["sl_spot"],
            "spot_target": pos["target_spot"],
            "waterfall_score": pos.get("waterfall_score", 8.0),
            "position_value_inr": round(entry_val, 2),
            "brokerage_fee_inr": round(entry_brokerage, 2),
            "total_cost_inr": round(entry_brokerage + exit_cost, 2),
            "executed_at": pos.get("entered_at", datetime.utcnow().isoformat() + "Z"),
            "exit_price": round(exit_premium, 2),
            "exit_reason": exit_reason,
            "realized_pnl_inr": round(net_pnl, 2),
            "realized_pnl_pct": round(pnl_pct, 2)
        }
        append_to_fo_trade_log(trade_log_row)
        return trade_log_row

    def monitor_positions(self, state: Dict[str, Any], bar_data: Optional[Any] = None) -> List[Dict[str, Any]]:
        open_positions = list(state.get("open_positions", []))
        if not open_positions:
            return []

        exited_trades = []
        remaining_positions = []

        for pos in open_positions:
            ticker = pos["ticker"]
            c_type = pos["contract_type"]
            sl_spot = float(pos["sl_spot"])
            target_spot = float(pos["target_spot"])
            entry_spot = float(pos["entry_spot"])

            live_spot = self._get_live_spot(ticker, bar_data)
            if live_spot is None:
                live_spot = entry_spot

            is_bullish = ("CE" in c_type) or (c_type == "FUTURES_LONG") or (c_type == "EQUITY_CASH" and pos.get("side", "BUY") == "BUY")
            exit_reason = None

            if is_bullish:
                if live_spot <= sl_spot:
                    exit_reason = "sl_hit"
                elif live_spot >= target_spot:
                    exit_reason = "target_hit"
            else:
                if live_spot >= sl_spot:
                    exit_reason = "sl_hit"
                elif live_spot <= target_spot:
                    exit_reason = "target_hit"

            if exit_reason:
                trade_record = self.exit_position(pos, state, current_spot=live_spot, exit_reason=exit_reason)
                exited_trades.append(trade_record)
            else:
                remaining_positions.append(pos)

        state["open_positions"] = remaining_positions
        if exited_trades:
            save_fo_state(state)

        # Check 3:15 PM IST Auto Square-Off
        ist_tz = timezone(timedelta(hours=5, minutes=30))
        now_ist = datetime.now(ist_tz)
        if now_ist.weekday() < 5 and (now_ist.hour > 15 or (now_ist.hour == 15 and now_ist.minute >= 15)):
            if state.get("open_positions"):
                logger.info("[F&O Executor] 3:15 PM IST Auto Square-Off triggered. Closing remaining open positions...")
                eod_exits = self.squareoff_all(state, bar_data=bar_data)
                exited_trades.extend(eod_exits)

        return exited_trades

    def squareoff_all(self, state: Dict[str, Any], bar_data: Optional[Any] = None) -> List[Dict[str, Any]]:
        open_positions = list(state.get("open_positions", []))
        if not open_positions:
            return []

        exited_trades = []
        for pos in open_positions:
            ticker = pos["ticker"]
            entry_spot = float(pos["entry_spot"])
            live_spot = self._get_live_spot(ticker, bar_data) or entry_spot
            
            trade_record = self.exit_position(pos, state, current_spot=live_spot, exit_reason="eod_squareoff")
            exited_trades.append(trade_record)

        state["open_positions"] = []
        save_fo_state(state)
        return exited_trades
