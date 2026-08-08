# Codebase Survey & Gap Analysis Report: Shadow Traders Quant Engine

## 1. Observation

Direct observations from examining the codebase at `c:\Users\RANAY\Desktop\FO TRADING BOT`:

### A. Strategy Execution Engine Architecture (Bot 1 vs Bot 2)
- **`main.py` (lines 5-10, 24-64)**:
  ```python
  from core.state import load_fo_state, save_fo_state
  from core.data_sources import yfinanceWrapper
  from agents.scout import FOScoutAgent
  from agents.technician import FOTechnicianAgent
  from agents.judge import FOJudgeAgent
  from agents.executor import FOExecutorAgent
  ...
  def run_fo_pipeline():
      ...
      executor = FOExecutorAgent(config)
      scout = FOScoutAgent(config)
      technician = FOTechnicianAgent(config)
      judge = FOJudgeAgent(config)
      ...
      timeframes = ["5m", "1m", "15m"]
      for tf in timeframes:
          candidates = scout.run(timeframe=tf)
          for cand in candidates:
              tech_out = technician.run(cand, timeframe=tf, vix_val=vix_val)
              judge_out = judge.run(cand, tech_out, state, timeframe=tf)
              if judge_out.verdict != "AVOID":
                  executor.execute(judge_out, state)
  ```
  - **Observation**: `main.py` only imports and runs F&O agents (`FOScoutAgent`, `FOTechnicianAgent`, `FOJudgeAgent`, `FOExecutorAgent`). There is **no Bot 1 (Equity Intraday Cash)** strategy engine or execution path defined anywhere in `main.py` or `agents/`.
- **`config/settings.yaml` (lines 22-85)**:
  - Defines `fo_universe` containing 2 index contracts (`^NSEI`, `^NSEBANK`) and 10 stock option/futures contracts (`RELIANCE.NS`, `HDFCBANK.NS`, `ICICIBANK.NS`, `INFY.NS`, `TCS.NS`, `DLF.NS`, `BHARTIARTL.NS`, `HINDALCO.NS`, `TATASTEEL.NS`, `MARUTI.NS`) with lot sizes and strike steps.
  - **Observation**: No separate universe or capital allocation rules exist for Bot 1 (Equity Intraday Cash).

### B. Live Signal Generation & Zero-Latency Bar Execution Logic
- **`core/data_sources.py` (lines 9-25)**:
  ```python
  class yfinanceWrapper:
      @staticmethod
      def fetch_ohlcv(ticker: str, timeframe: str = "5m", period: str = "1d") -> pd.DataFrame:
          data = yf.download(ticker, period=period, interval=timeframe, progress=False)
  ```
  - **Observation**: yfinance HTTP download is used for market data fetching. This introduces network overhead and latency, and does not provide real-time tick/bar streaming.
- **`main.py` (lines 48-60)**:
  - Execution runs as a single-shot batch script iterating over static timeframes `["5m", "1m", "15m"]`.
  - **Observation**: No persistent WebSocket connection, tick queue, or continuous real-time bar event loop exists.

### C. 3-Way Risk Committee Debaters (Scout, Technician, Newsdesk, Bull, Bear)
- **`agents/` directory contents**:
  - `agents/scout.py` (`FOScoutAgent`)
  - `agents/technician.py` (`FOTechnicianAgent`)
  - `agents/judge.py` (`FOJudgeAgent`)
  - `agents/executor.py` (`FOExecutorAgent`)
  - **Observation**: `Newsdesk`, `Bull`, and `Bear` agent files do not exist in `agents/`.
- **`agents/judge.py` (lines 33-40, 48-62)**:
  ```python
  base_score = 5.0
  scout_mod = float(scout.scout_modifier)
  tech_mod = float(tech.technical_score)
  waterfall_score = base_score + (scout_mod * 1.0) + (tech_mod * 1.8)
  ```
  - **Observation**: `FOJudgeAgent` computes a deterministic arithmetic score combining Scout and Technician modifiers. No multi-agent debate, risk counter-argumentation, or consensus protocol is implemented.
- **`index.html` (lines 602-617)**:
  ```html
  <tbody id="committee-table-body">
    <tr>
      <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 28px 0;">
        No active debate logs for current scan window. Subagent swarm evaluating market signals.
      </td>
    </tr>
  </tbody>
  ```
  - **Observation**: The UI table for the 3-Way Risk Committee contains static text and is not hydrated with debate arguments or committee decisions.

### D. Paper Trading Execution & State Management
- **`core/state.py` (lines 14-55)**:
  - Manages `state/portfolio_state.json` and `state/trade_log.csv`.
  - `DEFAULT_STATE` schema: `last_updated`, `pool_total` (500000.0), `pool_available`, `pool_deployed`, `daily_pnl_inr`, `daily_pnl_pct`, `total_brokerage_paid_inr`, `trades_today`, `open_positions`.
- **`agents/executor.py` (lines 90-129)**:
  ```python
  def monitor_positions(self, state: Dict[str, Any]) -> None:
      ...
      if now_ist.weekday() < 5 and (now_ist.hour > 15 or (now_ist.hour == 15 and now_ist.minute >= 15)):
          self.squareoff_all(state)

  def squareoff_all(self, state: Dict[str, Any]) -> None:
      ...
      for pos in open_positions:
          ...
          exit_premium = round(entry_premium * 1.03, 2)
          exit_val = exit_premium * total_shares
          gross_pnl = exit_val - entry_val
  ```
  - **Observation 1**: `monitor_positions()` only evaluates time condition (`>= 15:15 IST`). It does not check live spot price against `sl_spot` or `target_spot`.
  - **Observation 2**: `squareoff_all()` hardcodes `exit_premium = entry_premium * 1.03` (+3% gain) instead of fetching live exit prices.
- **`index.html` JavaScript (lines 656-672, 703-704)**:
  ```javascript
  async function updateDashboard() {
    try {
      const res = await fetch('../state/portfolio_state.json');
      if (res.ok) {
        const state = await res.json();
        document.getElementById('val-total').innerText = '₹' + Number(state.pool_total || 500000).toLocaleString(...);
        document.getElementById('val-available').innerText = '₹' + Number(state.pool_available || 500000).toLocaleString(...);
        ...
      }
    } catch(e) {}
  }
  ```
  - **Observation 3**: `updateDashboard()` only updates top KPI stat cards (`val-total`, `val-available`, `val-pnl`, `val-brokerage`). It does not populate `#trade-log-body` with rows from `trade_log.csv` or `open_positions`.

---

## 2. Logic Chain

1. **R1 Requirement vs. Existing Codebase**:
   - R1 requires: "Ensure zero-latency bar-by-bar execution, live signal generation, and 3-way risk committee debaters (Scout, Technician, Newsdesk, Bull, Bear) for both Bot 1 (Equity Intraday Cash) and Bot 2 (F&O Options Swarm)."
   - *Observation A & B show*: `main.py` only implements F&O (Bot 2) using `yfinance` batch queries. Equity Intraday Cash (Bot 1) is completely missing.
   - *Observation C shows*: `Newsdesk`, `Bull`, and `Bear` agents do not exist, and `FOJudgeAgent` uses a static mathematical formula rather than a risk debate protocol.
   - *Observation D shows*: Paper trading position monitoring omits real-time SL/target checks and hardcodes exit premiums at 3% profit. Furthermore, the dashboard UI omits trade log and committee debate hydration.

2. **Impact on System Functionality & Acceptance Criteria**:
   - Without Bot 1 (Equity Intraday Cash), the system only satisfies half of the asset class scope.
   - Without real-time SL/target monitoring during paper execution, open positions remain unmanaged until 3:15 PM EOD and exit with artificial P&L (+3%).
   - Without committee debate logging, the Risk Committee tab on the UI remains static and empty, failing the acceptance criterion for debate log rendering without errors.

---

## 3. Caveats

- **Network / Data Source Constraints**: `yfinance` is subject to rate-limiting and market hour restrictions. High-frequency or zero-latency testing in paper mode requires a robust local mock bar stream / backtest bar generator or WebSocket provider.
- **Frontend File Redundancy**: Root `index.html`, `dashboard/index.html`, and `public/index.html` are generated and synchronized via `scratch/fix_all_index_files.py` and `scratch/sync_public.py`. Any UI changes must be reflected across all target files.

---

## 4. Conclusion

The current codebase provides a solid foundation for F&O option pricing (Black-Scholes engine, strike selection, transaction cost calculations) and state persistence. However, significant gaps exist against the R1 requirements:

1. **Bot 1 (Equity Intraday Cash)**: Completely missing; needs dedicated strategy engine, position sizing (cash margin & share count), and signal generation.
2. **Bot 2 (F&O Options Swarm)**: Needs parallel execution capability and true zero-latency / mock bar-by-bar stream processing.
3. **3-Way Risk Committee Debaters**: Missing `NewsdeskAgent`, `BullDebaterAgent`, `BearDebaterAgent`, and debate consensus protocol.
4. **Paper Execution & State**: Needs real-time bar-by-bar position monitoring (SL/TP triggers), realistic live exit pricing, and complete UI hydration for trade logs, open positions, and committee debate logs.

---

## 5. Verification Method

To independently verify these findings:

1. **Inspect Code Files**:
   - Run `view_file` on `c:\Users\RANAY\Desktop\FO TRADING BOT\main.py` to confirm lack of Bot 1 imports and batch yfinance loop.
   - Run `view_file` on `c:\Users\RANAY\Desktop\FO TRADING BOT\agents\judge.py` to confirm absence of Bull/Bear/Newsdesk debate logic.
   - Run `view_file` on `c:\Users\RANAY\Desktop\FO TRADING BOT\agents\executor.py` (lines 90-129) to confirm hardcoded +3% exit premium in `squareoff_all()`.
   - Run `view_file` on `c:\Users\RANAY\Desktop\FO TRADING BOT\index.html` (lines 656-672) to confirm `updateDashboard()` only updates top KPI boxes.

2. **Invalidation Conditions**:
   - Findings 1 & 3 would be invalidated if `Bot 1` strategy classes or `Newsdesk`/`Bull`/`Bear` debater modules were located under a different directory (confirmed absent via `find_by_name`).
