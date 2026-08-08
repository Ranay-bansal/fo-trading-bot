import sys
import os
import math
import logging
from datetime import datetime
import pandas as pd
import numpy as np

# Ensure root dir is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.state import load_fo_state, save_fo_state
from core.data_sources import yfinanceWrapper, BarEvent
from core.options_engine import OptionsEngine
from core.schemas import FOJudgeOutput, FOContractData, Bot1Signal, FOScoutOutput
from agents.bot1_cash import Bot1EquityAgent
from agents.bot2_options import Bot2OptionSwarmAgent
from agents.scout import FOScoutAgent
from agents.technician import FOTechnicianAgent
from agents.judge import FOJudgeAgent
from agents.executor import FOExecutorAgent
from main import load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("M1StressTest")

def test_scenario_1_empty_and_short_df():
    logger.info("=== SCENARIO 1: Empty & Short OHLCV DataFrames ===")
    config = load_config()
    bot1 = Bot1EquityAgent(config)
    bot2 = Bot2OptionSwarmAgent(config)
    scout = FOScoutAgent(config)
    technician = FOTechnicianAgent(config)
    judge = FOJudgeAgent(config)
    state = load_fo_state()

    orig_fetch = yfinanceWrapper.fetch_ohlcv

    try:
        # Case 1A: Empty DataFrame
        yfinanceWrapper.fetch_ohlcv = staticmethod(lambda ticker, timeframe="5m", period="1d": pd.DataFrame())
        
        # Test Bot 1
        sig1 = bot1.run_symbol({"symbol": "RELIANCE", "ticker": "RELIANCE.NS"}, timeframe="5m", state=state)
        assert sig1.side == "AVOID", f"Expected AVOID for empty DF, got {sig1.side}"
        assert sig1.quantity == 0
        
        bot1_signals = bot1.run(state, timeframe="5m")
        assert isinstance(bot1_signals, list) and len(bot1_signals) == 0

        # Test Bot 2
        scout_outs = scout.run(timeframe="5m")
        assert isinstance(scout_outs, list) and len(scout_outs) == 0

        sig2 = bot2.run("^NSEI", timeframe="5m", state=state)
        assert sig2 is None

        scan2 = bot2.scan_universe(timeframe="5m", state=state)
        assert isinstance(scan2, list) and len(scan2) == 0

        # Case 1B: 2-row DataFrame (insufficient <5 bars)
        dates = pd.date_range("2026-08-08 09:15", periods=2, freq="5min")
        df_short = pd.DataFrame({
            "Open": [24000.0, 24050.0],
            "High": [24100.0, 24100.0],
            "Low": [23950.0, 24000.0],
            "Close": [24050.0, 24080.0],
            "Volume": [1000, 1500]
        }, index=dates)
        
        yfinanceWrapper.fetch_ohlcv = staticmethod(lambda ticker, timeframe="5m", period="1d": df_short.copy())

        sig1_short = bot1.run_symbol({"symbol": "RELIANCE", "ticker": "RELIANCE.NS"}, timeframe="5m", state=state)
        assert sig1_short.side == "AVOID"

        scout_outs_short = scout.run(timeframe="5m")
        assert isinstance(scout_outs_short, list) and len(scout_outs_short) == 0

        # Case 1C: DataFrame with NaN values
        df_nan = pd.DataFrame({
            "Open": [np.nan, 24050.0, 24000.0, 24100.0, 24050.0],
            "High": [24100.0, np.nan, 24150.0, 24200.0, 24100.0],
            "Low": [23950.0, 24000.0, np.nan, 24000.0, 24000.0],
            "Close": [24050.0, 24080.0, 24100.0, np.nan, 24080.0],
            "Volume": [1000, 1500, 1200, 800, np.nan]
        }, index=pd.date_range("2026-08-08 09:15", periods=5, freq="5min"))

        yfinanceWrapper.fetch_ohlcv = staticmethod(lambda ticker, timeframe="5m", period="1d": df_nan.copy())
        sig1_nan = bot1.run_symbol({"symbol": "RELIANCE", "ticker": "RELIANCE.NS"}, timeframe="5m", state=state)
        assert sig1_nan is not None

        logger.info("PASS: Scenario 1 (Empty & Short OHLCV DataFrames)")
    finally:
        yfinanceWrapper.fetch_ohlcv = orig_fetch

def test_scenario_2_zero_and_negative_capital():
    logger.info("=== SCENARIO 2: Zero, Negative, & Extreme Capital Balances ===")
    config = load_config()
    bot1 = Bot1EquityAgent(config)
    executor = FOExecutorAgent(config)

    # Case 2A: Zero Available Capital
    state_zero = {
        "pool_total": 500000.0,
        "pool_available": 0.0,
        "pool_deployed": 500000.0,
        "daily_pnl_inr": 0.0,
        "daily_pnl_pct": 0.0,
        "total_brokerage_paid_inr": 0.0,
        "trades_today": 0,
        "open_positions": []
    }

    sig_zero = bot1.run_symbol({"symbol": "RELIANCE", "ticker": "RELIANCE.NS"}, timeframe="5m", state=state_zero)
    assert sig_zero.quantity == 0 or sig_zero.side == "AVOID", f"Quantity should be 0 when capital is 0, got {sig_zero.quantity}"

    # Try executing a cash signal with 0 capital
    mock_cash_sig = Bot1Signal(
        ticker="RELIANCE.NS", symbol="RELIANCE", side="BUY", spot_cmp=2500.0,
        signal_score=8.5, timeframe="5m", suggested_entry=2500.0,
        suggested_sl=2450.0, suggested_target=2600.0, quantity=10,
        position_value_inr=25000.0, estimated_brokerage_inr=20.0, reasoning="Test"
    )
    executed_cash = executor.execute_cash(mock_cash_sig, state_zero)
    assert executed_cash is False, "execute_cash should fail when pool_available is 0"

    # Case 2B: Negative Available Capital
    state_neg = {
        "pool_total": 500000.0,
        "pool_available": -10000.0,
        "pool_deployed": 510000.0,
        "daily_pnl_inr": -10000.0,
        "daily_pnl_pct": -2.0,
        "total_brokerage_paid_inr": 100.0,
        "trades_today": 2,
        "open_positions": []
    }

    sig_neg = bot1.run_symbol({"symbol": "RELIANCE", "ticker": "RELIANCE.NS"}, timeframe="5m", state=state_neg)
    assert sig_neg.quantity == 0 or sig_neg.side == "AVOID"

    # Case 2C: Missing keys in state
    state_empty = {}
    sig_empty_state = bot1.run_symbol({"symbol": "RELIANCE", "ticker": "RELIANCE.NS"}, timeframe="5m", state=state_empty)
    assert sig_empty_state is not None

    logger.info("PASS: Scenario 2 (Zero & Negative Capital Balances)")

def test_scenario_3_max_open_position_limits():
    logger.info("=== SCENARIO 3: Max Open Position Limits ===")
    config = load_config()
    executor = FOExecutorAgent(config)
    
    orig_vix = yfinanceWrapper.fetch_vix
    yfinanceWrapper.fetch_vix = staticmethod(lambda: 14.5)

    try:
        max_cash_pos = config.get("bot1_equity", {}).get("max_open_positions", 5)

        state = {
            "pool_total": 1000000.0,
            "pool_available": 1000000.0,
            "pool_deployed": 0.0,
            "daily_pnl_inr": 0.0,
            "daily_pnl_pct": 0.0,
            "total_brokerage_paid_inr": 0.0,
            "trades_today": 0,
            "open_positions": []
        }

        # Pre-fill max allowed cash positions (5)
        for i in range(max_cash_pos):
            pos = {
                "ticker": f"STOCK_{i}.NS",
                "contract_type": "EQUITY_CASH",
                "symbol": f"STOCK_{i}",
                "strike_price": 0.0,
                "lots": 1,
                "total_shares": 10,
                "entry_premium": 100.0,
                "entry_spot": 100.0,
                "sl_spot": 95.0,
                "target_spot": 110.0,
                "entered_at": datetime.utcnow().isoformat() + "Z",
                "megabull_order_id": f"STOCK_{i}_CASH",
                "brokerage_paid_inr": 20.0,
                "side": "BUY",
                "waterfall_score": 8.0
            }
            state["open_positions"].append(pos)

        # Try executing 6th cash position
        new_sig = Bot1Signal(
            ticker="NEWSTOCK.NS", symbol="NEWSTOCK", side="BUY", spot_cmp=500.0,
            signal_score=8.5, timeframe="5m", suggested_entry=500.0,
            suggested_sl=490.0, suggested_target=520.0, quantity=10,
            position_value_inr=5000.0, estimated_brokerage_inr=20.0, reasoning="Test 6th pos"
        )

        executed = executor.execute_cash(new_sig, state)
        assert executed is False, f"Executor MUST reject trade when max_open_positions ({max_cash_pos}) reached"
        assert len([p for p in state["open_positions"] if p["contract_type"] == "EQUITY_CASH"]) == max_cash_pos

        # Test monitor_positions with open position list
        large_state = {
            "pool_total": 1000000.0,
            "pool_available": 500000.0,
            "pool_deployed": 500000.0,
            "daily_pnl_inr": 0.0,
            "daily_pnl_pct": 0.0,
            "total_brokerage_paid_inr": 0.0,
            "trades_today": 20,
            "open_positions": []
        }
        for i in range(20):
            large_state["open_positions"].append({
                "ticker": f"POS_{i}.NS",
                "contract_type": "OPTION_CE",
                "symbol": f"POS_{i}",
                "strike_price": 1000.0,
                "lots": 1,
                "total_shares": 50,
                "entry_premium": 50.0,
                "entry_spot": 1000.0,
                "sl_spot": 980.0, # Stop loss at 980
                "target_spot": 1050.0,
                "entered_at": datetime.utcnow().isoformat() + "Z",
                "megabull_order_id": f"ORDER_{i}",
                "brokerage_paid_inr": 20.0,
                "delta": 0.5,
                "expiry_dte": 7
            })

        # Trigger SL for half of them (first 10 tickers hit SL 950.0)
        bar_data = {f"POS_{i}.NS": 950.0 if i < 10 else 1000.0 for i in range(20)}
        exits = executor.monitor_positions(large_state, bar_data=bar_data)
        assert len(exits) == 10, f"Expected 10 exits, got {len(exits)}"
        assert len(large_state["open_positions"]) == 10

        logger.info("PASS: Scenario 3 (Max Open Position Limits)")
    finally:
        yfinanceWrapper.fetch_vix = orig_vix

def test_scenario_4_sudden_market_price_jumps_and_volatility():
    logger.info("=== SCENARIO 4: Sudden Market Price Jumps & Volatility ===")
    config = load_config()
    executor = FOExecutorAgent(config)
    opt_engine = OptionsEngine()

    orig_vix = yfinanceWrapper.fetch_vix
    yfinanceWrapper.fetch_vix = staticmethod(lambda: 14.5)

    try:
        # Case 4A: Black-Scholes robustness with extreme VIX, DTE, Spot
        res1 = opt_engine.calculate_bs_price_and_greeks(spot=0.0, strike=24000.0, dte=7, iv_pct=15.0)
        assert res1["price"] >= 0.5 and not math.isnan(res1["price"])

        res2 = opt_engine.calculate_bs_price_and_greeks(spot=24000.0, strike=24000.0, dte=0, iv_pct=15.0)
        assert res2["price"] >= 0.5 and not math.isnan(res2["price"])

        res3 = opt_engine.calculate_bs_price_and_greeks(spot=24000.0, strike=24000.0, dte=7, iv_pct=0.0)
        assert res3["price"] >= 0.5 and not math.isnan(res3["price"])

        res4 = opt_engine.calculate_bs_price_and_greeks(spot=24000.0, strike=24000.0, dte=7, iv_pct=999.0)
        assert res4["price"] >= 0.5 and not math.isnan(res4["price"])

        # Case 4B: Flash Crash in position monitor (50% drop)
        state = {
            "pool_total": 500000.0,
            "pool_available": 450000.0,
            "pool_deployed": 50000.0,
            "daily_pnl_inr": 0.0,
            "daily_pnl_pct": 0.0,
            "total_brokerage_paid_inr": 100.0,
            "trades_today": 1,
            "open_positions": [{
                "ticker": "NIFTY.NS",
                "contract_type": "OPTION_CE",
                "symbol": "NIFTY",
                "strike_price": 24000.0,
                "lots": 2,
                "total_shares": 50,
                "entry_premium": 200.0,
                "entry_spot": 24000.0,
                "sl_spot": 23640.0, # 1.5% SL
                "target_spot": 24720.0,
                "entered_at": datetime.utcnow().isoformat() + "Z",
                "megabull_order_id": "NIFTY_CRASH",
                "brokerage_paid_inr": 20.0,
                "delta": 0.5,
                "expiry_dte": 7
            }]
        }

        # Spot jumps down to 12000 (-50%)
        exits_crash = executor.monitor_positions(state, bar_data={"NIFTY.NS": 12000.0})
        assert len(exits_crash) == 1
        assert exits_crash[0]["exit_reason"] == "sl_hit"
        assert not math.isnan(exits_crash[0]["realized_pnl_inr"])

        # Case 4C: Huge Gap Up (+100% jump)
        state_gapup = {
            "pool_total": 500000.0,
            "pool_available": 450000.0,
            "pool_deployed": 50000.0,
            "daily_pnl_inr": 0.0,
            "daily_pnl_pct": 0.0,
            "total_brokerage_paid_inr": 100.0,
            "trades_today": 1,
            "open_positions": [{
                "ticker": "RELIANCE.NS",
                "contract_type": "EQUITY_CASH",
                "symbol": "RELIANCE",
                "strike_price": 0.0,
                "lots": 1,
                "total_shares": 100,
                "entry_premium": 1500.0,
                "entry_spot": 1500.0,
                "sl_spot": 1470.0,
                "target_spot": 1560.0,
                "entered_at": datetime.utcnow().isoformat() + "Z",
                "megabull_order_id": "RELIANCE_GAP",
                "brokerage_paid_inr": 20.0,
                "side": "BUY"
            }]
        }

        # Spot jumps to 3000.0 (+100%)
        exits_gapup = executor.monitor_positions(state_gapup, bar_data={"RELIANCE.NS": 3000.0})
        assert len(exits_gapup) == 1
        assert exits_gapup[0]["exit_reason"] == "target_hit"
        assert exits_gapup[0]["realized_pnl_inr"] == (3000.0 - 1500.0) * 100 - 20.0

        logger.info("PASS: Scenario 4 (Sudden Market Price Jumps & Volatility)")
    finally:
        yfinanceWrapper.fetch_vix = orig_vix

if __name__ == "__main__":
    test_scenario_1_empty_and_short_df()
    test_scenario_2_zero_and_negative_capital()
    test_scenario_3_max_open_position_limits()
    test_scenario_4_sudden_market_price_jumps_and_volatility()
    print("\n=======================================================")
    print("=== ALL M1 EMPIRICAL STRESS TEST SCENARIOS PASSED! ===")
    print("=======================================================")
