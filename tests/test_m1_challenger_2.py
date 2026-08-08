import sys
import os
import math
from datetime import datetime, timezone, timedelta

# Ensure parent directory is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.state import load_fo_state, save_fo_state
from core.schemas import FOContractData, FOJudgeOutput, Bot1Signal
from core.options_engine import OptionsEngine
from agents.executor import FOExecutorAgent
from main import load_config

def create_base_state():
    return {
        "pool_total": 500000.0,
        "pool_available": 500000.0,
        "pool_deployed": 0.0,
        "daily_pnl_inr": 0.0,
        "daily_pnl_pct": 0.0,
        "total_brokerage_paid_inr": 0.0,
        "trades_today": 0,
        "open_positions": []
    }

def test_suite_1_bullish_option_ce():
    print("\n--- Test Suite 1: Bullish Option (CE) SL/TP & Dynamic BS Exit Pricing ---")
    config = load_config()
    executor = FOExecutorAgent(config)
    state = create_base_state()

    contract = FOContractData(
        contract_type="OPTION_CE",
        symbol="NIFTY",
        strike_price=24000,
        expiry_dte=7,
        lot_size=50,
        lots_qty=1,
        total_shares=50,
        option_premium=200.0,
        delta=0.52,
        gamma=0.001,
        theta_per_day=-6.0,
        vega=15.0,
        premium_value_inr=10000.0,
        estimated_brokerage_inr=20.0,
        estimated_total_cost_inr=26.25,
        spot_entry=24000.0
    )
    verdict = FOJudgeOutput(
        ticker="^NSEI",
        run_timestamp=datetime.now(timezone.utc),
        verdict="BUY_CE",
        waterfall_score=8.5,
        confidence=8.5,
        contract=contract,
        position_sizing_inr=10026.25,
        reasoning="Test CE Execution"
    )

    # 1. Execute Entry
    executed = executor.execute(verdict, state, spot_price=24000.0)
    assert executed is True, "CE execution failed"
    assert len(state["open_positions"]) == 1
    pos = state["open_positions"][0]
    assert pos["sl_spot"] == 23640.0, f"Expected SL 23640.0, got {pos['sl_spot']}"
    assert pos["target_spot"] == 24720.0, f"Expected TP 24720.0, got {pos['target_spot']}"

    # 2. Bar with no breach (Spot 24100)
    exits = executor.monitor_positions(state, bar_data={"^NSEI": 24100.0})
    assert len(exits) == 0, "Position exited prematurely"
    assert len(state["open_positions"]) == 1, "Position missing from state"

    # 3. Bar with TP breach (Spot 24750 >= Target 24720)
    exits = executor.monitor_positions(state, bar_data={"^NSEI": 24750.0})
    assert len(exits) == 1, "TP breach failed to exit position"
    assert len(state["open_positions"]) == 0, "Position still open after exit"
    
    trade = exits[0]
    assert trade["exit_reason"] == "target_hit", f"Wrong exit reason: {trade['exit_reason']}"
    
    # Verify dynamic option exit pricing via Black-Scholes
    # At spot 24750 (strike 24000, 7 DTE), BS option price must be > intrinsic value (750)
    expected_min_bs = 750.0
    assert trade["exit_price"] >= expected_min_bs, f"Exit price {trade['exit_price']} lower than intrinsic {expected_min_bs}"
    assert trade["exit_price"] != round(200.0 * 1.03, 2), "Exit price wrongly hardcoded to entry_premium * 1.03!"

    # Verify transaction fee deduction on exit
    bs_val = trade["exit_price"] * 50
    expected_costs = executor.options_engine.calculate_trade_costs(turnover_inr=bs_val, is_sell=True, contract_type="OPTION")
    expected_net_pnl = (bs_val - 10000.0) - expected_costs["total_cost"]
    assert math.isclose(trade["realized_pnl_inr"], round(expected_net_pnl, 2), abs_tol=0.1), \
        f"Net PnL mismatch: got {trade['realized_pnl_inr']}, expected {expected_net_pnl}"

    print("  [PASS] Bullish Option (CE) TP Exit & Dynamic Pricing Verified.")

    # 4. SL Breach Test (Re-entry then Spot 23500 <= SL 23640)
    state = create_base_state()
    executor.execute(verdict, state, spot_price=24000.0)
    exits_sl = executor.monitor_positions(state, bar_data={"^NSEI": 23500.0})
    assert len(exits_sl) == 1
    trade_sl = exits_sl[0]
    assert trade_sl["exit_reason"] == "sl_hit"
    assert trade_sl["exit_price"] < 200.0, f"Exit price should be lower on SL, got {trade_sl['exit_price']}"
    assert trade_sl["realized_pnl_inr"] < 0.0, f"PnL should be negative on SL, got {trade_sl['realized_pnl_inr']}"
    print("  [PASS] Bullish Option (CE) SL Exit Verified.")

def test_suite_2_bearish_option_pe():
    print("\n--- Test Suite 2: Bearish Option (PE) SL/TP & Dynamic BS Exit Pricing ---")
    config = load_config()
    executor = FOExecutorAgent(config)
    state = create_base_state()

    contract = FOContractData(
        contract_type="OPTION_PE",
        symbol="NIFTY",
        strike_price=24000,
        expiry_dte=7,
        lot_size=50,
        lots_qty=1,
        total_shares=50,
        option_premium=200.0,
        delta=-0.48,
        gamma=0.001,
        theta_per_day=-6.0,
        vega=15.0,
        premium_value_inr=10000.0,
        estimated_brokerage_inr=20.0,
        estimated_total_cost_inr=26.25,
        spot_entry=24000.0
    )
    verdict = FOJudgeOutput(
        ticker="^NSEI",
        run_timestamp=datetime.now(timezone.utc),
        verdict="BUY_PE",
        waterfall_score=8.5,
        confidence=8.5,
        contract=contract,
        position_sizing_inr=10026.25,
        reasoning="Test PE Execution"
    )

    # 1. Execute Entry
    executed = executor.execute(verdict, state, spot_price=24000.0)
    assert executed is True, "PE execution failed"
    pos = state["open_positions"][0]
    # For PE (Bearish), SL spot is HIGHER (+1.5% -> 24360), Target spot is LOWER (-3.0% -> 23280)
    assert pos["sl_spot"] == 24360.0, f"Expected PE SL 24360.0, got {pos['sl_spot']}"
    assert pos["target_spot"] == 23280.0, f"Expected PE TP 23280.0, got {pos['target_spot']}"

    # 2. Bar with no breach (Spot 23900)
    exits = executor.monitor_positions(state, bar_data={"^NSEI": 23900.0})
    assert len(exits) == 0, "PE Position exited prematurely"

    # 3. Bar with PE TP breach (Spot 23200 <= Target 23280)
    exits = executor.monitor_positions(state, bar_data={"^NSEI": 23200.0})
    assert len(exits) == 1, "PE TP breach failed to exit"
    trade = exits[0]
    assert trade["exit_reason"] == "target_hit", f"Wrong exit reason: {trade['exit_reason']}"
    
    # Put Option at spot 23200 (strike 24000, r=6.5%, 7 DTE) European BS price is ~774.02
    # (Strike present value 24000 * exp(-0.065 * 7/365) - 23200 = ~770.10 + time value)
    expected_min_bs = 750.0
    assert trade["exit_price"] >= expected_min_bs, f"PE Exit price {trade['exit_price']} lower than expected BS price threshold {expected_min_bs}"
    assert trade["realized_pnl_inr"] > 0, "PE TP should be profitable"
    print("  [PASS] Bearish Option (PE) TP Exit & Dynamic Pricing Verified.")

    # 4. Bar with PE SL breach (Spot 24400 >= SL 24360)
    state = create_base_state()
    executor.execute(verdict, state, spot_price=24000.0)
    exits_sl = executor.monitor_positions(state, bar_data={"^NSEI": 24400.0})
    assert len(exits_sl) == 1
    trade_sl = exits_sl[0]
    assert trade_sl["exit_reason"] == "sl_hit", f"Wrong SL exit reason: {trade_sl['exit_reason']}"
    assert trade_sl["exit_price"] < 200.0, f"PE option premium should drop when spot rises, got {trade_sl['exit_price']}"
    assert trade_sl["realized_pnl_inr"] < 0, "PE SL should result in negative PnL"
    print("  [PASS] Bearish Option (PE) SL Exit Verified.")

def test_suite_3_bullish_futures_long():
    print("\n--- Test Suite 3: Bullish Futures (FUTURES_LONG) SL/TP & Pricing ---")
    config = load_config()
    executor = FOExecutorAgent(config)
    state = create_base_state()

    contract = FOContractData(
        contract_type="FUTURES_LONG",
        symbol="BANKNIFTY",
        strike_price=51000,
        expiry_dte=14,
        lot_size=15,
        lots_qty=2,
        total_shares=30,
        option_premium=51000.0,
        delta=1.0,
        gamma=0.0,
        theta_per_day=0.0,
        vega=0.0,
        premium_value_inr=1530000.0,
        estimated_brokerage_inr=20.0,
        estimated_total_cost_inr=211.25,
        spot_entry=51000.0
    )
    verdict = FOJudgeOutput(
        ticker="^NSEBANK",
        run_timestamp=datetime.now(timezone.utc),
        verdict="BUY_FUTURES",
        waterfall_score=9.0,
        confidence=9.0,
        contract=contract,
        position_sizing_inr=1530211.25,
        reasoning="Test Futures Long"
    )

    state["pool_available"] = 2000000.0
    state["pool_total"] = 2000000.0
    executed = executor.execute(verdict, state, spot_price=51000.0)
    assert executed is True, "Futures Long execution failed"
    pos = state["open_positions"][0]
    assert pos["sl_spot"] == 50235.0 # -1.5%
    assert pos["target_spot"] == 52530.0 # +3.0%

    # TP breach at 52600
    exits = executor.monitor_positions(state, bar_data={"^NSEBANK": 52600.0})
    assert len(exits) == 1
    trade = exits[0]
    assert trade["exit_reason"] == "target_hit"
    assert trade["exit_price"] == 52600.0
    
    # Futures PnL = (52600 - 51000) * 30 - exit_cost = 48,000 - exit_cost
    expected_costs = executor.options_engine.calculate_trade_costs(turnover_inr=52600*30, is_sell=True, contract_type="FUTURES")
    expected_pnl = 48000.0 - expected_costs["total_cost"]
    assert math.isclose(trade["realized_pnl_inr"], round(expected_pnl, 2), abs_tol=0.1)
    print("  [PASS] Bullish Futures Long TP Exit & PnL Verified.")

def test_suite_4_bearish_futures_short():
    print("\n--- Test Suite 4: Bearish Futures (FUTURES_SHORT) SL/TP & Pricing ---")
    config = load_config()
    executor = FOExecutorAgent(config)
    state = create_base_state()
    state["pool_available"] = 2000000.0
    state["pool_total"] = 2000000.0

    contract = FOContractData(
        contract_type="FUTURES_SHORT",
        symbol="BANKNIFTY",
        strike_price=51000,
        expiry_dte=14,
        lot_size=15,
        lots_qty=2,
        total_shares=30,
        option_premium=51000.0,
        delta=-1.0,
        gamma=0.0,
        theta_per_day=0.0,
        vega=0.0,
        premium_value_inr=1530000.0,
        estimated_brokerage_inr=20.0,
        estimated_total_cost_inr=211.25,
        spot_entry=51000.0
    )
    verdict = FOJudgeOutput(
        ticker="^NSEBANK",
        run_timestamp=datetime.now(timezone.utc),
        verdict="SELL_FUTURES",
        waterfall_score=9.0,
        confidence=9.0,
        contract=contract,
        position_sizing_inr=1530211.25,
        reasoning="Test Futures Short"
    )

    executor.execute(verdict, state, spot_price=51000.0)
    pos = state["open_positions"][0]
    assert pos["sl_spot"] == 51765.0 # +1.5%
    assert pos["target_spot"] == 49470.0 # -3.0%

    # TP breach at 49400 (spot falls)
    exits = executor.monitor_positions(state, bar_data={"^NSEBANK": 49400.0})
    assert len(exits) == 1
    trade = exits[0]
    assert trade["exit_reason"] == "target_hit"
    # Gross PnL = (51000 - 49400) * 30 = 48,000
    expected_costs = executor.options_engine.calculate_trade_costs(turnover_inr=49400*30, is_sell=True, contract_type="FUTURES")
    expected_pnl = 48000.0 - expected_costs["total_cost"]
    assert math.isclose(trade["realized_pnl_inr"], round(expected_pnl, 2), abs_tol=0.1)
    print("  [PASS] Bearish Futures Short TP Exit & PnL Verified.")

    # SL breach at 51800 (spot rises)
    state = create_base_state()
    state["pool_available"] = 2000000.0
    state["pool_total"] = 2000000.0
    executor.execute(verdict, state, spot_price=51000.0)
    exits_sl = executor.monitor_positions(state, bar_data={"^NSEBANK": 51800.0})
    assert len(exits_sl) == 1
    trade_sl = exits_sl[0]
    assert trade_sl["exit_reason"] == "sl_hit"
    assert trade_sl["realized_pnl_inr"] < 0
    print("  [PASS] Bearish Futures Short SL Exit Verified.")

def test_suite_5_equity_cash_buy_sell():
    print("\n--- Test Suite 5: Equity Cash BUY and SELL SL/TP ---")
    config = load_config()
    executor = FOExecutorAgent(config)

    # 1. Equity Cash BUY
    state_buy = create_base_state()
    sig_buy = Bot1Signal(
        ticker="RELIANCE.NS",
        symbol="RELIANCE",
        side="BUY",
        spot_cmp=2500.0,
        signal_score=8.0,
        timeframe="5m",
        suggested_entry=2500.0,
        suggested_sl=2462.50, # -1.5%
        suggested_target=2575.00, # +3.0%
        quantity=20,
        position_value_inr=50000.0,
        estimated_brokerage_inr=20.0,
        reasoning="Test Cash Buy"
    )
    executed = executor.execute_cash(sig_buy, state_buy)
    assert executed is True

    exits_buy = executor.monitor_positions(state_buy, bar_data={"RELIANCE.NS": 2580.0})
    assert len(exits_buy) == 1
    assert exits_buy[0]["exit_reason"] == "target_hit"
    # Gross PnL = (2580 - 2500) * 20 = 1600. Net PnL = 1600 - 20 (exit brokerage) = 1580
    assert exits_buy[0]["realized_pnl_inr"] == 1580.0
    print("  [PASS] Equity Cash BUY TP Exit & PnL Verified.")

    # 2. Equity Cash SELL (Short)
    state_sell = create_base_state()
    sig_sell = Bot1Signal(
        ticker="RELIANCE.NS",
        symbol="RELIANCE",
        side="SELL",
        spot_cmp=2500.0,
        signal_score=8.0,
        timeframe="5m",
        suggested_entry=2500.0,
        suggested_sl=2537.50, # +1.5%
        suggested_target=2425.00, # -3.0%
        quantity=20,
        position_value_inr=50000.0,
        estimated_brokerage_inr=20.0,
        reasoning="Test Cash Sell"
    )
    executed_sell = executor.execute_cash(sig_sell, state_sell)
    assert executed_sell is True

    exits_sell = executor.monitor_positions(state_sell, bar_data={"RELIANCE.NS": 2420.0})
    assert len(exits_sell) == 1
    assert exits_sell[0]["exit_reason"] == "target_hit"
    # Gross PnL = (2500 - 2420) * 20 = 1600. Net PnL = 1600 - 20 = 1580
    assert exits_sell[0]["realized_pnl_inr"] == 1580.0
    print("  [PASS] Equity Cash SELL TP Exit & PnL Verified.")

def test_suite_6_no_hardcoded_multipliers():
    print("\n--- Test Suite 6: Code Audit for Hardcoded +3% Option Multipliers ---")
    import inspect
    source_code = inspect.getsource(FOExecutorAgent.exit_position)
    assert "1.03" not in source_code, "Hardcoded '1.03' multiplier found in exit_position()!"
    assert "0.985" not in source_code, "Hardcoded '0.985' multiplier found in exit_position()!"
    print("  [PASS] Confirmed zero hardcoded multipliers in exit_position(). Pricing is 100% dynamic.")

if __name__ == "__main__":
    print("=======================================================================")
    print("M1 CHALLENGER 2: EMPIRICAL POSITION MONITOR & EXIT PRICING TEST HARNESS")
    print("=======================================================================")
    test_suite_1_bullish_option_ce()
    test_suite_2_bearish_option_pe()
    test_suite_3_bullish_futures_long()
    test_suite_4_bearish_futures_short()
    test_suite_5_equity_cash_buy_sell()
    test_suite_6_no_hardcoded_multipliers()
    print("=======================================================================")
    print("ALL EMPIRICAL TESTS PASSED SUCCESSFULLY! MONITOR & EXIT PRICING APPROVED!")
    print("=======================================================================")
