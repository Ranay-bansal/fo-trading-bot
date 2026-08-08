import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime

from core.state import load_fo_state, save_fo_state, append_to_fo_trade_log
from core.data_sources import yfinanceWrapper, BarEvent, StreamingTickSimulator
from core.schemas import FOJudgeOutput, FOContractData, Bot1Signal
from agents.bot1_cash import Bot1EquityAgent
from agents.bot2_options import Bot2OptionSwarmAgent
from agents.executor import FOExecutorAgent
from main import load_config

def test_bot1_equity_cash_agent():
    config = load_config()
    state = load_fo_state()
    agent = Bot1EquityAgent(config)
    signals = agent.run(state, timeframe="5m")
    assert isinstance(signals, list)

def test_bot2_option_swarm_agent():
    config = load_config()
    state = load_fo_state()
    agent = Bot2OptionSwarmAgent(config)
    out = agent.run("^NSEI", timeframe="5m", state=state, vix_val=14.0)
    # Result can be FOJudgeOutput or None
    if out:
        assert isinstance(out, FOJudgeOutput)

def test_executor_and_position_monitor():
    config = load_config()
    executor = FOExecutorAgent(config)
    state = load_fo_state()
    state["pool_available"] = 500000.0
    state["open_positions"] = []

    contract = FOContractData(
        contract_type="OPTION_CE",
        symbol="NIFTY",
        strike_price=24200,
        expiry_dte=7,
        lot_size=25,
        lots_qty=2,
        total_shares=50,
        option_premium=145.0,
        delta=0.55,
        gamma=0.001,
        theta_per_day=-5.0,
        vega=12.0,
        premium_value_inr=7250.0,
        estimated_brokerage_inr=20.0,
        estimated_total_cost_inr=24.50,
        spot_entry=24210.50
    )
    judge_out = FOJudgeOutput(
        ticker="^NSEI",
        run_timestamp=datetime.utcnow(),
        verdict="BUY_CE",
        waterfall_score=8.5,
        confidence=8.5,
        contract=contract,
        position_sizing_inr=7274.50,
        reasoning="Test execute"
    )

    executed = executor.execute(judge_out, state)
    assert executed is True
    assert len(state["open_positions"]) == 1
    pos = state["open_positions"][0]
    assert pos["entry_spot"] == 24210.50
    assert pos["sl_spot"] == round(24210.50 * 0.985, 2)
    assert pos["target_spot"] == round(24210.50 * 1.03, 2)

    # Test Target Hit Exit
    bar_data = {"^NSEI": 25057.87}
    exits = executor.monitor_positions(state, bar_data=bar_data)
    assert len(exits) == 1
    assert len(state["open_positions"]) == 0
    assert exits[0]["exit_reason"] == "target_hit"
    assert exits[0]["realized_pnl_inr"] > 0

if __name__ == "__main__":
    test_bot1_equity_cash_agent()
    test_bot2_option_swarm_agent()
    test_executor_and_position_monitor()
    print("=== ALL M1 UNIT TESTS PASSED SUCCESSFULLY ===")
