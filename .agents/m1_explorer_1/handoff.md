# HANDOFF REPORT: Bot 1 Equity Intraday Cash Strategy Execution Engine Specification

**Author**: M1 Explorer 1 (`teamwork_preview_explorer`)  
**Target Recipient**: Worker Agent / Implementer  
**Working Directory**: `c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\m1_explorer_1`  
**Date**: 2026-08-08  

---

## 1. Observation

Direct code observations from inspecting the codebase:

1. **`main.py` (lines 24–61)**: Currently defines `run_fo_pipeline()`, which executes only Bot 2 (`FOScoutAgent`, `FOTechnicianAgent`, `FOJudgeAgent`, `FOExecutorAgent`). Bot 1 (Equity Intraday Cash Engine) is absent from the execution workflow.
2. **`config/settings.yaml` (lines 22–85)**: `fo_universe` defines contract lot sizes for 2 indices and 10 stocks. There is no dedicated `bot1_equity` section configuring cash margin parameters, cash allocation limits, or cash stock universe.
3. **`agents/` directory**: Contains `scout.py`, `technician.py`, `judge.py`, and `executor.py`. File `agents/bot1_cash.py` does NOT exist.
4. **`core/data_sources.py` (lines 10–104)**: Provides complete technical analysis helper utilities (`yfinanceWrapper.fetch_ohlcv`, `fetch_vix`, `calculate_rsi`, `calculate_atr`, `calculate_adx`, `calculate_vwap`, `calculate_supertrend`).
5. **`core/schemas.py` (lines 5–105)**: Defines F&O schemas (`FOScoutOutput`, `FOTechnicianOutput`, `FOContractData`, `FOJudgeOutput`, `FOOpenPosition`, `FOPortfolioState`). No signal schema exists for Bot 1 cash trades.
6. **`agents/executor.py` (lines 18–130)**: `FOExecutorAgent` handles position capital deduction (`pool_available`, `pool_deployed`), state persistence (`save_fo_state`), trade logging (`append_to_fo_trade_log`), and 3:15 PM IST square-off (`squareoff_all`).

---

## 2. Logic Chain

1. **Requirement Mapping**: Project Specification `PROJECT.md` (Feature 1, line 16) and `ORIGINAL_REQUEST.md` (R1) require Bot 1 (Equity Intraday Cash Engine) with zero-latency bar-by-bar execution, live signal generation, cash margin sizing (1x cash margin), and seamless integration into `main.py`.
2. **Configuration Design**: `config/settings.yaml` must define `bot1_equity` with `cash_margin_multiplier: 1.0` (1x cash margin), `max_allocation_per_trade_pct: 15.0`, `execution_score_threshold: 7.0`, and a liquid NIFTY50 cash universe (`RELIANCE.NS`, `HDFCBANK.NS`, `ICICIBANK.NS`, `INFY.NS`, `TCS.NS`, `BHARTIARTL.NS`, `MARUTI.NS`, `LT.NS`, `AXISBANK.NS`, `SBIN.NS`).
3. **Schema Specification**: `core/schemas.py` must include `Bot1Signal` model encapsulating `ticker`, `symbol`, `side` ("BUY"/"SELL"/"AVOID"), `spot_cmp`, `signal_score`, `suggested_entry`, `suggested_sl`, `suggested_target`, `quantity`, `position_value_inr`, `estimated_brokerage_inr`, `reasoning`, and `timestamp`.
4. **Agent Implementation**: `agents/bot1_cash.py` will host `Bot1EquityAgent`. Its `run_symbol` method calculates EMA9/21, RSI, ADX, ATR, VWAP, and Supertrend over intraday OHLCV bars to compute a multi-factor score (0.0 to 10.0). Scores $\ge 7.0$ trigger `BUY` signals, while scores $\le 3.0$ trigger `SELL` signals.
5. **Cash Margin Position Sizing**:
   $$\text{Max Trade Allocation (INR)} = \min(\text{pool\_available}, \text{pool\_total} \times \text{max\_allocation\_per\_trade\_pct})$$
   $$\text{Quantity} = \lfloor \frac{\text{Max Trade Allocation} \times \text{cash\_margin\_multiplier}}{\text{CMP}} \rfloor$$
   $$\text{Position Value (INR)} = \text{Quantity} \times \text{CMP}$$
   $$\text{Stop Loss} = \text{CMP} \mp (\text{ATR} \times \text{atr\_sl\_multiplier}), \quad \text{Target} = \text{CMP} \pm (\text{ATR} \times \text{atr\_target\_multiplier})$$
6. **Executor Enhancement**: `FOExecutorAgent` in `agents/executor.py` must be enhanced with `execute_cash(signal, state)` to record `contract_type: "EQUITY_CASH"` in `state["open_positions"]`, deduct `position_value_inr + brokerage`, and append rows to `trade_log.csv`.
7. **Pipeline Orchestration**: `main.py` must expose `run_quant_pipeline()` which sequentially runs position monitoring, Bot 1 Cash scan loop, and Bot 2 F&O Swarm scan loop, preserving `run_fo_pipeline()` as an alias.

---

## 3. Caveats

- **yfinance Intraday Latency/Limits**: Yahoo Finance 1m/5m interval data may occasionally be delayed or empty outside market hours; fallback logic in `yfinanceWrapper.fetch_ohlcv` handles 15m/5d data fallback gracefully.
- **Intraday Cash Shorting**: Cash short positions (`SELL`) must be squared off before 3:15 PM IST per Indian stock exchange regulations. The 3:15 PM IST auto square-off logic in `FOExecutorAgent.monitor_positions()` guarantees compliance.
- **Shared Portfolio Capital**: Bot 1 and Bot 2 draw from the unified `pool_available` balance in `state/portfolio_state.json`.

---

## 4. Conclusion

Bot 1 (Equity Intraday Cash Strategy Execution Engine) can be fully implemented without breaking existing F&O functionality. The Worker should implement the 5 specific file modifications outlined in Section 6 below.

---

## 5. Verification Method

1. **Configuration Inspection**:
   Validate `config/settings.yaml` contains `bot1_equity` block with 10 cash tickers and `cash_margin_multiplier: 1.0`.
2. **Unit Execution Test**:
   Run command in shell:
   ```powershell
   python -c "from agents.bot1_cash import Bot1EquityAgent; from main import load_config; from core.state import load_fo_state; cfg=load_config(); st=load_fo_state(); agent=Bot1EquityAgent(cfg); sigs=agent.run(st); print(f'Generated {len(sigs)} cash signals')"
   ```
3. **End-to-End Execution Test**:
   Run command in shell:
   ```powershell
   python main.py
   ```
4. **State & Log Invalidation Checks**:
   - Inspect `state/portfolio_state.json` to verify `pool_available` + `pool_deployed` equals total capital pool.
   - Inspect `state/trade_log.csv` to confirm cash trade rows are appended with `contract_type = EQUITY_CASH`.

---

## 6. Exact File Changes & Code Design for Worker

### File 1: `config/settings.yaml` (Append Section)

Add the following configuration block under `project_name`:

```yaml
# ─────────────────────────────────────────────
# BOT 1: EQUITY INTRADAY CASH STRATEGY CONFIGURATION
# ─────────────────────────────────────────────
bot1_equity:
  enabled: true
  cash_margin_multiplier: 1.0         # 1x Cash Margin (No leverage)
  max_allocation_per_trade_pct: 15.0  # Max 15% of total pool per stock cash trade
  max_open_positions: 5               # Max 5 concurrent cash positions
  min_stop_loss_pct: 1.0              # Minimum 1.0% SL floor
  atr_sl_multiplier: 2.0              # 2.0x ATR SL for cash positions
  atr_target_multiplier: 3.0          # 3.0x ATR Target for cash positions
  min_risk_reward_ratio: 1.2
  execution_score_threshold: 7.0      # Score >= 7.0 triggers BUY/SELL signal
  universe:
    - symbol: "RELIANCE"
      ticker: "RELIANCE.NS"
      sector: "ENERGY"
    - symbol: "HDFCBANK"
      ticker: "HDFCBANK.NS"
      sector: "BANK"
    - symbol: "ICICIBANK"
      ticker: "ICICIBANK.NS"
      sector: "BANK"
    - symbol: "INFY"
      ticker: "INFY.NS"
      sector: "IT"
    - symbol: "TCS"
      ticker: "TCS.NS"
      sector: "IT"
    - symbol: "BHARTIARTL"
      ticker: "BHARTIARTL.NS"
      sector: "TELECOM"
    - symbol: "MARUTI"
      ticker: "MARUTI.NS"
      sector: "AUTO"
    - symbol: "LT"
      ticker: "LT.NS"
      sector: "INFRA"
    - symbol: "AXISBANK"
      ticker: "AXISBANK.NS"
      sector: "BANK"
    - symbol: "SBIN"
      ticker: "SBIN.NS"
      sector: "BANK"
```

---

### File 2: `core/schemas.py` (Add Pydantic Model)

Append `Bot1Signal` schema:

```python
class Bot1Signal(BaseModel):
    ticker: str
    symbol: str
    side: str  # "BUY" / "SELL" / "AVOID"
    spot_cmp: float
    signal_score: float
    timeframe: str
    suggested_entry: float
    suggested_sl: float
    suggested_target: float
    quantity: int
    position_value_inr: float
    estimated_brokerage_inr: float = 20.0
    reasoning: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

---

### File 3: `agents/bot1_cash.py` (NEW FILE)

Create `agents/bot1_cash.py`:

```python
import math
import logging
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd

from core.data_sources import (
    yfinanceWrapper, calculate_rsi, calculate_atr, calculate_adx,
    calculate_vwap, calculate_supertrend
)
from core.schemas import Bot1Signal

logger = logging.getLogger(__name__)

class Bot1EquityAgent:
    """
    Bot 1: Equity Intraday Cash Strategy Execution Engine.
    Generates intraday signals for liquid NIFTY50 cash stocks using multi-indicator scoring
    and 1x cash margin sizing based on available capital pool.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.equity_cfg = config.get("bot1_equity", {})
        self.universe = self.equity_cfg.get("universe", [])
        self.margin_mult = float(self.equity_cfg.get("cash_margin_multiplier", 1.0))
        self.max_alloc_pct = float(self.equity_cfg.get("max_allocation_per_trade_pct", 15.0)) / 100.0
        self.threshold = float(self.equity_cfg.get("execution_score_threshold", 7.0))

    def run_symbol(self, stock_info: Dict[str, str], timeframe: str, state: Dict[str, Any]) -> Bot1Signal:
        ticker = stock_info["ticker"]
        symbol = stock_info["symbol"]

        df = yfinanceWrapper.fetch_ohlcv(ticker, timeframe=timeframe, period="1d")
        if df.empty or len(df) < 5:
            df = yfinanceWrapper.fetch_ohlcv(ticker, timeframe="15m", period="5d")

        if df.empty or len(df) < 5:
            return Bot1Signal(
                ticker=ticker, symbol=symbol, side="AVOID", spot_cmp=0.0,
                signal_score=0.0, timeframe=timeframe, suggested_entry=0.0,
                suggested_sl=0.0, suggested_target=0.0, quantity=0,
                position_value_inr=0.0, reasoning="Insufficient price data fetched."
            )

        cmp = float(df['Close'].iloc[-1])
        close_prices = df['Close']
        
        # Technical indicators calculation
        ema9 = float(close_prices.ewm(span=9, adjust=False).mean().iloc[-1])
        ema21 = float(close_prices.ewm(span=21, adjust=False).mean().iloc[-1])
        rsi = float(calculate_rsi(close_prices, period=min(14, len(df)-1)).iloc[-1])
        adx = float(calculate_adx(df, period=min(14, len(df)-1)).iloc[-1])
        atr = float(calculate_atr(df, period=min(14, len(df)-1)).iloc[-1])
        vwap = float(calculate_vwap(df).iloc[-1])
        st_series, st_dir = calculate_supertrend(df, period=7, multiplier=3.0)
        supertrend_dir = int(st_dir.iloc[-1])

        # Multi-factor technical score calculation (0.0 to 10.0)
        score = 5.0

        # 1. Supertrend & EMA Trend alignment (+/- 1.5)
        if supertrend_dir == 1:
            score += 1.0
        else:
            score -= 1.0

        if ema9 > ema21:
            score += 0.5
        else:
            score -= 0.5

        # 2. VWAP positioning (+/- 0.8)
        if cmp > vwap:
            score += 0.8
        else:
            score -= 0.8

        # 3. Momentum (RSI + ADX) (+/- 1.5)
        if 50.0 <= rsi <= 68.0:
            score += 0.7
        elif rsi > 70.0:
            score -= 0.3
        elif 32.0 <= rsi < 50.0:
            score -= 0.7
        elif rsi < 30.0:
            score += 0.3

        if adx > 20.0:
            score += 0.5 if score >= 5.0 else -0.5

        score = max(0.0, min(10.0, score))

        # Determine trade side based on score threshold
        if score >= self.threshold:
            side = "BUY"
        elif score <= (10.0 - self.threshold):
            side = "SELL"
        else:
            side = "AVOID"

        if side == "AVOID":
            return Bot1Signal(
                ticker=ticker, symbol=symbol, side="AVOID", spot_cmp=round(cmp, 2),
                signal_score=round(score, 2), timeframe=timeframe, suggested_entry=round(cmp, 2),
                suggested_sl=0.0, suggested_target=0.0, quantity=0,
                position_value_inr=0.0, reasoning=f"Signal score {score:.2f} did not reach execution threshold {self.threshold}."
            )

        # 1x Cash Margin Sizing Logic
        pool_avail = float(state.get("pool_available", 0.0))
        pool_total = float(state.get("pool_total", 500000.0))

        max_trade_cap = min(pool_avail, pool_total * self.max_alloc_pct)
        effective_capital = max_trade_cap * self.margin_mult  # 1x cash margin

        quantity = math.floor(effective_capital / cmp) if cmp > 0 else 0
        if quantity < 1:
            return Bot1Signal(
                ticker=ticker, symbol=symbol, side="AVOID", spot_cmp=round(cmp, 2),
                signal_score=round(score, 2), timeframe=timeframe, suggested_entry=round(cmp, 2),
                suggested_sl=0.0, suggested_target=0.0, quantity=0,
                position_value_inr=0.0, reasoning=f"Insufficient pool (₹{pool_avail:.2f}) to buy 1 share @ ₹{cmp:.2f}."
            )

        position_val = round(quantity * cmp, 2)
        atr_sl_mult = float(self.equity_cfg.get("atr_sl_multiplier", 2.0))
        atr_tgt_mult = float(self.equity_cfg.get("atr_target_multiplier", 3.0))
        stop_dist = max(atr * atr_sl_mult, cmp * 0.01)

        if side == "BUY":
            sl = round(cmp - stop_dist, 2)
            target = round(cmp + (stop_dist * (atr_tgt_mult / atr_sl_mult)), 2)
        else:
            sl = round(cmp + stop_dist, 2)
            target = round(cmp - (stop_dist * (atr_tgt_mult / atr_sl_mult)), 2)

        return Bot1Signal(
            ticker=ticker,
            symbol=symbol,
            side=side,
            spot_cmp=round(cmp, 2),
            signal_score=round(score, 2),
            timeframe=timeframe,
            suggested_entry=round(cmp, 2),
            suggested_sl=sl,
            suggested_target=target,
            quantity=quantity,
            position_value_inr=position_val,
            estimated_brokerage_inr=20.0,
            reasoning=f"Approved {side} signal for {symbol} cash stock. Score: {score:.2f}/10. Qty: {quantity} @ ₹{cmp:.2f} (1x Cash Margin Val: ₹{position_val:.2f})."
        )

    def run(self, state: Dict[str, Any], timeframe: str = "5m") -> List[Bot1Signal]:
        logger.info(f"--- Running Bot 1 (Equity Intraday Cash Engine) Scan ({timeframe}) ---")
        signals = []
        for stock_info in self.universe:
            sig = self.run_symbol(stock_info, timeframe=timeframe, state=state)
            if sig.side != "AVOID":
                signals.append(sig)
        logger.info(f"[Bot 1 Equity Agent] Found {len(signals)} actionable cash signals on {timeframe} timeframe.")
        return signals
```

---

### File 4: `agents/executor.py` (Add `execute_cash` Method)

Add `execute_cash` to `FOExecutorAgent`:

```python
    def execute_cash(self, signal: Any, state: Dict[str, Any]) -> bool:
        if signal.side == "AVOID" or signal.quantity <= 0:
            return False

        ticker = signal.ticker
        symbol = signal.symbol
        side = signal.side
        qty = signal.quantity
        cmp = signal.spot_cmp
        pos_val = signal.position_value_inr
        brokerage = signal.estimated_brokerage_inr
        total_cash_required = pos_val + brokerage

        if state["pool_available"] < total_cash_required:
            logger.warning(f"[Bot 1 Cash Executor] Insufficient available cash for {symbol}: Required ₹{total_cash_required:.2f}, Avail ₹{state['pool_available']:.2f}")
            return False

        max_cash_pos = self.config.get("bot1_equity", {}).get("max_open_positions", 5)
        cash_open_count = sum(1 for p in state.get("open_positions", []) if p.get("contract_type") == "EQUITY_CASH")
        if cash_open_count >= max_cash_pos:
            logger.warning(f"[Bot 1 Cash Executor] Max cash open positions limit ({max_cash_pos}) reached. Skipping {symbol}.")
            return False

        logger.info(f"[BOT 1 EXECUTOR] Executing Cash {side} for {symbol}: {qty} shares @ ₹{cmp:.2f}. Total Value: ₹{pos_val:.2f}, Brokerage: ₹{brokerage}")

        state["pool_available"] -= total_cash_required
        state["pool_deployed"] += pos_val
        state["total_brokerage_paid_inr"] += brokerage
        state["trades_today"] += 1

        run_id = f"{symbol}_CASH_{side}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        new_position = {
            "ticker": ticker,
            "contract_type": "EQUITY_CASH",
            "symbol": symbol,
            "strike_price": 0.0,
            "lots": 1,
            "total_shares": qty,
            "entry_premium": cmp,
            "entry_spot": cmp,
            "sl_spot": signal.suggested_sl,
            "target_spot": signal.suggested_target,
            "entered_at": datetime.utcnow().isoformat() + "Z",
            "megabull_order_id": run_id,
            "brokerage_paid_inr": brokerage
        }
        state["open_positions"].append(new_position)
        save_fo_state(state)

        log_row = {
            "run_id": run_id,
            "ticker": ticker,
            "symbol": symbol,
            "verdict": f"CASH_{side}",
            "contract_type": "EQUITY_CASH",
            "strike_price": 0.0,
            "lots": 1,
            "total_shares": qty,
            "spot_entry": cmp,
            "option_premium": cmp,
            "spot_sl": signal.suggested_sl,
            "spot_target": signal.suggested_target,
            "waterfall_score": signal.signal_score,
            "position_value_inr": pos_val,
            "brokerage_fee_inr": brokerage,
            "total_cost_inr": pos_val + brokerage,
            "executed_at": datetime.utcnow().isoformat() + "Z"
        }
        append_to_fo_trade_log(log_row)
        return True
```

---

### File 5: `main.py` (Update Execution Pipeline)

Update `main.py` to run both Bot 1 and Bot 2:

```python
import os
import yaml
import logging
from datetime import datetime, timezone, timedelta
from core.state import load_fo_state, save_fo_state
from core.data_sources import yfinanceWrapper
from agents.bot1_cash import Bot1EquityAgent
from agents.scout import FOScoutAgent
from agents.technician import FOTechnicianAgent
from agents.judge import FOJudgeAgent
from agents.executor import FOExecutorAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("QuantOrchestrator")

def load_config():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(root_dir, "config", "settings.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_quant_pipeline():
    logger.info("=== STARTING SHADOW TRADERS QUANT PIPELINE (BOT 1 CASH & BOT 2 F&O SWARM) ===")
    config = load_config()
    state = load_fo_state()

    ist_tz = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(ist_tz)
    
    executor = FOExecutorAgent(config)
    executor.monitor_positions(state)

    if now_ist.hour > 13 or (now_ist.hour == 13 and now_ist.minute >= 30):
        logger.warning("Scan triggered after 1:30 PM IST entry cutoff. No new entries allowed.")
        save_fo_state(state)
        return

    timeframes = ["5m", "1m", "15m"]

    # --- BOT 1: EQUITY INTRADAY CASH STRATEGY EXECUTION ENGINE ---
    if config.get("bot1_equity", {}).get("enabled", True):
        logger.info("--- [BOT 1] Executing Equity Intraday Cash Strategy Engine ---")
        bot1_agent = Bot1EquityAgent(config)
        for tf in timeframes:
            cash_signals = bot1_agent.run(state, timeframe=tf)
            for sig in cash_signals:
                if sig.side != "AVOID":
                    logger.info(f"[Bot 1 Cash Triggered] {sig.symbol} ({tf}): {sig.side} (Score: {sig.signal_score}/10, Qty: {sig.quantity})")
                    executor.execute_cash(sig, state)

    # --- BOT 2: F&O OPTIONS SWARM STRATEGY EXECUTION ENGINE ---
    logger.info("--- [BOT 2] Executing F&O Options Swarm Engine ---")
    scout = FOScoutAgent(config)
    technician = FOTechnicianAgent(config)
    judge = FOJudgeAgent(config)

    vix_val = yfinanceWrapper.fetch_vix()
    logger.info(f"India VIX: {vix_val:.2f}")

    for tf in timeframes:
        logger.info(f"--- Running F&O Scan Cycle on {tf} timeframe ---")
        candidates = scout.run(timeframe=tf)
        for cand in candidates:
            tech_out = technician.run(cand, timeframe=tf, vix_val=vix_val)
            judge_out = judge.run(cand, tech_out, state, timeframe=tf)

            if judge_out.verdict != "AVOID":
                logger.info(f"[Bot 2 F&O Triggered] {cand.symbol} ({tf}): Verdict = {judge_out.verdict} (Score: {judge_out.waterfall_score}/10)")
                executor.execute(judge_out, state)

    save_fo_state(state)
    logger.info("=== QUANT PIPELINE COMPLETED SUCCESSFULLY ===")

def run_fo_pipeline():
    """Backward compatibility wrapper for F&O pipeline runner."""
    run_quant_pipeline()

if __name__ == "__main__":
    run_quant_pipeline()
```
