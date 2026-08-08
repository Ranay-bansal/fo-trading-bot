import unittest
from unittest.mock import patch, MagicMock
import os
import json
import tempfile
from datetime import datetime, timezone, timedelta

from core.schemas import FOJudgeOutput, FOContractData
from agents.executor import FOExecutorAgent
from core.state import load_fo_state, save_fo_state, append_to_fo_trade_log

class TestFOExecutor(unittest.TestCase):
    """
    Tier 1 & Tier 2 Test Suite for FOExecutorAgent.
    Covers order execution, margin deductions, CSV trade logging, real-time position monitoring,
    3:15 PM IST auto square-off, P&L realization, and edge cases.
    """

    def setUp(self):
        import core.state
        core.state.DEFAULT_STATE["open_positions"] = []
        core.state.DEFAULT_STATE["total_brokerage_paid_inr"] = 0.0
        core.state.DEFAULT_STATE["daily_pnl_inr"] = 0.0
        self.config = {
            "project_name": "AlphaDesk Executor Test",
            "capital": {
                "initial_pool_inr": 500000.0,
                "brokerage_per_order_inr": 20.0
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

    def _create_sample_verdict(self, symbol="NIFTY", verdict="SCALP_CE", premium=150.0, lot_size=25, lots=2):
        total_shares = lot_size * lots
        premium_val = premium * total_shares
        return FOJudgeOutput(
            ticker=f"^NSE{symbol}",
            run_timestamp=datetime.utcnow(),
            verdict=verdict,
            waterfall_score=8.5,
            confidence=8.5,
            contract=FOContractData(
                contract_type="SCALP_CE", symbol=symbol, strike_price=24000.0,
                expiry_dte=7, lot_size=lot_size, lots_qty=lots, total_shares=total_shares,
                option_premium=premium, delta=0.5, gamma=0.01, theta_per_day=-2.0, vega=5.0,
                premium_value_inr=premium_val, estimated_brokerage_inr=20.0, estimated_total_cost_inr=premium_val*0.001 + 20.0
            ),
            position_sizing_inr=premium_val + 20.0,
            reasoning="Sample Executor Verdict"
        )

    def test_executor_successful_order_execution(self):
        """Test 1: Successful execution deducts margin, adds open position, and updates state."""
        executor = FOExecutorAgent(self.config)
        verdict = self._create_sample_verdict()

        with patch("agents.executor.save_fo_state"), patch("agents.executor.append_to_fo_trade_log"):
            success = executor.execute(verdict, self.state)

        self.assertTrue(success)
        self.assertEqual(len(self.state["open_positions"]), 1)
        self.assertEqual(self.state["trades_today"], 1)
        self.assertEqual(self.state["total_brokerage_paid_inr"], 20.0)
        self.assertLess(self.state["pool_available"], 500000.0)

    def test_executor_run_id_generation(self):
        """Test 2: Order execution generates valid formatted run_id."""
        executor = FOExecutorAgent(self.config)
        verdict = self._create_sample_verdict(symbol="BANKNIFTY", verdict="BUY_CE")

        with patch("agents.executor.save_fo_state"), patch("agents.executor.append_to_fo_trade_log") as mock_csv:
            executor.execute(verdict, self.state)
            self.assertTrue(mock_csv.called)
            row = mock_csv.call_args[0][0]
            self.assertIn("BANKNIFTY", row["run_id"])
            self.assertIn("SCALP_CE", row["run_id"])

    def test_executor_csv_log_appending(self):
        """Test 3: Executed trade appends complete dict with required CSV log fields."""
        executor = FOExecutorAgent(self.config)
        verdict = self._create_sample_verdict(symbol="RELIANCE", verdict="SCALP_CE")

        with patch("agents.executor.save_fo_state"), patch("agents.executor.append_to_fo_trade_log") as mock_csv:
            executor.execute(verdict, self.state)
            row = mock_csv.call_args[0][0]
            expected_keys = ["run_id", "ticker", "symbol", "verdict", "contract_type", "strike_price",
                             "lots", "total_shares", "spot_entry", "option_premium", "spot_sl", "spot_target",
                             "waterfall_score", "position_value_inr", "brokerage_fee_inr", "total_cost_inr", "executed_at"]
            for key in expected_keys:
                self.assertIn(key, row)

    def test_executor_open_position_schema(self):
        """Test 4: Open position dict matches schema requirements."""
        executor = FOExecutorAgent(self.config)
        verdict = self._create_sample_verdict(symbol="INFY", verdict="BUY_PE")

        with patch("agents.executor.save_fo_state"), patch("agents.executor.append_to_fo_trade_log"):
            executor.execute(verdict, self.state)

        pos = self.state["open_positions"][0]
        self.assertEqual(pos["symbol"], "INFY")
        self.assertEqual(pos["brokerage_paid_inr"], 20.0)
        self.assertIn("sl_spot", pos)
        self.assertIn("target_spot", pos)

    def test_executor_auto_squareoff_315_pm(self):
        """Test 5: Position monitor triggers auto square-off after 3:15 PM IST on weekday."""
        executor = FOExecutorAgent(self.config)
        self.state["open_positions"].append({
            "ticker": "RELIANCE.NS", "contract_type": "SCALP_CE", "symbol": "RELIANCE",
            "strike_price": 2500.0, "lots": 1, "total_shares": 250, "entry_premium": 50.0,
            "entry_spot": 12500.0, "sl_spot": 12000.0, "target_spot": 13000.0,
            "entered_at": datetime.utcnow().isoformat() + "Z", "megabull_order_id": "RELIANCE_1",
            "brokerage_paid_inr": 20.0
        })

        # Mock IST weekday at 15:20
        mock_now = datetime(2026, 8, 7, 15, 20, tzinfo=timezone(timedelta(hours=5, minutes=30)))
        with patch("agents.executor.datetime") as mock_dt, patch("agents.executor.save_fo_state"):
            mock_dt.now.return_value = mock_now
            executor.monitor_positions(self.state)

        self.assertEqual(len(self.state["open_positions"]), 0)

    def test_executor_squareoff_realized_pnl_update(self):
        """Test 6: Square-off calculates gross P&L, deducts exit brokerage ₹20, and updates daily P&L."""
        executor = FOExecutorAgent(self.config)
        entry_val = 50.0 * 250  # ₹12,500
        self.state["pool_deployed"] = entry_val
        self.state["pool_available"] = 500000.0 - entry_val
        self.state["total_brokerage_paid_inr"] = 0.0
        self.state["daily_pnl_inr"] = 0.0
        self.state["open_positions"] = [{
            "ticker": "RELIANCE.NS", "contract_type": "SCALP_CE", "symbol": "RELIANCE",
            "strike_price": 2500.0, "lots": 1, "total_shares": 250, "entry_premium": 50.0,
            "entry_spot": 12500.0, "sl_spot": 12000.0, "target_spot": 13000.0,
            "entered_at": datetime.utcnow().isoformat() + "Z", "megabull_order_id": "RELIANCE_1",
            "brokerage_paid_inr": 20.0
        }]

        mock_costs = {"total_cost": 23.76, "brokerage": 20.0, "stt": 1.0, "exchange_fee": 1.0, "gst": 1.76, "sebi": 0.0}
        with patch("agents.executor.save_fo_state"), patch.object(executor, "_get_live_spot", return_value=12600.0), patch.object(executor.options_engine, "calculate_trade_costs", return_value=mock_costs):
            executor.squareoff_all(self.state)

        self.assertEqual(self.state["pool_deployed"], 0.0)
        self.assertEqual(len(self.state["open_positions"]), 0)
        self.assertEqual(self.state["total_brokerage_paid_inr"], 23.76)
        self.assertGreater(self.state["daily_pnl_inr"], 0.0)

    def test_executor_no_positions_monitor_noop(self):
        """Test 7: Position monitor cleanly returns early when open_positions is empty."""
        executor = FOExecutorAgent(self.config)
        executor.monitor_positions(self.state)
        self.assertEqual(len(self.state["open_positions"]), 0)

    def test_executor_avoid_verdict_ignored(self):
        """Test 8: AVOID verdict produces False and modifies nothing."""
        executor = FOExecutorAgent(self.config)
        verdict = FOJudgeOutput(
            ticker="NIFTY", run_timestamp=datetime.utcnow(), verdict="AVOID",
            waterfall_score=3.0, confidence=3.0,
            contract=FOContractData(
                contract_type="NONE", symbol="NIFTY", strike_price=24000.0,
                expiry_dte=7, lot_size=25, lots_qty=0, total_shares=0,
                option_premium=0.0, delta=0.0, gamma=0.0, theta_per_day=0.0, vega=0.0,
                premium_value_inr=0.0, estimated_total_cost_inr=0.0
            ),
            position_sizing_inr=0.0, reasoning="Avoid"
        )
        success = executor.execute(verdict, self.state)
        self.assertFalse(success)
        self.assertEqual(self.state["pool_available"], 500000.0)

    def test_executor_multiple_position_executions(self):
        """Test 9: Multiple trades add distinct open position records."""
        executor = FOExecutorAgent(self.config)
        v1 = self._create_sample_verdict(symbol="NIFTY", verdict="SCALP_CE")
        v2 = self._create_sample_verdict(symbol="BANKNIFTY", verdict="BUY_PE")

        with patch("agents.executor.save_fo_state"), patch("agents.executor.append_to_fo_trade_log"):
            executor.execute(v1, self.state)
            executor.execute(v2, self.state)

        self.assertEqual(len(self.state["open_positions"]), 2)
        symbols = [p["symbol"] for p in self.state["open_positions"]]
        self.assertIn("NIFTY", symbols)
        self.assertIn("BANKNIFTY", symbols)

    def test_executor_insufficient_available_margin(self):
        """Test 10 (Boundary): Insufficient funds prevents trade execution."""
        self.state["pool_available"] = 100.0
        executor = FOExecutorAgent(self.config)
        verdict = self._create_sample_verdict(premium=200.0, lot_size=25, lots=1)  # Requires ~3,800 INR

        success = executor.execute(verdict, self.state)
        self.assertFalse(success)
        self.assertEqual(len(self.state["open_positions"]), 0)

    def test_executor_zero_positions_squareoff(self):
        """Test 11 (Boundary): Calling squareoff_all with 0 positions exits safely."""
        executor = FOExecutorAgent(self.config)
        with patch("agents.executor.save_fo_state"):
            executor.squareoff_all(self.state)
        self.assertEqual(self.state["pool_deployed"], 0.0)

    def test_executor_weekend_timing_check(self):
        """Test 12 (Boundary): Position monitor skips auto square-off during weekend hours."""
        executor = FOExecutorAgent(self.config)
        self.state["open_positions"] = [{
            "ticker": "RELIANCE.NS", "contract_type": "SCALP_CE", "symbol": "RELIANCE",
            "strike_price": 2500.0, "lots": 1, "total_shares": 250, "entry_premium": 50.0,
            "entry_spot": 12500.0, "sl_spot": 12000.0, "target_spot": 13000.0,
            "entered_at": datetime.utcnow().isoformat() + "Z", "megabull_order_id": "RELIANCE_1",
            "brokerage_paid_inr": 20.0
        }]

        # Mock Saturday at 16:00 IST and mock spot price equal to entry spot so SL is not triggered
        mock_saturday = datetime(2026, 8, 8, 16, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
        with patch("agents.executor.datetime") as mock_dt, patch.object(executor, "_get_live_spot", return_value=12500.0):
            mock_dt.now.return_value = mock_saturday
            executor.monitor_positions(self.state)

        # Positions remain open because it's weekend and SL/TP not hit
        self.assertEqual(len(self.state["open_positions"]), 1)

if __name__ == "__main__":
    unittest.main()
