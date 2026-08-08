# 5-Component Handoff Report: Paper Execution & Real-Time Position Monitoring

## 1. Observation

Direct code inspection of `agents/executor.py`, `core/state.py`, `core/schemas.py`, `agents/judge.py`, `state/portfolio_state.json`, and `state/trade_log.csv` revealed three critical implementation defects:

### Observation 1.1: Flawed Entry Spot & SL/Target Spot Assignment in `agents/executor.py`
In `agents/executor.py` (lines 56–59):
```python
56: "entry_premium": premium,
57: "entry_spot": verdict.position_sizing_inr,
58: "sl_spot": verdict.position_sizing_inr * 0.985,
59: "target_spot": verdict.position_sizing_inr * 1.03,
```
`entry_spot` is assigned `verdict.position_sizing_inr` (total capital allocated in INR, e.g. ₹75,000.00) instead of the actual underlying stock/index spot CMP (e.g. 24,210.50 for NIFTY). Consequently, `sl_spot` and `target_spot` are calculated on total position cash value rather than underlying price levels.

### Observation 1.2: Hardcoded Fake Exit Gains in `agents/executor.py` (`squareoff_all`)
In `agents/executor.py` (lines 110–112):
```python
110: entry_premium = float(pos["entry_premium"])
111: 
112: exit_premium = round(entry_premium * 1.03, 2)
```
Exit premium is hardcoded as `entry_premium * 1.03` (+3% gain) regardless of actual market price movement, violating paper trading realism.

### Observation 1.3: Defective Position Monitoring in `agents/executor.py` (`monitor_positions`)
In `agents/executor.py` (lines 90–99):
```python
90: def monitor_positions(self, state: Dict[str, Any]) -> None:
91:     open_positions = state.get("open_positions", [])
92:     if not open_positions:
93:         return
94: 
95:     ist_tz = timezone(timedelta(hours=5, minutes=30))
96:     now_ist = datetime.now(ist_tz)
97:     if now_ist.weekday() < 5 and (now_ist.hour > 15 or (now_ist.hour == 15 and now_ist.minute >= 15)):
98:         logger.info("[F&O Executor] 3:15 PM IST Auto Square-Off triggered. Closing all open F&O positions...")
99:         self.squareoff_all(state)
```
`monitor_positions()` only evaluates the EOD 3:15 PM IST condition. It completely lacks bar-by-bar live spot price checking against `sl_spot` and `target_spot`, and does not execute individual position exits when stop loss or target thresholds are breached.

### Observation 1.4: Missing CSV Header Check on Empty File in `core/state.py`
In `core/state.py` (lines 44–55):
```python
44: os.makedirs(os.path.dirname(TRADE_LOG_FILE), exist_ok=True)
45: file_exists = os.path.exists(TRADE_LOG_FILE)
...
53: if not file_exists:
54:     writer.writeheader()
```
If `trade_log.csv` exists but has 0 bytes, `os.path.exists(TRADE_LOG_FILE)` returns `True`, preventing header creation and producing invalid CSV rows without headers.

---

## 2. Logic Chain

1. **Spot Price Propagation**:
   - `FOScoutAgent` extracts `spot_cmp` from live market data (or yfinance fallback).
   - `FOJudgeAgent` evaluates trade candidates using `scout.spot_cmp`.
   - `FOContractData` in `core/schemas.py` must include `spot_entry: float = 0.0`.
   - In `judge.py`, `contract.spot_entry = spot` ensures underlying spot price is attached to the verdict contract.
   - `FOExecutorAgent.execute()` reads `verdict.contract.spot_entry` (or `verdict.position_sizing_inr` fallback if missing) as `spot_cmp`.

2. **Directional SL / Target Calculation**:
   - For **Bullish** positions (`OPTION_CE`, `SCALP_CE`, `FUTURES_LONG`):
     - Stop Loss: `sl_spot = spot_cmp * (1 - sl_pct)` (default 1.5% below entry spot).
     - Target: `target_spot = spot_cmp * (1 + target_pct)` (default 3.0% above entry spot).
   - For **Bearish** positions (`OPTION_PE`, `SCALP_PE`, `FUTURES_SHORT`):
     - Stop Loss: `sl_spot = spot_cmp * (1 + sl_pct)` (1.5% above entry spot, since spot rise harms put/short positions).
     - Target: `target_spot = spot_cmp * (1 - target_pct)` (3.0% below entry spot, since spot fall benefits put/short positions).

3. **Real-Time Bar-by-Bar Position Monitoring**:
   - `monitor_positions(state, bar_data=None)` receives optional live bar data or fetches latest spot prices via `yfinanceWrapper.fetch_ohlcv(ticker, timeframe="1m")`.
   - For each open position in `state["open_positions"]`:
     - Compares live spot price against `sl_spot` and `target_spot` based on direction.
     - If triggered, invokes `exit_position(pos, state, current_spot=live_spot, exit_reason=reason)`.
   - Also evaluates 3:15 PM IST Auto Square-Off, invoking `squareoff_all(state, bar_data=bar_data)` with `exit_reason="eod_squareoff"`.

4. **Dynamic Exit Execution & Pricing**:
   - `exit_position()` calculates actual market exit premium:
     - Options: Uses `OptionsEngine.calculate_bs_price_and_greeks(spot=current_spot, strike=pos["strike_price"], dte=pos.get("expiry_dte", 7), iv_pct=vix, option_type=opt_type)` or delta-adjusted pricing `entry_premium + delta * (current_spot - entry_spot)`.
     - Futures: Uses `current_spot`.
   - Calculates exit transaction costs using `OptionsEngine.calculate_trade_costs(exit_val, is_sell=True, contract_type=...)`.
   - Calculates gross P&L, net P&L after exit brokerage, and net return percentage.
   - Updates `portfolio_state.json` fields (`pool_deployed`, `pool_available`, `daily_pnl_inr`, `daily_pnl_pct`, `total_brokerage_paid_inr`) and appends trade exit record to `trade_log.csv`.

5. **State Persistence & Exception Safety**:
   - `core/state.py` saves JSON state atomically using temp files / try-except error handling.
   - `append_to_fo_trade_log()` checks `os.path.exists(TRADE_LOG_FILE) and os.path.getsize(TRADE_LOG_FILE) > 0` before omitting the CSV header.

---

## 3. Caveats

1. **Market Off-Hours Data Availability**: During market close or weekends, `yfinance` returns the last available daily close price. If live spot price cannot be fetched, position monitoring falls back gracefully to `pos["entry_spot"]` to prevent execution crashes.
2. **Implied Volatility (IV) Assumption**: When re-pricing option exit premiums outside live option chains, Black-Scholes uses current India VIX (or default 14.5%) as IV proxy.
3. **Transaction Fee Accuracy**: Exit costs strictly incorporate flat ₹20 brokerage, STT (0.0625% on option sell / 0.0125% on futures sell), exchange fees, and 18% GST via `OptionsEngine`.

---

## 4. Conclusion & Detailed Code Design for Worker

The Worker MUST modify three files: `core/schemas.py`, `agents/judge.py`, `agents/executor.py`, and `core/state.py`.

### Change 1: `core/schemas.py`
Add `spot_entry: float = 0.0` to `FOContractData`.

```python
class FOContractData(BaseModel):
    contract_type: str  # "OPTION_CE" / "OPTION_PE" / "FUTURES"
    symbol: str
    strike_price: float
    expiry_dte: int
    lot_size: int
    lots_qty: int
    total_shares: int
    option_premium: float
    delta: float
    gamma: float
    theta_per_day: float
    vega: float
    premium_value_inr: float
    estimated_brokerage_inr: float = 20.0
    estimated_total_cost_inr: float
    spot_entry: float = 0.0  # ADDED: Actual underlying spot CMP at entry
```

### Change 2: `agents/judge.py`
In `FOJudgeAgent.run()`, assign `spot_entry=spot` when instantiating `FOContractData`.

```python
contract = FOContractData(
    contract_type=c_type,
    symbol=symbol,
    strike_price=strike,
    expiry_dte=dte,
    lot_size=lot_size,
    lots_qty=lots,
    total_shares=total_shares,
    option_premium=premium,
    delta=bs_res["delta"],
    gamma=bs_res["gamma"],
    theta_per_day=bs_res["theta_per_day"],
    vega=bs_res["vega"],
    premium_value_inr=round(total_premium_val, 2),
    estimated_brokerage_inr=self.brokerage_fee,
    estimated_total_cost_inr=round(costs["total_cost"], 2),
    spot_entry=round(spot, 2)  # ADDED: Underlying spot CMP
)
```

### Change 3: `agents/executor.py`
Replace `FOExecutorAgent` in `agents/executor.py` with the complete production design:

```python
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from core.data_sources import yfinanceWrapper
from core.state import save_fo_state, append_to_fo_trade_log
from core.schemas import FOJudgeOutput
from core.options_engine import OptionsEngine

logger = logging.getLogger(__name__)

class FOExecutorAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.options_engine = OptionsEngine()
        self.brokerage_per_order = config.get("capital", {}).get("brokerage_per_order_inr", 20.0)

    def execute(self, verdict: FOJudgeOutput, state: Dict[str, Any], spot_price: Optional[float] = None) -> bool:
        if verdict.verdict in ["AVOID", "REJECT", "WATCHLIST"]:
            return False

        contract = verdict.contract
        ticker = verdict.ticker
        symbol = contract.symbol
        c_type = contract.contract_type
        strike = contract.strike_price
        lots = contract.lots_qty
        total_shares = contract.total_shares
        premium = contract.option_premium
        premium_val = contract.premium_value_inr
        brokerage = contract.estimated_brokerage_inr
        total_cost = contract.estimated_total_cost_inr

        total_cash_required = premium_val + total_cost
        if state["pool_available"] < total_cash_required:
            logger.warning(f"[F&O Executor] Insufficient funds for {ticker} {c_type}: Required ₹{total_cash_required:.2f}, Avail ₹{state['pool_available']:.2f}")
            return False

        # Determine spot entry price
        spot_entry = spot_price or getattr(contract, "spot_entry", 0.0)
        if spot_entry <= 0.0:
            spot_entry = contract.strike_price  # Fallback to strike price if spot not populated

        # Directional Stop-Loss and Target calculation
        is_bullish = ("CE" in c_type) or (c_type == "FUTURES_LONG")
        if is_bullish:
            sl_spot = round(spot_entry * 0.985, 2)    # -1.5% stop loss
            target_spot = round(spot_entry * 1.03, 2)  # +3.0% target gain
        else:
            sl_spot = round(spot_entry * 1.015, 2)    # +1.5% stop loss for PE / short
            target_spot = round(spot_entry * 0.97, 2)  # -3.0% target gain for PE / short

        logger.info(f"[F&O EXECUTOR] Executing {verdict.verdict} ({c_type}) for {symbol} {strike}: {lots} Lots ({total_shares} shares) @ Premium ₹{premium}. Spot: ₹{spot_entry}, SL: ₹{sl_spot}, TP: ₹{target_spot}")

        # Deduct capital & brokerage fee
        state["pool_available"] -= total_cash_required
        state["pool_deployed"] += premium_val
        state["total_brokerage_paid_inr"] += brokerage
        state["trades_today"] += 1

        run_id = f"{symbol}_{c_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        new_position = {
            "ticker": ticker,
            "contract_type": c_type,
            "symbol": symbol,
            "strike_price": strike,
            "lots": lots,
            "total_shares": total_shares,
            "entry_premium": premium,
            "entry_spot": spot_entry,
            "sl_spot": sl_spot,
            "target_spot": target_spot,
            "entered_at": datetime.utcnow().isoformat() + "Z",
            "megabull_order_id": run_id,
            "brokerage_paid_inr": brokerage,
            "delta": getattr(contract, "delta", 0.5),
            "expiry_dte": getattr(contract, "expiry_dte", 7),
            "verdict": verdict.verdict,
            "waterfall_score": verdict.waterfall_score
        }
        state["open_positions"].append(new_position)
        save_fo_state(state)

        return True

    def _get_live_spot(self, ticker: str, bar_data: Optional[Dict[str, Any]] = None) -> Optional[float]:
        if bar_data:
            if ticker in bar_data:
                val = bar_data[ticker]
                if isinstance(val, (int, float)): return float(val)
                if isinstance(val, dict) and "close" in val: return float(val["close"])
                if isinstance(val, dict) and "Close" in val: return float(val["Close"])
            for k, v in bar_data.items():
                if k in ticker or ticker in k:
                    if isinstance(v, (int, float)): return float(v)
                    if isinstance(v, dict) and "close" in v: return float(v["close"])

        try:
            df = yfinanceWrapper.fetch_ohlcv(ticker, timeframe="1m", period="1d")
            if not df.empty and 'Close' in df.columns:
                return float(df['Close'].iloc[-1])
        except Exception as e:
            logger.error(f"[F&O Executor] Error fetching live spot for {ticker}: {e}")
        return None

    def exit_position(self, pos: Dict[str, Any], state: Dict[str, Any], current_spot: float, exit_reason: str) -> Dict[str, Any]:
        symbol = pos["symbol"]
        c_type = pos["contract_type"]
        total_shares = int(pos["total_shares"])
        entry_premium = float(pos["entry_premium"])
        entry_spot = float(pos["entry_spot"])
        strike = float(pos["strike_price"])
        dte = int(pos.get("expiry_dte", 7))
        delta = float(pos.get("delta", 0.5))

        # Dynamic Exit Premium Pricing
        is_option = ("OPTION" in c_type) or ("SCALP" in c_type)
        if is_option:
            opt_type = "CE" if "CE" in c_type else "PE"
            try:
                vix = yfinanceWrapper.fetch_vix()
                bs_res = self.options_engine.calculate_bs_price_and_greeks(
                    spot=current_spot, strike=strike, dte=dte, iv_pct=vix, option_type=opt_type
                )
                exit_premium = bs_res["price"]
            except Exception:
                # Delta-adjusted fallback
                spot_change = (current_spot - entry_spot) if opt_type == "CE" else (entry_spot - current_spot)
                approx_change = spot_change * abs(delta)
                exit_premium = max(0.50, round(entry_premium + approx_change, 2))
        else:
            exit_premium = round(current_spot, 2)

        exit_val = exit_premium * total_shares
        entry_val = entry_premium * total_shares

        # Exit transaction costs
        costs = self.options_engine.calculate_trade_costs(
            turnover_inr=exit_val, is_sell=True, contract_type="OPTION" if is_option else "FUTURES"
        )
        exit_cost = costs["total_cost"]
        entry_brokerage = float(pos.get("brokerage_paid_inr", self.brokerage_per_order))

        gross_pnl = exit_val - entry_val
        net_pnl = gross_pnl - exit_cost
        pnl_pct = (net_pnl / entry_val) * 100.0 if entry_val > 0 else 0.0

        # Update Portfolio State
        state["pool_deployed"] = max(0.0, state["pool_deployed"] - entry_val)
        state["pool_available"] += (entry_val + net_pnl)
        state["daily_pnl_inr"] += net_pnl
        state["pool_total"] = state["pool_available"] + state["pool_deployed"]
        state["daily_pnl_pct"] = round((state["daily_pnl_inr"] / 500000.0) * 100.0, 2)
        state["total_brokerage_paid_inr"] += exit_cost

        logger.info(f"[F&O Executor] Exited {symbol} {c_type} ({exit_reason}) @ Spot ₹{current_spot:.2f}, Prem ₹{exit_premium:.2f}. Net P&L: ₹{net_pnl:.2f} ({pnl_pct:.2f}%)")

        # Append complete trade record to trade_log.csv
        trade_log_row = {
            "run_id": pos.get("megabull_order_id", f"{symbol}_{c_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"),
            "ticker": pos["ticker"],
            "symbol": symbol,
            "verdict": pos.get("verdict", c_type),
            "contract_type": c_type,
            "strike_price": strike,
            "lots": pos["lots"],
            "total_shares": total_shares,
            "spot_entry": entry_spot,
            "option_premium": entry_premium,
            "spot_sl": pos["sl_spot"],
            "spot_target": pos["target_spot"],
            "waterfall_score": pos.get("waterfall_score", 8.0),
            "position_value_inr": round(entry_val, 2),
            "brokerage_fee_inr": round(entry_brokerage, 2),
            "total_cost_inr": round(entry_brokerage + exit_cost, 2),
            "executed_at": pos.get("entered_at", datetime.utcnow().isoformat() + "Z"),
            "exit_price": round(exit_premium, 2),
            "exit_reason": exit_reason,
            "realized_pnl_inr": round(net_pnl, 2),
            "realized_pnl_pct": round(pnl_pct, 2)
        }
        append_to_fo_trade_log(trade_log_row)

        return trade_log_row

    def monitor_positions(self, state: Dict[str, Any], bar_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        open_positions = list(state.get("open_positions", []))
        if not open_positions:
            return []

        exited_trades = []
        remaining_positions = []

        for pos in open_positions:
            ticker = pos["ticker"]
            c_type = pos["contract_type"]
            sl_spot = float(pos["sl_spot"])
            target_spot = float(pos["target_spot"])
            entry_spot = float(pos["entry_spot"])

            live_spot = self._get_live_spot(ticker, bar_data)
            if live_spot is None:
                live_spot = entry_spot  # Fallback to entry spot if live data unavailable

            is_bullish = ("CE" in c_type) or (c_type == "FUTURES_LONG")
            exit_reason = None

            if is_bullish:
                if live_spot <= sl_spot:
                    exit_reason = "sl_hit"
                elif live_spot >= target_spot:
                    exit_reason = "target_hit"
            else:
                if live_spot >= sl_spot:
                    exit_reason = "sl_hit"
                elif live_spot <= target_spot:
                    exit_reason = "target_hit"

            if exit_reason:
                trade_record = self.exit_position(pos, state, current_spot=live_spot, exit_reason=exit_reason)
                exited_trades.append(trade_record)
            else:
                remaining_positions.append(pos)

        state["open_positions"] = remaining_positions
        if exited_trades:
            save_fo_state(state)

        # Check 3:15 PM IST Auto Square-Off
        ist_tz = timezone(timedelta(hours=5, minutes=30))
        now_ist = datetime.now(ist_tz)
        if now_ist.weekday() < 5 and (now_ist.hour > 15 or (now_ist.hour == 15 and now_ist.minute >= 15)):
            if state.get("open_positions"):
                logger.info("[F&O Executor] 3:15 PM IST Auto Square-Off triggered. Closing remaining open positions...")
                eod_exits = self.squareoff_all(state, bar_data=bar_data)
                exited_trades.extend(eod_exits)

        return exited_trades

    def squareoff_all(self, state: Dict[str, Any], bar_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        open_positions = list(state.get("open_positions", []))
        if not open_positions:
            return []

        exited_trades = []
        for pos in open_positions:
            ticker = pos["ticker"]
            entry_spot = float(pos["entry_spot"])
            live_spot = self._get_live_spot(ticker, bar_data) or entry_spot
            
            trade_record = self.exit_position(pos, state, current_spot=live_spot, exit_reason="eod_squareoff")
            exited_trades.append(trade_record)

        state["open_positions"] = []
        save_fo_state(state)
        return exited_trades
```

### Change 4: `core/state.py`
Update `core/state.py` for atomic state saving and header verification on empty files:

```python
import json
import os
import csv
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(ROOT_DIR, "state", "portfolio_state.json")
TRADE_LOG_FILE = os.path.join(ROOT_DIR, "state", "trade_log.csv")

DEFAULT_STATE = {
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

def load_fo_state() -> Dict[str, Any]:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading F&O state: {e}")
    return DEFAULT_STATE.copy()

def save_fo_state(state: Dict[str, Any]) -> None:
    try:
        state["last_updated"] = datetime.utcnow().isoformat() + "Z"
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        temp_file = STATE_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)
        os.replace(temp_file, STATE_FILE)
    except Exception as e:
        logger.error(f"Error saving F&O state to {STATE_FILE}: {e}")

def append_to_fo_trade_log(row: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(TRADE_LOG_FILE), exist_ok=True)
        file_has_content = os.path.exists(TRADE_LOG_FILE) and os.path.getsize(TRADE_LOG_FILE) > 0
        fieldnames = [
            "run_id", "ticker", "symbol", "verdict", "contract_type", "strike_price",
            "lots", "total_shares", "spot_entry", "option_premium", "spot_sl", "spot_target",
            "waterfall_score", "position_value_inr", "brokerage_fee_inr", "total_cost_inr",
            "executed_at", "exit_price", "exit_reason", "realized_pnl_inr", "realized_pnl_pct"
        ]
        with open(TRADE_LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_has_content:
                writer.writeheader()
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    except Exception as e:
        logger.error(f"Error appending trade log to {TRADE_LOG_FILE}: {e}")
```

---

## 5. Verification Method

To verify the implementation independently, execute the following unit test script in Python:

```bash
python -c "
from core.state import load_fo_state, save_fo_state, append_to_fo_trade_log
from agents.executor import FOExecutorAgent
from core.schemas import FOJudgeOutput, FOContractData
from datetime import datetime

config = {'capital': {'brokerage_per_order_inr': 20.0}}
executor = FOExecutorAgent(config)
state = load_fo_state()

# 1. Test Trade Execution with spot entry
contract = FOContractData(
    contract_type='OPTION_CE', symbol='NIFTY', strike_price=24200, expiry_dte=7,
    lot_size=25, lots_qty=2, total_shares=50, option_premium=145.0, delta=0.55,
    gamma=0.001, theta_per_day=-5.0, vega=12.0, premium_value_inr=7250.0,
    estimated_brokerage_inr=20.0, estimated_total_cost_inr=24.50, spot_entry=24210.50
)
judge_out = FOJudgeOutput(
    ticker='^NSEI', run_timestamp=datetime.utcnow(), verdict='BUY_CE',
    waterfall_score=8.5, confidence=8.5, contract=contract, position_sizing_inr=7274.50,
    reasoning='Test execute'
)

executed = executor.execute(judge_out, state)
assert executed, 'Execution failed'
assert len(state['open_positions']) == 1, 'Position not added'
pos = state['open_positions'][0]
assert pos['entry_spot'] == 24210.50, f'Incorrect entry_spot: {pos[\"entry_spot\"]}'
assert pos['sl_spot'] == round(24210.50 * 0.985, 2), 'Incorrect SL spot'
assert pos['target_spot'] == round(24210.50 * 1.03, 2), 'Incorrect Target spot'

# 2. Test Position Monitoring & Exit
# Simulate spot price hitting target (24210.50 * 1.035 = 25057.87)
bar_data = {'^NSEI': 25057.87}
exits = executor.monitor_positions(state, bar_data=bar_data)
assert len(exits) == 1, 'Position failed to exit on target hit'
assert len(state['open_positions']) == 0, 'Open position remaining after exit'
assert exits[0]['exit_reason'] == 'target_hit', f'Wrong exit reason: {exits[0][\"exit_reason\"]}'
assert exits[0]['realized_pnl_inr'] > 0, 'PnL should be positive on target hit'

print('=== ALL PAPER EXECUTION & POSITION MONITORING TESTS PASSED ===')
"
```

### Invalidation Conditions:
1. `entry_spot` in `open_positions` equals position sizing cash value (₹70,000+) instead of spot CMP (24,000+).
2. Exits produce hardcoded `entry_premium * 1.03` output.
3. `monitor_positions()` fails to trigger exits when `bar_data` breaches `sl_spot` or `target_spot`.
4. File write exceptions crash the execution loop.
