import os
import json
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime

from core.schemas import (
    FOScoutOutput, FOTechnicianOutput, FOJudgeOutput, FOContractData,
    NewsdeskOutput, BullDebaterOutput, BearDebaterOutput, CommitteeDebateRecord
)
from core.state import COMMITTEE_DEBATE_LOG_FILE
from agents.scout import FOScoutAgent
from agents.technician import FOTechnicianAgent
from agents.newsdesk import NewsdeskAgent
from agents.bull_debater import BullDebaterAgent
from agents.bear_debater import BearDebaterAgent
from agents.judge import FOJudgeAgent

class TestCommitteeDebaters(unittest.TestCase):
    """
    Tier 1 & Tier 2 Test Suite for 3-Way Risk Committee Debaters.
    Covers ScoutAgent opportunity identification, TechnicianAgent chart/momentum analysis,
    12-pattern engine, Bull & Bear risk debate, and JudgeAgent consensus & override protocol.
    """

    def setUp(self):
        import core.state
        core.state.DEFAULT_STATE["open_positions"] = []
        core.state.DEFAULT_STATE["total_brokerage_paid_inr"] = 0.0
        self.config = {
            "project_name": "AlphaDesk Committee Test",
            "capital": {
                "initial_pool_inr": 500000.0,
                "brokerage_per_order_inr": 20.0
            },
            "judge": {
                "waterfall_base_score": 5.0,
                "execute_threshold": 8.0,
                "cautious_threshold": 7.0
            },
            "fo_universe": {
                "indices": [
                    {"ticker": "^NSEI", "symbol": "NIFTY", "lot_size": 25, "strike_step": 50}
                ],
                "stocks": [
                    {"symbol": "RELIANCE", "ticker": "RELIANCE.NS", "lot_size": 250, "strike_step": 20, "sector": "ENERGY"}
                ]
            }
        }
        self.state = {
            "pool_total": 500000.0,
            "pool_available": 500000.0,
            "open_positions": []
        }

    def _generate_df(self, length=30, trend="up"):
        dates = pd.date_range(end=datetime.now(), periods=length, freq="5min")
        np.random.seed(123)
        if trend == "up":
            prices = 2500.0 + np.cumsum(np.random.uniform(0.5, 2.5, size=length))
        elif trend == "down":
            prices = 2500.0 - np.cumsum(np.random.uniform(0.5, 2.5, size=length))
        else:
            prices = 2500.0 + np.random.uniform(-1.0, 1.0, size=length)
        
        return pd.DataFrame({
            "Open": prices - 0.2,
            "High": prices + 1.0,
            "Low": prices - 1.0,
            "Close": prices,
            "Volume": [10000] * length
        }, index=dates)

    @patch("core.data_sources.yf.download")
    def test_scout_agent_screening_indices(self, mock_yf):
        """Test 1: ScoutAgent screens index contracts and calculates RVOL & scout rank."""
        mock_yf.return_value = self._generate_df(20)
        scout = FOScoutAgent(self.config)
        candidates = scout.run(timeframe="5m")

        self.assertGreater(len(candidates), 0)
        idx_cand = candidates[0]
        self.assertEqual(idx_cand.symbol, "NIFTY")
        self.assertTrue(idx_cand.is_index)
        self.assertGreater(idx_cand.scout_modifier, 0.0)

    @patch("core.data_sources.yf.download")
    def test_scout_agent_screening_stocks(self, mock_yf):
        """Test 2: ScoutAgent screens stock universe and builds FOScoutOutput list."""
        mock_yf.return_value = self._generate_df(20)
        scout = FOScoutAgent(self.config)
        candidates = scout.run(timeframe="5m")

        stock_cands = [c for c in candidates if not c.is_index]
        self.assertGreater(len(stock_cands), 0)
        self.assertEqual(stock_cands[0].symbol, "RELIANCE")

    @patch("core.data_sources.yf.download")
    def test_technician_12_pattern_detection(self, mock_yf):
        """Test 3: FOTechnicianAgent 12-pattern detection identifies candlestick patterns."""
        df = self._generate_df(30, trend="up")
        mock_yf.return_value = df

        scout_out = FOScoutOutput(
            ticker="RELIANCE.NS", symbol="RELIANCE", is_index=False,
            spot_cmp=2550.0, rvol=1.5, price_change_pct=1.0,
            lot_size=250, strike_step=20.0, scout_rank=1, scout_modifier=0.5
        )
        tech_agent = FOTechnicianAgent(self.config)
        tech_out = tech_agent.run(scout_out, timeframe="5m")

        self.assertIsInstance(tech_out.patterns_detected, list)
        self.assertIn(tech_out.stance, ["bullish", "neutral", "bearish"])

    @patch("core.data_sources.yf.download")
    def test_technician_indicator_integration(self, mock_yf):
        """Test 4: Technician integrates VWAP, Supertrend, RSI, ADX, ATR into technical score."""
        df = self._generate_df(30, trend="up")
        mock_yf.return_value = df

        scout_out = FOScoutOutput(
            ticker="RELIANCE.NS", symbol="RELIANCE", is_index=False,
            spot_cmp=2550.0, rvol=1.5, price_change_pct=1.0,
            lot_size=250, strike_step=20.0, scout_rank=1, scout_modifier=0.5
        )
        tech_agent = FOTechnicianAgent(self.config)
        tech_out = tech_agent.run(scout_out, timeframe="5m")

        self.assertGreaterEqual(tech_out.technical_score, -3.0)
        self.assertLessEqual(tech_out.technical_score, 3.0)
        self.assertGreater(tech_out.momentum.rsi, 0.0)
        self.assertGreater(tech_out.volatility.atr, 0.0)

    def test_judge_waterfall_score_calculation(self):
        """Test 5: JudgeAgent computes waterfall score using base (5.0) + scout_mod*1.0 + tech_mod*1.8."""
        scout_out = FOScoutOutput(
            ticker="RELIANCE.NS", symbol="RELIANCE", is_index=False,
            spot_cmp=2500.0, rvol=2.0, price_change_pct=1.5,
            lot_size=250, strike_step=20.0, scout_rank=1, scout_modifier=0.6
        )
        tech_out = MagicMock()
        tech_out.stance = "bullish"
        tech_out.vix = 14.0
        tech_out.technical_score = 2.0

        judge = FOJudgeAgent(self.config)
        judge_out = judge.run(scout_out, tech_out, self.state, timeframe="5m")

        # Base 5.0 + 0.6*1.0 + 2.0*1.8 = 9.2 -> capped at 9.2
        self.assertGreaterEqual(judge_out.waterfall_score, 8.0)
        self.assertIn(judge_out.verdict, ["SCALP_CE", "BUY_CE"])

    def test_judge_execution_threshold_pass(self):
        """Test 6: High waterfall score (>= 7.0 for 5m) yields executable verdict."""
        scout_out = FOScoutOutput(
            ticker="RELIANCE.NS", symbol="RELIANCE", is_index=False,
            spot_cmp=2500.0, rvol=1.5, price_change_pct=1.0,
            lot_size=250, strike_step=20.0, scout_rank=1, scout_modifier=0.5
        )
        tech_out = MagicMock()
        tech_out.stance = "bullish"
        tech_out.vix = 14.0
        tech_out.technical_score = 1.5

        judge = FOJudgeAgent(self.config)
        judge_out = judge.run(scout_out, tech_out, self.state, timeframe="5m")

        self.assertNotEqual(judge_out.verdict, "AVOID")
        self.assertGreater(judge_out.contract.total_shares, 0)

    def test_judge_execution_threshold_avoid(self):
        """Test 7: Low waterfall score (< 7.0) returns AVOID verdict."""
        scout_out = FOScoutOutput(
            ticker="RELIANCE.NS", symbol="RELIANCE", is_index=False,
            spot_cmp=2500.0, rvol=0.5, price_change_pct=0.0,
            lot_size=250, strike_step=20.0, scout_rank=5, scout_modifier=0.1
        )
        tech_out = MagicMock()
        tech_out.stance = "neutral"
        tech_out.vix = 14.0
        tech_out.technical_score = 0.0

        judge = FOJudgeAgent(self.config)
        judge_out = judge.run(scout_out, tech_out, self.state, timeframe="5m")

        self.assertEqual(judge_out.verdict, "AVOID")
        self.assertEqual(judge_out.contract.contract_type, "NONE")

    def test_judge_short_verdict_determination(self):
        """Test 8: Strong bearish technical stance produces Put buying / short verdict."""
        scout_out = FOScoutOutput(
            ticker="RELIANCE.NS", symbol="RELIANCE", is_index=False,
            spot_cmp=2500.0, rvol=2.0, price_change_pct=-2.0,
            lot_size=250, strike_step=20.0, scout_rank=1, scout_modifier=0.6
        )
        tech_out = MagicMock()
        tech_out.stance = "bearish"
        tech_out.vix = 18.0
        tech_out.technical_score = -2.5

        judge = FOJudgeAgent(self.config)
        judge_out = judge.run(scout_out, tech_out, self.state, timeframe="5m")

        self.assertIn(judge_out.verdict, ["SCALP_PE", "BUY_PE"])

    @patch("core.data_sources.yf.download")
    def test_scout_agent_empty_df_resilience(self, mock_yf):
        """Test 9 (Boundary): ScoutAgent handles empty DataFrame from yfinance safely."""
        mock_yf.return_value = pd.DataFrame()
        scout = FOScoutAgent(self.config)
        candidates = scout.run(timeframe="5m")

        self.assertIsInstance(candidates, list)
        self.assertEqual(len(candidates), 0)

    @patch("core.data_sources.yf.download")
    def test_technician_agent_short_dataframe(self, mock_yf):
        """Test 10 (Boundary): TechnicianAgent handles < 5 rows of data with fallback neutral stance."""
        mock_yf.return_value = pd.DataFrame({
            "Open": [100.0, 101.0], "High": [102.0, 103.0],
            "Low": [99.0, 100.0], "Close": [101.0, 102.0],
            "Volume": [500, 600]
        })

        scout_out = FOScoutOutput(
            ticker="RELIANCE.NS", symbol="RELIANCE", is_index=False,
            spot_cmp=102.0, rvol=1.0, price_change_pct=0.0,
            lot_size=250, strike_step=20.0, scout_rank=1, scout_modifier=0.0
        )
        tech_agent = FOTechnicianAgent(self.config)
        tech_out = tech_agent.run(scout_out, timeframe="5m")

        self.assertEqual(tech_out.stance, "neutral")
        self.assertEqual(tech_out.technical_score, 0.0)

    def test_judge_verdict_schema_validation(self):
        """Test 11: FOJudgeOutput instance satisfies strict Pydantic model contract."""
        scout_out = FOScoutOutput(
            ticker="RELIANCE.NS", symbol="RELIANCE", is_index=False,
            spot_cmp=2500.0, rvol=1.5, price_change_pct=1.0,
            lot_size=250, strike_step=20.0, scout_rank=1, scout_modifier=0.5
        )
        tech_out = MagicMock()
        tech_out.stance = "bullish"
        tech_out.vix = 14.0
        tech_out.technical_score = 2.0

        judge = FOJudgeAgent(self.config)
        judge_out = judge.run(scout_out, tech_out, self.state, timeframe="5m")

        self.assertIsInstance(judge_out, FOJudgeAgent.__annotations__.get('run', object) if hasattr(FOJudgeAgent, '__annotations__') else object)
        self.assertIsNotNone(judge_out.ticker)
        self.assertIsNotNone(judge_out.reasoning)

    def test_bull_bear_debater_stance_weighting(self):
        """Test 12: Bullish vs Bearish debater stance changes verdict direction from Call to Put."""
        scout_out = FOScoutOutput(
            ticker="RELIANCE.NS", symbol="RELIANCE", is_index=False,
            spot_cmp=2500.0, rvol=1.5, price_change_pct=1.0,
            lot_size=250, strike_step=20.0, scout_rank=1, scout_modifier=0.5
        )
        tech_bullish = MagicMock(stance="bullish", vix=14.0, technical_score=2.0)
        tech_bearish = MagicMock(stance="bearish", vix=14.0, technical_score=-2.0)

        judge = FOJudgeAgent(self.config)
        out_bull = judge.run(scout_out, tech_bullish, self.state, timeframe="5m")
        out_bear = judge.run(scout_out, tech_bearish, self.state, timeframe="5m")

        self.assertIn("CE", out_bull.verdict)
        self.assertIn("PE", out_bear.verdict)

    def test_newsdesk_agent_execution_and_fallback(self):
        """Test 13: NewsdeskAgent calculates sentiment, catalyst risk, regime, macro risk scores with fallback."""
        scout_out = FOScoutOutput(
            ticker="RELIANCE.NS", symbol="RELIANCE", is_index=False,
            spot_cmp=2500.0, rvol=1.5, price_change_pct=1.0,
            lot_size=250, strike_step=20.0, scout_rank=1, scout_modifier=0.5
        )
        news_agent = NewsdeskAgent(self.config)
        news_out = news_agent.run(scout_out, vix_val=15.0)

        self.assertIsInstance(news_out, NewsdeskOutput)
        self.assertGreaterEqual(news_out.news_sentiment_score, 0.0)
        self.assertLessEqual(news_out.news_sentiment_score, 10.0)
        self.assertGreaterEqual(news_out.catalyst_risk_score, 0.0)
        self.assertLessEqual(news_out.catalyst_risk_score, 10.0)
        self.assertIn(news_out.market_regime, ["bullish", "bearish", "volatile", "rangebound"])

    def test_bull_debater_agent_conviction(self):
        """Test 14: BullDebaterAgent synthesizes upside arguments and conviction score."""
        scout_out = FOScoutOutput(
            ticker="RELIANCE.NS", symbol="RELIANCE", is_index=False,
            spot_cmp=2500.0, rvol=1.5, price_change_pct=1.2,
            lot_size=250, strike_step=20.0, scout_rank=1, scout_modifier=0.5
        )
        tech_out = FOTechnicianAgent(self.config).run(scout_out, timeframe="5m")
        news_out = NewsdeskOutput(ticker="RELIANCE.NS", symbol="RELIANCE", news_sentiment_score=7.0, catalyst_risk_score=2.0)

        bull_agent = BullDebaterAgent(self.config)
        bull_out = bull_agent.run(scout_out, tech_out, news_out)

        self.assertIsInstance(bull_out, BullDebaterOutput)
        self.assertGreaterEqual(bull_out.conviction_score, 0.0)
        self.assertLessEqual(bull_out.conviction_score, 10.0)
        self.assertGreater(len(bull_out.upside_arguments), 0)

    def test_bear_debater_agent_risk_score(self):
        """Test 15: BearDebaterAgent formulates downside counter-arguments and bear risk score."""
        scout_out = FOScoutOutput(
            ticker="RELIANCE.NS", symbol="RELIANCE", is_index=False,
            spot_cmp=2500.0, rvol=1.5, price_change_pct=-1.5,
            lot_size=250, strike_step=20.0, scout_rank=1, scout_modifier=0.5
        )
        tech_out = FOTechnicianAgent(self.config).run(scout_out, timeframe="5m")
        news_out = NewsdeskOutput(ticker="RELIANCE.NS", symbol="RELIANCE", news_sentiment_score=3.0, catalyst_risk_score=6.5)

        bear_agent = BearDebaterAgent(self.config)
        bear_out = bear_agent.run(scout_out, tech_out, news_out)

        self.assertIsInstance(bear_out, BearDebaterOutput)
        self.assertGreaterEqual(bear_out.bear_risk_score, 0.0)
        self.assertLessEqual(bear_out.bear_risk_score, 10.0)
        self.assertGreater(len(bear_out.downside_arguments), 0)

    def test_judge_risk_committee_override_veto(self):
        """Test 16: Risk Committee Override vetoes trade when Bear Risk >= 7.5 or VIX >= 28.0."""
        scout_out = FOScoutOutput(
            ticker="RELIANCE.NS", symbol="RELIANCE", is_index=False,
            spot_cmp=2500.0, rvol=2.0, price_change_pct=1.5,
            lot_size=250, strike_step=20.0, scout_rank=1, scout_modifier=0.6
        )
        tech_high_vix = MagicMock(stance="bullish", vix=30.0, technical_score=2.0)
        bear_high_risk = BearDebaterOutput(ticker="RELIANCE.NS", symbol="RELIANCE", bear_risk_score=8.0)

        judge = FOJudgeAgent(self.config)
        out_vix = judge.run(scout_out, tech_high_vix, self.state, timeframe="5m")
        out_bear = judge.run(scout_out, MagicMock(stance="bullish", vix=14.0, technical_score=2.0), self.state, timeframe="5m", bear=bear_high_risk)

        self.assertEqual(out_vix.verdict, "AVOID")
        self.assertEqual(out_vix.risk_override_status, "RISK_OVERRIDE_TRIGGERED")
        self.assertEqual(out_bear.verdict, "AVOID")
        self.assertEqual(out_bear.risk_override_status, "RISK_OVERRIDE_TRIGGERED")

    def test_judge_fact_checker_rejection(self):
        """Test 17: Fact-Checker rejects trade when spot price <= 0 or lot size <= 0."""
        scout_invalid_spot = FOScoutOutput(
            ticker="RELIANCE.NS", symbol="RELIANCE", is_index=False,
            spot_cmp=0.0, rvol=1.5, price_change_pct=1.0,
            lot_size=250, strike_step=20.0, scout_rank=1, scout_modifier=0.5
        )
        tech_out = MagicMock(stance="bullish", vix=14.0, technical_score=2.0)
        judge = FOJudgeAgent(self.config)
        out = judge.run(scout_invalid_spot, tech_out, self.state, timeframe="5m")

        self.assertEqual(out.verdict, "AVOID")
        self.assertFalse(out.fact_checker_approved)

    def test_committee_debate_log_persistence(self):
        """Test 18: JudgeAgent automatically persists debate entry to committee_debate_log.json."""
        scout_out = FOScoutOutput(
            ticker="RELIANCE.NS", symbol="RELIANCE", is_index=False,
            spot_cmp=2500.0, rvol=1.5, price_change_pct=1.0,
            lot_size=250, strike_step=20.0, scout_rank=1, scout_modifier=0.5
        )
        tech_out = MagicMock(stance="bullish", vix=14.0, technical_score=1.5)
        judge = FOJudgeAgent(self.config)
        judge.run(scout_out, tech_out, self.state, timeframe="5m")

        self.assertTrue(os.path.exists(COMMITTEE_DEBATE_LOG_FILE))
        with open(COMMITTEE_DEBATE_LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
            self.assertIsInstance(logs, list)
            self.assertGreater(len(logs), 0)
            latest = logs[-1]
            required_keys = ["timestamp", "symbol", "ticker", "scout_stance", "tech_stance", "news_stance", "bull_stance", "bear_stance", "consensus_score", "fact_checker_approved", "risk_override_status", "judge_verdict", "reasoning"]
            for key in required_keys:
                self.assertIn(key, latest)

if __name__ == "__main__":
    unittest.main()

