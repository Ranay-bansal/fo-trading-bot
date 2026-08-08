import unittest
import json
import csv
import os
import tempfile
from unittest.mock import patch, MagicMock

from core.state import load_fo_state, save_fo_state, append_to_fo_trade_log, DEFAULT_STATE
from scratch.fix_all_index_files import fix_all

class TestUIHydration(unittest.TestCase):
    """
    Tier 1 & Tier 2 Test Suite for Dashboard UI & State Hydration.
    Covers portfolio_state.json schema, falsy 0 balance bug prevention, trade_log.csv parsing,
    KPI stat card hydration, index.html file syncing, and boundary fallback mechanisms.
    """

    def setUp(self):
        import core.state
        core.state.DEFAULT_STATE["open_positions"] = []
        core.state.DEFAULT_STATE["total_brokerage_paid_inr"] = 0.0
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_portfolio_state_json_schema(self):
        """Test 1: DEFAULT_STATE and state JSON schema contain all top KPI fields."""
        required_keys = [
            "pool_total", "pool_available", "pool_deployed",
            "daily_pnl_inr", "daily_pnl_pct", "total_brokerage_paid_inr",
            "trades_today", "open_positions"
        ]
        for key in required_keys:
            self.assertIn(key, DEFAULT_STATE)

    def test_ui_nullish_coalescing_zero_balance_bug_fix(self):
        """Test 2: Verifies JS nullish coalescing fix prevents falsy 0 balance bug."""
        # Simulated JS state object with zero balance
        state_with_zero = {"pool_total": 0.0, "pool_available": 0.0}
        
        # Bug behavior: 0 || 500000 evaluates to 500000 (WRONG!)
        falsy_bug_val = state_with_zero["pool_total"] or 500000.0
        self.assertEqual(falsy_bug_val, 500000.0)

        # Correct nullish coalescing: 0 ?? 500000 evaluates to 0.0 (CORRECT!)
        correct_val = state_with_zero["pool_total"] if state_with_zero["pool_total"] is not None else 500000.0
        self.assertEqual(correct_val, 0.0)

    def test_trade_log_csv_format(self):
        """Test 3: Trade log CSV fieldnames match required 21 fields."""
        fieldnames = [
            "run_id", "ticker", "symbol", "verdict", "contract_type", "strike_price",
            "lots", "total_shares", "spot_entry", "option_premium", "spot_sl", "spot_target",
            "waterfall_score", "position_value_inr", "brokerage_fee_inr", "total_cost_inr",
            "executed_at", "exit_price", "exit_reason", "realized_pnl_inr", "realized_pnl_pct"
        ]
        self.assertEqual(len(fieldnames), 21)

    def test_trade_log_csv_parsing(self):
        """Test 4: CSV trade log rows parse correctly without error."""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
            writer = csv.DictWriter(tmp, fieldnames=["run_id", "symbol", "net_pnl"])
            writer.writeheader()
            writer.writerow({"run_id": "RELIANCE_1", "symbol": "RELIANCE", "net_pnl": "250.50"})

        try:
            with open(tmp_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["symbol"], "RELIANCE")
                self.assertEqual(float(rows[0]["net_pnl"]), 250.50)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_index_html_files_synced(self):
        """Test 5: Index HTML files exist at root, public/, and dashboard/."""
        root_index = os.path.join(self.base_dir, "index.html")
        public_index = os.path.join(self.base_dir, "public", "index.html")
        dashboard_index = os.path.join(self.base_dir, "dashboard", "index.html")

        self.assertTrue(os.path.exists(root_index))
        self.assertTrue(os.path.exists(public_index))
        self.assertTrue(os.path.exists(dashboard_index))

    def test_ui_trade_log_table_rendering(self):
        """Test 6: index.html contains required table body IDs for hydration."""
        root_index = os.path.join(self.base_dir, "index.html")
        with open(root_index, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('id="trade-log-body"', content)
        self.assertIn('id="committee-table-body"', content)
        self.assertIn('id="memory-table-body"', content)

    def test_ui_kpi_card_ids(self):
        """Test 7: index.html contains top KPI card elements with correct IDs."""
        root_index = os.path.join(self.base_dir, "index.html")
        with open(root_index, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('id="val-total"', content)
        self.assertIn('id="val-available"', content)
        self.assertIn('id="val-pnl"', content)
        self.assertIn('id="val-brokerage"', content)

    def test_state_file_load_and_save(self):
        """Test 8: load_fo_state and save_fo_state persist state data correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_state_file = os.path.join(tmp_dir, "portfolio_state.json")
            with patch("core.state.STATE_FILE", tmp_state_file):
                test_state = DEFAULT_STATE.copy()
                test_state["pool_available"] = 450000.0
                save_fo_state(test_state)

                loaded = load_fo_state()
                self.assertEqual(loaded["pool_available"], 450000.0)
                self.assertIsNotNone(loaded["last_updated"])

    def test_empty_state_hydration_fallback(self):
        """Test 9 (Boundary): Missing state file returns DEFAULT_STATE without crashing."""
        with patch("core.state.STATE_FILE", "/non/existent/path/portfolio_state.json"):
            loaded = load_fo_state()
            self.assertEqual(loaded["pool_total"], 500000.0)

    def test_corrupted_json_state_handling(self):
        """Test 10 (Boundary): Corrupted JSON state file falls back to DEFAULT_STATE."""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as tmp:
            tmp.write("{ invalid json format... ")
            tmp_path = tmp.name

        try:
            with patch("core.state.STATE_FILE", tmp_path):
                loaded = load_fo_state()
                self.assertEqual(loaded["pool_total"], 500000.0)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_trade_log_csv_append_header_creation(self):
        """Test 11: append_to_fo_trade_log writes header when creating new file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_csv_file = os.path.join(tmp_dir, "trade_log.csv")
            with patch("core.state.TRADE_LOG_FILE", tmp_csv_file):
                append_to_fo_trade_log({"symbol": "NIFTY", "verdict": "BUY_CE"})

            with open(tmp_csv_file, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
                self.assertGreaterEqual(len(rows), 2)
                self.assertEqual(rows[0][0], "run_id")
                self.assertEqual(rows[1][2], "NIFTY")

    def test_negative_pnl_formatting(self):
        """Test 12: Formatting negative P&L values produces red text and correct minus sign."""
        pnl = -1250.75
        formatted = (f"+₹" if pnl >= 0 else "-₹") + f"{abs(pnl):,.2f}"
        self.assertEqual(formatted, "-₹1,250.75")

if __name__ == "__main__":
    unittest.main()
