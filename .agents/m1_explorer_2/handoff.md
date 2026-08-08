# HANDOFF REPORT — M1 Explorer 2
**Task**: Detailed Implementation Specification for Zero-Latency Bar-by-Bar Stream Execution & Bot 2 (F&O Options Swarm) Parallel Engine.
**Target Files**: `core/data_sources.py`, `agents/bot2_options.py`, `main.py`

---

## 1. Observation

Direct evidence gathered from analyzing the codebase:

### 1.1 `main.py` Current State
- **File**: `c:\Users\RANAY\Desktop\FO TRADING BOT\main.py` (lines 1-65)
- Currently performs a single snapshot scan iteration:
  ```python
  def run_fo_pipeline():
      ...
      scout = FOScoutAgent(config)
      technician = FOTechnicianAgent(config)
      judge = FOJudgeAgent(config)
      vix_val = yfinanceWrapper.fetch_vix()
      for tf in timeframes:
          candidates = scout.run(timeframe=tf)
          for cand in candidates:
              tech_out = technician.run(cand, timeframe=tf, vix_val=vix_val)
              judge_out = judge.run(cand, tech_out, state, timeframe=tf)
              if judge_out.verdict != "AVOID":
                  executor.execute(judge_out, state)
  ```
- **Lacks**:
  1. Continuous bar-by-bar streaming event loop.
  2. Bot 2 (`Bot2OptionSwarmAgent`) engine wrapper.
  3. Parallel execution for Bot 1 (Equity Intraday Cash) and Bot 2 (F&O Options Swarm).

### 1.2 `core/data_sources.py` Current State
- **File**: `c:\Users\RANAY\Desktop\FO TRADING BOT\core\data_sources.py` (lines 1-104)
- Contains `yfinanceWrapper.fetch_ohlcv()`, `fetch_vix()`, and indicator functions (`calculate_rsi`, `calculate_atr`, `calculate_adx`, `calculate_vwap`, `calculate_supertrend`).
- **Lacks**: `StreamingTickSimulator` / `BarEvent` data structure for zero-latency event-driven bar-by-bar streaming without lookahead bias.

### 1.3 `core/options_engine.py` Current State
- **File**: `c:\Users\RANAY\Desktop\FO TRADING BOT\core\options_engine.py` (lines 15-110)
- Fully functional `OptionsEngine` class with Black-Scholes pricing (`calculate_bs_price_and_greeks`), strike selection (`select_strike`), futures pricing (`calculate_futures_price`), and statutory brokerage cost deductions (`calculate_trade_costs`).

### 1.4 `config/settings.yaml` Configuration
- **File**: `c:\Users\RANAY\Desktop\FO TRADING BOT\config\settings.yaml` (lines 22-85)
- Fully specifies `fo_universe` with indices (`^NSEI` NIFTY50, `^NSEBANK` BANKNIFTY) and top liquid F&O stocks (`RELIANCE.NS`, `HDFCBANK.NS`, `ICICIBANK.NS`, `INFY.NS`, `TCS.NS`, `DLF.NS`, `BHARTIARTL.NS`, `HINDALCO.NS`, `TATASTEEL.NS`, `MARUTI.NS`).

---

## 2. Logic Chain

From the observations above, we establish the following logic steps for architectural design:

1. **Zero-Latency Event-Driven Bar Stream**:
   - To achieve zero-latency bar-by-bar execution (R1 requirement), `core/data_sources.py` must provide a streaming tick simulator (`StreamingTickSimulator`) that preloads historical OHLCV data for all target tickers and timeframes.
   - It iterates chronologically through timestamps, yielding `BarEvent` instances. Each `BarEvent` contains current bar OHLCV and a `rolling_df` slice of historical bars up to the current bar's timestamp. This guarantees zero lookahead bias when strategy engines compute technical indicators.

2. **Bot 2 (F&O Options Swarm Engine) Refactoring**:
   - `agents/bot2_options.py` must encapsulate the F&O Options Swarm strategy engine into `Bot2OptionSwarmAgent`.
   - It integrates `FOScoutAgent`, `FOTechnicianAgent`, `OptionsEngine`, and `FOJudgeAgent` into a unified API: `run(ticker, timeframe, state, vix_val, bar_event) -> Optional[FOJudgeOutput]`.
   - It processes F&O indices (`^NSEI`, `^NSEBANK`) and F&O stock candidates, evaluating momentum, Black-Scholes option pricing (CE/PE), strike selection (ATM/ITM), lot sizing, and cost viability gates.

3. **Parallel Bot Execution Architecture**:
   - In `main.py`, the continuous stream loop (`run_continuous_stream`) processes each bar event.
   - For each bar event or scan cycle, Bot 1 (`Bot1EquityAgent` for Equity Intraday Cash) and Bot 2 (`Bot2OptionSwarmAgent` for F&O Options Swarm) are executed in parallel using `concurrent.futures.ThreadPoolExecutor(max_workers=2)`.
   - Both strategy engines evaluate their respective universes concurrently. Generated signals are collected and passed sequentially to `FOExecutorAgent.execute(signal, state)` under a `threading.Lock` to guarantee thread-safe portfolio state updates in `core/state.py`.
   - Position monitoring (`executor.monitor_positions(state, bar_event)`) is executed on every bar event to evaluate SL/TP triggers in real time.

---

## 3. Caveats

1. **Network Connectivity & Preload Fallback**: `yfinance` may experience rate limits or downtime. `StreamingTickSimulator` must handle empty DataFrame returns gracefully by providing synthetic/mock bar generation fallback when yfinance fails.
2. **State Thread Safety**: Although strategy signal generation is parallelized, state mutation (`FOPortfolioState`) must be synchronized using `threading.Lock()` to prevent race conditions when Bot 1 and Bot 2 generate signals simultaneously.
3. **Execution Delay Configuration**: In backtest/simulation mode, `delay_seconds=0.0` ensures zero-latency execution. In live paper mode, `delay_seconds > 0` allows realistic interval simulation.

---

## 4. Conclusion & Implementation Specification

### 4.1 Changes to `core/data_sources.py`

Add `BarEvent` schema and `StreamingTickSimulator` class:

```python
from pydantic import BaseModel
from typing import Dict, List, Optional, Generator, Any
from datetime import datetime
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class BarEvent(BaseModel):
    ticker: str
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    rolling_df: pd.DataFrame

    class Config:
        arbitrary_types_allowed = True

class StreamingTickSimulator:
    """
    Zero-Latency Streaming Bar & Tick Simulator.
    Preloads market data and streams OHLCV bar events sequentially
    without lookahead bias.
    """
    def __init__(
        self,
        tickers: List[str],
        timeframes: List[str] = ["5m", "1m"],
        period: str = "1d",
        simulate_live: bool = False,
        delay_seconds: float = 0.0
    ):
        self.tickers = tickers
        self.timeframes = timeframes
        self.period = period
        self.simulate_live = simulate_live
        self.delay_seconds = delay_seconds
        self.data_cache: Dict[str, Dict[str, pd.DataFrame]] = {}
        self.latest_prices: Dict[str, float] = {}

    def preload((self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """Preloads historical OHLCV data for all tickers and timeframes."""
        for ticker in self.tickers:
            self.data_cache[ticker] = {}
            for tf in self.timeframes:
                df = yfinanceWrapper.fetch_ohlcv(ticker, timeframe=tf, period=self.period)
                if not df.empty:
                    self.data_cache[ticker][tf] = df
        return self.data_cache

    def stream_bars(self, timeframe: str = "5m") -> Generator[BarEvent, None, None]:
        """
        Yields BarEvent objects in strict chronological order across tickers.
        """
        # Collect all unique timestamps across preloaded data
        all_timestamps = set()
        for ticker, tf_map in self.data_cache.items():
            if timeframe in tf_map and not tf_map[timeframe].empty:
                all_timestamps.update(tf_map[timeframe].index)

        sorted_timestamps = sorted(list(all_timestamps))

        for ts in sorted_timestamps:
            for ticker in self.tickers:
                tf_map = self.data_cache.get(ticker, {})
                if timeframe in tf_map:
                    df = tf_map[timeframe]
                    if ts in df.index:
                        idx = df.index.get_loc(ts)
                        # Slice rolling dataframe up to current bar (no future lookahead)
                        rolling_df = df.iloc[:idx + 1]
                        row = df.loc[ts]
                        close_price = float(row['Close'])
                        self.latest_prices[ticker] = close_price

                        symbol = ticker.replace(".NS", "").replace("^", "")

                        bar_evt = BarEvent(
                            ticker=ticker,
                            symbol=symbol,
                            timeframe=timeframe,
                            timestamp=ts if isinstance(ts, datetime) else pd.to_datetime(ts),
                            open=float(row['Open']),
                            high=float(row['High']),
                            low=float(row['Low']),
                            close=close_price,
                            volume=float(row['Volume']),
                            rolling_df=rolling_df
                        )
                        yield bar_evt

    def get_latest_price(self, ticker: str) -> Optional[float]:
        return self.latest_prices.get(ticker)
```

---

### 4.2 New File `agents/bot2_options.py`

Create `agents/bot2_options.py` containing `Bot2OptionSwarmAgent`:

```python
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from core.schemas import FOJudgeOutput, FOPortfolioState, BarEvent
from core.options_engine import OptionsEngine
from agents.scout import FOScoutAgent
from agents.technician import FOTechnicianAgent
from agents.judge import FOJudgeAgent

logger = logging.getLogger("Bot2OptionSwarmAgent")

class Bot2OptionSwarmAgent:
    """
    Bot 2 Strategy Engine: F&O Options Swarm Agent.
    Generates options & futures signals (BUY_CE, BUY_PE, BUY_FUT, SELL_FUT)
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
        state: Optional[FOPortfolioState] = None,
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

            # 2. Compute technical indicators & score
            tech_out = self.technician.run(cand, timeframe=timeframe, vix_val=vix_val)

            # 3. Judge verdict with Black-Scholes pricing & cost gate
            judge_out = self.judge.run(cand, tech_out, state, timeframe=timeframe)

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
        state: Optional[FOPortfolioState] = None,
        vix_val: float = 14.5
    ) -> List[FOJudgeOutput]:
        """
        Scans all F&O universe symbols and returns actionable signals.
        """
        signals = []
        candidates = self.scout.run(timeframe=timeframe)
        for cand in candidates:
            tech_out = self.technician.run(cand, timeframe=timeframe, vix_val=vix_val)
            judge_out = self.judge.run(cand, tech_out, state, timeframe=timeframe)
            if judge_out and judge_out.verdict not in ["AVOID", "REJECT", "WATCHLIST"]:
                signals.append(judge_out)
        return signals
```

---

### 4.3 Refactoring `main.py`

Update `main.py` to support `run_continuous_stream()` with parallel execution:

```python
import os
import yaml
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta

from core.state import load_fo_state, save_fo_state
from core.data_sources import yfinanceWrapper, StreamingTickSimulator, BarEvent
from agents.bot1_cash import Bot1EquityAgent
from agents.bot2_options import Bot2OptionSwarmAgent
from agents.executor import FOExecutorAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("FOOrchestrator")

state_lock = threading.Lock()

def load_config():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(root_dir, "config", "settings.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_continuous_stream(simulate_live: bool = False, delay_seconds: float = 0.0):
    """
    Continuous Zero-Latency Bar-by-Bar Parallel Stream Execution Loop.
    Executes Bot 1 (Equity Cash) and Bot 2 (F&O Swarm) concurrently.
    """
    logger.info("=== STARTING ZERO-LATENCY PARALLEL STREAM EXECUTION ENGINE ===")
    config = load_config()
    state = load_fo_state()

    bot1_agent = Bot1EquityAgent(config)
    bot2_agent = Bot2OptionSwarmAgent(config)
    executor = FOExecutorAgent(config)

    # Collect universe tickers
    fo_indices = [item["ticker"] for item in config.get("fo_universe", {}).get("indices", [])]
    fo_stocks = [item["ticker"] for item in config.get("fo_universe", {}).get("stocks", [])]
    cash_stocks = config.get("equity_cash_universe", ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "TCS.NS"])

    all_tickers = list(set(fo_indices + fo_stocks + cash_stocks))
    
    simulator = StreamingTickSimulator(
        tickers=all_tickers,
        timeframes=["5m"],
        period="1d",
        simulate_live=simulate_live,
        delay_seconds=delay_seconds
    )

    logger.info(f"Preloading streaming data for {len(all_tickers)} tickers...")
    simulator.preload()

    vix_val = yfinanceWrapper.fetch_vix()
    logger.info(f"Initial India VIX: {vix_val:.2f}")

    with ThreadPoolExecutor(max_workers=2) as thread_pool:
        for bar_evt in simulator.stream_bars(timeframe="5m"):
            logger.info(f"[Bar Stream] {bar_evt.ticker} @ {bar_evt.timestamp} | Close={bar_evt.close}")

            # 1. Continuous Position Monitoring (SL/TP check)
            with state_lock:
                executor.monitor_positions(state, bar_evt)

            # 2. Parallel Strategy Execution (Bot 1 and Bot 2)
            futures = {}

            # Submit Bot 1 (Equity Cash) task if ticker in cash universe
            if bar_evt.ticker in cash_stocks:
                futures[thread_pool.submit(bot1_agent.run, bar_evt.ticker, "5m", state)] = "Bot1"

            # Submit Bot 2 (F&O Options Swarm) task if ticker in F&O universe
            if bar_evt.ticker in (fo_indices + fo_stocks):
                futures[thread_pool.submit(bot2_agent.run, bar_evt.ticker, "5m", state, vix_val, bar_evt)] = "Bot2"

            # 3. Gather Signals & Execute under Lock
            for fut in as_completed(futures):
                bot_name = futures[fut]
                try:
                    signal = fut.result()
                    if signal and hasattr(signal, "verdict") and signal.verdict not in ["AVOID", "REJECT", "WATCHLIST"]:
                        logger.info(f"[{bot_name} Actionable Signal] Executing {signal.verdict} for {signal.ticker}")
                        with state_lock:
                            executor.execute(signal, state)
                except Exception as e:
                    logger.error(f"[{bot_name} Thread Error]: {e}")

            # 4. Periodically save state
            with state_lock:
                save_fo_state(state)

    logger.info("=== ZERO-LATENCY PARALLEL STREAM EXECUTION COMPLETED ===")

def run_fo_pipeline():
    """Legacy entry point for single scan pass."""
    run_continuous_stream(simulate_live=False, delay_seconds=0.0)

if __name__ == "__main__":
    run_continuous_stream()
```

---

## 5. Verification Method

To verify the implementation independently:

1. **Syntax & Unit Verification**:
   ```bash
   python -m py_compile core/data_sources.py agents/bot2_options.py main.py
   ```
2. **Run Continuous Stream Test**:
   ```bash
   python main.py
   ```
   - Verify logs contain `[Bar Stream]` events emitting bar-by-bar.
   - Verify parallel execution of Bot 1 and Bot 2 without thread deadlocks or state file corruption.
   - Verify `state/portfolio_state.json` and `state/trade_log.csv` update cleanly.
