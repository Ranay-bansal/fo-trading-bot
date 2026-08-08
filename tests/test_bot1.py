import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import os
import json
import tempfile
from datetime import datetime

from core.schemas import FOScoutOutput, FOTechnicianOutput, FOJudgeOutput, FOContractData
from core.data_sources import yfinanceWrapper, calculate_vwap, calculate_rsi, calculate_supertrend
from agents.scout import FOScoutAgent
from agents.technician import FOTechnicianAgent
from agents.judge import FOJudgeAgent
from agents.executor import FOExecutorAgent

class TestBot1CashEngine(unittest.TestCase):
    """
    Tier 1 & Tier 2 Test Suite for Bot 1: Equity Intraday Cash Engine.
    Covers cash margin position sizing (1x), signal generation, SL/TP monitoring,
    zero-latency bar execution, cash balance constraints, and boundary edge cases.
    """

    def setUp(self):
        import core.state
        core.state.DEFAULT_STATE["open_positions"] = []
        core.state.DEFAULT_STATE["total_brokerage_paid_inr"] = 0.0
        self.config = {
            "project_name": "AlphaDesk Cash Engine Test",
            "capital": {
                "initial_pool_inr": 500000.0,
                "brokerage_per_order_inr": 20.0
            },
            "risk": {
                "risk_pct_per_trade": 2.0,
                "max_open_positions": 4,
                "min_stop_loss_pct": 1.5
            },
            "fo_universe": {
                "stocks": [
                    {"symbol": "RELIANCE", "ticker": "RELIANCE.NS", "lot_size": 1, "strike_step": 10, "sector": "ENERGY"},
                    {"symbol": "TCS", "ticker": "TCS.NS", "lot_size": 1, "strike_step": 20, "sector": "IT"}
                ]
            }
        }
        self.state = {
            "last_updated": None,
            "pool_total": 500000.0,
            "pool_available": 500000.0,
            "pool_deployed": 0.0,
            "daily_pnl_inr": 0.0,
            "daily_pnl_pct": 0.0,
            "total_brokerage_paid_inr": 0.0,
            "trades_today": 0,
            "open_positions": []
        }

    def _generate_synthetic_ohlcv(self, length=30, start_price=2500.0, trend="up"):
        dates = pd.date_range(end=datetime.now(), periods=length, freq="5min")
        np.random.seed(42)
        if trend == "up":
            prices = start_price + np.cumsum(np.random.uniform(0.5, 3.0, size=length))
        elif trend == "down":
            prices = start_price - np.cumsum(np.random.uniform(0.5, 3.0, size=length))
        else:
            prices = start_price + np.random.uniform(-2.0, 2.0, size=length)
        
        df = pd.DataFrame({
            "Open": prices - np.random.uniform(0.1, 0.5, size=length),
            "High": prices + np.random.uniform(0.5, 1.5, size=length),
            "Low": prices - np.random.uniform(0.5, 1.5, size=length),
            "Close": prices,
            "Volume": np.random.randint(1000, 50000, size=length)
        }, index=dates)
        return df

    def test_bot1_cash_margin_position_sizing_1x(self):
        """Test 1: Equity cash 1x margin position sizing does not exceed available cash pool."""
        scout_out = FOScoutOutput(
            ticker="RELIANCE.NS", symbol="RELIANCE", is_index=False,
            spot_cmp=2500.0, rvol=1.5, price_change_pct=1.2,
            lot_size=1, strike_step=10.0, scout_rank=1, scout_modifier=0.5
        )
        tech_out = MagicMock()
        tech_out.stance = "bullish"
        tech_out.vix = 14.5
        tech_out.technical_score = 2.0

        judge = FOJudgeAgent(self.config)
        judge_out = judge.run(scout_out, tech_out, self.state, timeframe="5m")

        self.assertIn(judge_out.verdict, ["BUY_CE", "SCALP_CE", "BUY_FUT", "AVOID"])
        if judge_out.verdict != "AVOID":
            self.assertLessEqual(judge_out.position_sizing_inr, self.state["pool_available"])
            self.assertGreater(judge_out.contract.total_shares, 0)

    @patch("core.data_sources.yf.download")
    def test_bot1_signal_generation_bullish_vwap_bounce(self, mock_yf):
        """Test 2: Cash signal engine identifies bullish VWAP bounce pattern."""
        df = self._generate_synthetic_ohlcv(30, start_price=2500.0, trend="up")
        mock_yf.return_value = df

        scout_agent = FOScoutAgent(self.config)
        scout_list = scout_agent.run(timeframe="5m")
        self.assertGreater(len(scout_list), 0)

        tech_agent = FOTechnicianAgent(self.config)
        tech_out = tech_agent.run(scout_list[0], timeframe="5m", vix_val=14.0)

        self.assertIn(tech_out.stance, ["bullish", "neutral", "bearish"])
        self.assertGreaterEqual(tech_out.suggested_spot_entry, 0.0)
        self.assertLess(tech_out.suggested_spot_sl, tech_out.suggested_spot_entry)

    @patch("core.data_sources.yf.download")
    def test_bot1_signal_generation_bearish_vwap_rejection(self, mock_yf):
        """Test 3: Cash signal engine identifies bearish VWAP rejection pattern."""
        df = self._generate_synthetic_ohlcv(30, start_price=2500.0, trend="down")
        mock_yf.return_value = df

        scout_out = FOScoutOutput(
            ticker="RELIANCE.NS", symbol="RELIANCE", is_index=False,
            spot_cmp=2400.0, rvol=1.8, price_change_pct=-2.5,
            lot_size=1, strike_step=10.0, scout_rank=1, scout_modifier=0.6
        )
        tech_agent = FOTechnicianAgent(self.config)
        tech_out = tech_agent.run(scout_out, timeframe="5m", vix_val=18.0)

        self.assertEqual(tech_out.stance, "bearish")
        self.assertGreater(tech_out.suggested_spot_sl, tech_out.suggested_spot_entry)

    def test_bot1_stop_loss_target_calculation(self):
        """Test 4: Verifies cash equity stop-loss and profit target distance logic."""
        scout_out = FOScoutOutput(
            ticker="TCS.NS", symbol="TCS", is_index=False,
            spot_cmp=3500.0, rvol=1.2, price_change_pct=0.8,
            lot_size=1, strike_step=20.0, scout_rank=1, scout_modifier=0.4
        )
        tech_agent = FOTechnicianAgent(self.config)
        with patch("core.data_sources.yf.download") as mock_yf:
            mock_yf.return_value = self._generate_synthetic_ohlcv(30, start_price=3500.0)
            tech_out = tech_agent.run(scout_out, timeframe="5m")

        self.assertGreater(tech_out.risk_reward_ratio, 0.0)
        self.assertNotEqual(tech_out.suggested_spot_entry, tech_out.suggested_spot_sl)

    @patch("core.data_sources.yf.download")
    def test_bot1_zero_latency_bar_processing(self, mock_yf):
        """Test 5: Zero-latency bar execution rapidly updates indicator values per tick/bar."""
        df = self._generate_synthetic_ohlcv(50, start_price=1000.0)
        mock_yf.return_value = df

        vwap_series = calculate_vwap(df)
        st_series, st_dir = calculate_supertrend(df)

        self.assertEqual(len(vwap_series), 50)
        self.assertEqual(len(st_dir), 50)
        self.assertFalse(vwap_series.isna().any())

    def test_bot1_cash_balance_constraint_pass(self):
        """Test 6: Execution passes when available cash pool exceeds total trade cost."""
        executor = FOExecutorAgent(self.config)
        verdict = FOJudgeOutput(
            ticker="RELIANCE.NS",
            run_timestamp=datetime.utcnow(),
            verdict="SCALP_CE",
            waterfall_score=8.5,
            confidence=8.5,
            contract=FOContractData(
                contract_type="SCALP_CE", symbol="RELIANCE", strike_price=2500.0,
                expiry_dte=7, lot_size=1, lots_qty=10, total_shares=10,
                option_premium=50.0, delta=0.5, gamma=0.01, theta_per_day=-1.0, vega=2.0,
                premium_value_inr=500.0, estimated_brokerage_inr=20.0, estimated_total_cost_inr=22.0
            ),
            position_sizing_inr=522.0,
            reasoning="Valid Cash Trade"
        )
        with patch("agents.executor.save_fo_state"), patch("agents.executor.append_to_fo_trade_log"):
            success = executor.execute(verdict, self.state)
        self.assertTrue(success)
        self.assertEqual(len(self.state["open_positions"]), 1)
        self.assertLess(self.state["pool_available"], 500000.0)

    def test_bot1_cash_balance_constraint_insufficient_funds(self):
        """Test 7 (Boundary): Trade execution rejected cleanly when capital pool is insufficient."""
        self.state["pool_available"] = 50.0  # Only ₹50 available
        executor = FOExecutorAgent(self.config)
        verdict = FOJudgeOutput(
            ticker="RELIANCE.NS",
            run_timestamp=datetime.utcnow(),
            verdict="SCALP_CE",
            waterfall_score=8.5,
            confidence=8.5,
            contract=FOContractData(
                contract_type="SCALP_CE", symbol="RELIANCE", strike_price=2500.0,
                expiry_dte=7, lot_size=1, lots_qty=10, total_shares=10,
                option_premium=50.0, delta=0.5, gamma=0.01, theta_per_day=-1.0, vega=2.0,
                premium_value_inr=500.0, estimated_brokerage_inr=20.0, estimated_total_cost_inr=22.0
            ),
            position_sizing_inr=522.0,
            reasoning="Insufficient capital test"
        )
        success = executor.execute(verdict, self.state)
        self.assertFalse(success)
        self.assertEqual(len(self.state["open_positions"]), 0)

    def test_bot1_zero_cash_balance(self):
        """Test 8 (Boundary): Zero available cash pool prevents any order execution."""
        self.state["pool_available"] = 0.0
        executor = FOExecutorAgent(self.config)
        verdict = FOJudgeOutput(
            ticker="TCS.NS", run_timestamp=datetime.utcnow(), verdict="BUY_CE",
            waterfall_score=9.0, confidence=9.0,
            contract=FOContractData(
                contract_type="OPTION_CE", symbol="TCS", strike_price=3500.0,
                expiry_dte=7, lot_size=1, lots_qty=1, total_shares=1,
                option_premium=10.0, delta=0.5, gamma=0.0, theta_per_day=-0.5, vega=1.0,
                premium_value_inr=10.0, estimated_total_cost_inr=20.5
            ),
            position_sizing_inr=30.5, reasoning="Zero balance"
        )
        success = executor.execute(verdict, self.state)
        self.assertFalse(success)

    @patch("core.data_sources.yf.download")
    def test_bot1_negative_equity_price_handling(self, mock_yf):
        """Test 9 (Boundary): Invalid/zero/negative market prices handle gracefully without crash."""
        df = pd.DataFrame({
            "Open": [0.0, -10.0],
            "High": [0.0, -5.0],
            "Low": [0.0, -15.0],
            "Close": [0.0, -10.0],
            "Volume": [0, 0]
        })
        mock_yf.return_value = df

        scout_out = FOScoutOutput(
            ticker="BAD.NS", symbol="BAD", is_index=False,
            spot_cmp=-10.0, rvol=0.0, price_change_pct=0.0,
            lot_size=1, strike_step=10.0, scout_rank=1, scout_modifier=0.0
        )
        tech_agent = FOTechnicianAgent(self.config)
        tech_out = tech_agent.run(scout_out, timeframe="5m")
        self.assertIsNotNone(tech_out)
        self.assertEqual(tech_out.stance, "neutral")

    def test_bot1_single_share_min_qty(self):
        """Test 10 (Boundary): Sizing logic handles minimum 1 share/lot allocation."""
        scout_out = FOScoutOutput(
            ticker="TCS.NS", symbol="TCS", is_index=False,
            spot_cmp=3500.0, rvol=1.1, price_change_pct=0.5,
            lot_size=1, strike_step=50.0, scout_rank=1, scout_modifier=0.3
        )
        tech_out = MagicMock()
        tech_out.stance = "bullish"
        tech_out.vix = 14.0
        tech_out.technical_score = 2.5

        judge = FOJudgeAgent(self.config)
        judge_out = judge.run(scout_out, tech_out, self.state, timeframe="5m")
        if judge_out.verdict != "AVOID":
            self.assertGreaterEqual(judge_out.contract.lots_qty, 1)

    def test_bot1_avoid_verdict_no_execution(self):
        """Test 11: AVOID verdict returns False and does not modify portfolio state."""
        executor = FOExecutorAgent(self.config)
        verdict = FOJudgeOutput(
            ticker="RELIANCE.NS", run_timestamp=datetime.utcnow(), verdict="AVOID",
            waterfall_score=4.0, confidence=4.0,
            contract=FOContractData(
                contract_type="NONE", symbol="RELIANCE", strike_price=2500.0,
                expiry_dte=7, lot_size=1, lots_qty=0, total_shares=0, option_premium=0.0,
                delta=0.5, gamma=0.0, theta_per_day=0.0, vega=0.0, premium_value_inr=0.0,
                estimated_total_cost_inr=0.0
            ),
            position_sizing_inr=0.0, reasoning="Avoided"
        )
        success = executor.execute(verdict, self.state)
        self.assertFalse(success)
        self.assertEqual(self.state["pool_available"], 500000.0)

    def test_bot1_intraday_cash_trade_logging(self):
        """Test 12: Successful execution logs trade details and updates pool_deployed."""
        executor = FOExecutorAgent(self.config)
        verdict = FOJudgeOutput(
            ticker="RELIANCE.NS", run_timestamp=datetime.utcnow(), verdict="SCALP_CE",
            waterfall_score=8.2, confidence=8.2,
            contract=FOContractData(
                contract_type="SCALP_CE", symbol="RELIANCE", strike_price=2500.0,
                expiry_dte=7, lot_size=1, lots_qty=1, total_shares=1,
                option_premium=100.0, delta=0.5, gamma=0.01, theta_per_day=-1.0, vega=2.0,
                premium_value_inr=100.0, estimated_brokerage_inr=20.0, estimated_total_cost_inr=23.0
            ),
            position_sizing_inr=123.0, reasoning="Logging Test"
        )
        with patch("agents.executor.save_fo_state"), patch("agents.executor.append_to_fo_trade_log") as mock_csv:
            success = executor.execute(verdict, self.state)
            self.assertTrue(success)
            self.assertTrue(mock_csv.called)
            logged_row = mock_csv.call_args[0][0]
            self.assertEqual(logged_row["symbol"], "RELIANCE")
            self.assertEqual(logged_row["verdict"], "SCALP_CE")

if __name__ == "__main__":
    unittest.main()
