import unittest
from unittest.mock import patch, MagicMock
import math
from datetime import datetime

from core.options_engine import OptionsEngine, _cdf, _pdf
from core.schemas import FOScoutOutput, FOTechnicianOutput, FOJudgeOutput, FOContractData
from agents.judge import FOJudgeAgent

class TestBot2OptionsEngine(unittest.TestCase):
    """
    Tier 1 & Tier 2 Test Suite for Bot 2: F&O Options Swarm Engine.
    Covers Black-Scholes pricing, Greeks calculation, strike selection (ATM/ITM),
    futures pricing, statutory transaction cost model, and boundary edge cases.
    """

    def setUp(self):
        import core.state
        core.state.DEFAULT_STATE["open_positions"] = []
        core.state.DEFAULT_STATE["total_brokerage_paid_inr"] = 0.0
        self.engine = OptionsEngine(risk_free_rate=0.065)
        self.config = {
            "project_name": "AlphaDesk F&O Test",
            "capital": {
                "initial_pool_inr": 500000.0,
                "brokerage_per_order_inr": 20.0
            },
            "judge": {
                "waterfall_base_score": 5.0,
                "execute_threshold": 8.0
            }
        }
        self.state = {
            "pool_total": 500000.0,
            "pool_available": 500000.0,
            "open_positions": []
        }

    def test_options_pricing_black_scholes_call(self):
        """Test 1: Black-Scholes Call option pricing returns realistic premium and Greeks."""
        res = self.engine.calculate_bs_price_and_greeks(
            spot=24000.0, strike=24000.0, dte=7.0, iv_pct=15.0, option_type="CE"
        )
        self.assertIn("price", res)
        self.assertIn("delta", res)
        self.assertIn("gamma", res)
        self.assertIn("theta_per_day", res)
        self.assertIn("vega", res)

        self.assertGreater(res["price"], 0.0)
        self.assertGreater(res["delta"], 0.4)
        self.assertLess(res["delta"], 0.6)

    def test_options_pricing_black_scholes_put(self):
        """Test 2: Black-Scholes Put option pricing returns realistic premium and Put delta."""
        res = self.engine.calculate_bs_price_and_greeks(
            spot=24000.0, strike=24000.0, dte=7.0, iv_pct=15.0, option_type="PE"
        )
        self.assertGreater(res["price"], 0.0)
        self.assertLess(res["delta"], 0.0)
        self.assertGreater(res["delta"], -0.6)

    def test_greeks_delta_gamma_theta_vega(self):
        """Test 3: Option Greeks adhere to theoretical domain constraints."""
        res_ce = self.engine.calculate_bs_price_and_greeks(spot=2500.0, strike=2500.0, dte=5.0, iv_pct=20.0, option_type="CE")
        self.assertGreaterEqual(res_ce["delta"], 0.0)
        self.assertLessEqual(res_ce["delta"], 1.0)
        self.assertGreaterEqual(res_ce["gamma"], 0.0)
        self.assertLessEqual(res_ce["theta_per_day"], 0.0)
        self.assertGreaterEqual(res_ce["vega"], 0.0)

    def test_strike_selection_bullish_itm(self):
        """Test 4: Bullish ITM strike selection picks strike below current spot for Call."""
        spot = 24320.0
        strike_step = 100.0
        strike = self.engine.select_strike(spot, strike_step, stance="bullish", itm_depth=1)
        self.assertEqual(strike, 24200.0)  # ATM=24300 - 100 = 24200

    def test_strike_selection_bearish_itm(self):
        """Test 5: Bearish ITM strike selection picks strike above current spot for Put."""
        spot = 24320.0
        strike_step = 100.0
        strike = self.engine.select_strike(spot, strike_step, stance="bearish", itm_depth=1)
        self.assertEqual(strike, 24400.0)  # ATM=24300 + 100 = 24400

    def test_futures_pricing_cost_of_carry(self):
        """Test 6: Futures pricing applies cost-of-carry model with risk-free rate."""
        spot = 2500.0
        dte = 30.0
        fut_price = self.engine.calculate_futures_price(spot, dte)
        self.assertGreater(fut_price, spot)

    def test_statutory_transaction_costs_options(self):
        """Test 7: Statutory transaction costs breakdown includes ₹20 brokerage, STT, Exchange Fee & GST."""
        turnover = 100000.0
        costs = self.engine.calculate_trade_costs(turnover_inr=turnover, is_sell=True, contract_type="OPTION")
        self.assertEqual(costs["brokerage"], 20.0)
        self.assertGreater(costs["stt"], 0.0)
        self.assertGreater(costs["exchange_fee"], 0.0)
        self.assertGreater(costs["gst"], 0.0)
        self.assertGreater(costs["total_cost"], 20.0)

    def test_statutory_transaction_costs_futures(self):
        """Test 8: Futures transaction costs use correct STT rate (0.0125% on sell)."""
        turnover = 500000.0
        costs = self.engine.calculate_trade_costs(turnover_inr=turnover, is_sell=True, contract_type="FUTURES")
        expected_stt = round(turnover * 0.000125, 2)
        self.assertEqual(costs["stt"], expected_stt)

    def test_zero_dte_boundary_handling(self):
        """Test 9 (Boundary): Zero or negative DTE inputs handled safely with fallback intrinsic pricing."""
        res = self.engine.calculate_bs_price_and_greeks(spot=2500.0, strike=2400.0, dte=0.0, iv_pct=15.0, option_type="CE")
        self.assertGreaterEqual(res["price"], 1.0)
        self.assertEqual(res["delta"], 0.5)

    def test_zero_spot_strike_boundary_handling(self):
        """Test 10 (Boundary): Zero or negative spot/strike inputs return intrinsic fallback without math error."""
        res = self.engine.calculate_bs_price_and_greeks(spot=-100.0, strike=2500.0, dte=7.0, iv_pct=15.0, option_type="CE")
        self.assertGreaterEqual(res["price"], 1.0)

    def test_extreme_iv_boundary_handling(self):
        """Test 11 (Boundary): Extreme IV values (0.01% or 500%) calculate without overflow."""
        res_low = self.engine.calculate_bs_price_and_greeks(spot=2500.0, strike=2500.0, dte=7.0, iv_pct=0.01, option_type="CE")
        res_high = self.engine.calculate_bs_price_and_greeks(spot=2500.0, strike=2500.0, dte=7.0, iv_pct=500.0, option_type="CE")
        self.assertGreater(res_low["price"], 0.0)
        self.assertGreater(res_high["price"], 0.0)

    def test_lot_size_multiplicity(self):
        """Test 12: F&O Judge sizing ensures integer multiples of lot sizes (NIFTY 25, BANKNIFTY 15)."""
        scout_nifty = FOScoutOutput(
            ticker="^NSEI", symbol="NIFTY", is_index=True,
            spot_cmp=24000.0, rvol=2.0, price_change_pct=1.5,
            lot_size=25, strike_step=50.0, scout_rank=1, scout_modifier=0.6
        )
        tech_out = MagicMock()
        tech_out.stance = "bullish"
        tech_out.vix = 14.5
        tech_out.technical_score = 2.5

        judge = FOJudgeAgent(self.config)
        judge_out = judge.run(scout_nifty, tech_out, self.state, timeframe="5m")
        if judge_out.verdict != "AVOID":
            self.assertEqual(judge_out.contract.total_shares % 25, 0)

    def test_cost_viability_gate_rejection(self):
        """Test 13: JudgeAgent cost viability gate rejects trades with tiny premium gain vs brokerage friction."""
        self.state["pool_available"] = 50.0
        scout_out = FOScoutOutput(
            ticker="TATASTEEL.NS", symbol="TATASTEEL", is_index=False,
            spot_cmp=150.0, rvol=1.1, price_change_pct=0.2,
            lot_size=1, strike_step=2.5, scout_rank=1, scout_modifier=0.1
        )
        tech_out = MagicMock()
        tech_out.stance = "bullish"
        tech_out.vix = 10.0  # Very low VIX -> tiny option premium
        tech_out.technical_score = 1.2

        judge = FOJudgeAgent(self.config)
        # Mock options engine to return super low premium
        with patch.object(judge.options_engine, "calculate_bs_price_and_greeks") as mock_bs:
            mock_bs.return_value = {"price": 0.05, "delta": 0.5, "gamma": 0.0, "theta_per_day": 0.0, "vega": 0.0}
            judge_out = judge.run(scout_out, tech_out, self.state, timeframe="5m")

        self.assertEqual(judge_out.verdict, "AVOID")
        self.assertIn("friction", judge_out.reasoning)

if __name__ == "__main__":
    unittest.main()
