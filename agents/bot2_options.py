import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from core.schemas import FOJudgeOutput, FOPortfolioState
from core.data_sources import BarEvent

from core.options_engine import OptionsEngine
from agents.scout import FOScoutAgent
from agents.technician import FOTechnicianAgent
from agents.judge import FOJudgeAgent

logger = logging.getLogger("Bot2OptionSwarmAgent")

class Bot2OptionSwarmAgent:
    """
    Bot 2 Strategy Engine: F&O Options Swarm Agent.
    Generates options & futures signals (BUY_CE, BUY_PE, BUY_FUT, SELL_FUT, SCALP_CE, SCALP_PE)
    using Black-Scholes pricing, strike selection, lot sizing, and cost-gate checks.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.scout = FOScoutAgent(self.config)
        self.technician = FOTechnicianAgent(self.config)
        self.judge = FOJudgeAgent(self.config)
        self.options_engine = OptionsEngine()

    def run(
        self,
        ticker: str,
        timeframe: str = "5m",
        state: Optional[Dict[str, Any]] = None,
        vix_val: float = 14.5,
        bar_event: Optional[BarEvent] = None
    ) -> Optional[FOJudgeOutput]:
        """
        Evaluates a single F&O ticker at a given timestamp/bar.
        Returns FOJudgeOutput if actionable signal generated, else None.
        """
        try:
            # 1. Obtain candidate structure from scout
            candidates = self.scout.run(timeframe=timeframe)
            cand = next((c for c in candidates if c.ticker == ticker), None)
            if not cand:
                return None

            # If bar_event is supplied, update spot_cmp from live bar event
            if bar_event and hasattr(bar_event, "close"):
                cand.spot_cmp = bar_event.close

            # 2. Compute technical indicators & score
            effective_state = state or {}
            tech_out = self.technician.run(cand, timeframe=timeframe, vix_val=vix_val)

            # 3. Judge verdict with Black-Scholes pricing & cost gate
            judge_out = self.judge.run(cand, tech_out, effective_state, timeframe=timeframe)

            if judge_out and judge_out.verdict not in ["AVOID", "REJECT", "WATCHLIST"]:
                logger.info(f"[Bot 2 F&O Swarm Signal] {ticker} ({timeframe}): Verdict={judge_out.verdict}, Score={judge_out.waterfall_score}")
                return judge_out

            return None
        except Exception as e:
            logger.error(f"[Bot 2 Engine Error] {ticker} ({timeframe}): {e}")
            return None

    def scan_universe(
        self,
        timeframe: str = "5m",
        state: Optional[Dict[str, Any]] = None,
        vix_val: float = 14.5
    ) -> List[FOJudgeOutput]:
        """
        Scans all F&O universe symbols and returns actionable signals.
        """
        signals = []
        effective_state = state or {}
        candidates = self.scout.run(timeframe=timeframe)
        for cand in candidates:
            tech_out = self.technician.run(cand, timeframe=timeframe, vix_val=vix_val)
            judge_out = self.judge.run(cand, tech_out, effective_state, timeframe=timeframe)
            if judge_out and judge_out.verdict not in ["AVOID", "REJECT", "WATCHLIST"]:
                signals.append(judge_out)
        return signals
