## 2026-08-08T06:17:34Z
You are M1 Worker (`teamwork_preview_worker`).
Working directory: c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\m1_worker_1
Original request path: c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\ORIGINAL_REQUEST.md
Project specification path: c:\Users\RANAY\Desktop\FO TRADING BOT\PROJECT.md

Task: Implement Milestone 1 — Core Strategy Execution Engine (Bot 1 Equity Cash Engine, Bot 2 F&O Options Swarm Engine, Zero-Latency Bar-by-Bar Streaming Event Loop, and Real-Time Paper SL/TP Position Monitoring).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Please read `c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\ORIGINAL_REQUEST.md`, `c:\Users\RANAY\Desktop\FO TRADING BOT\PROJECT.md`, and the 3 Explorer handoff reports:
- `c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\m1_explorer_1\handoff.md`
- `c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\m1_explorer_2\handoff.md`
- `c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\m1_explorer_3\handoff.md`

Perform the following code changes:
1. `config/settings.yaml`: Add `bot1_equity` configuration block with 10 NIFTY50 cash stocks and `cash_margin_multiplier: 1.0`.
2. `core/schemas.py`: Add `Bot1Signal` schema and `spot_entry: float = 0.0` field to `FOContractData`.
3. `agents/bot1_cash.py`: Create `Bot1EquityAgent` with 1x cash margin sizing and multi-indicator technical scoring (EMA, RSI, ADX, ATR, VWAP, Supertrend).
4. `agents/bot2_options.py`: Create `Bot2OptionSwarmAgent` wrapping Scout, Technician, OptionsEngine, and Judge into unified F&O signal generation.
5. `core/data_sources.py`: Add `BarEvent` and `StreamingTickSimulator` for zero-latency event streaming.
6. `agents/executor.py`: Implement `execute_cash()`, real-time position monitoring (`monitor_positions()`) checking live spot prices against `sl_spot` and `target_spot`, dynamic exit pricing in `exit_position()` using Black-Scholes / delta adjustment, and `squareoff_all()`.
7. `core/state.py`: Update `save_fo_state` for atomic write and `append_to_fo_trade_log` to verify file size before skipping CSV header.
8. `agents/judge.py`: Ensure `contract.spot_entry = spot` is populated in `FOJudgeAgent.run()`.
9. `main.py`: Implement `run_continuous_stream()` and `run_quant_pipeline()` running Bot 1 (Equity Cash) and Bot 2 (F&O Swarm) concurrently using `ThreadPoolExecutor`. Keep `run_fo_pipeline()` as alias.

After making the edits:
1. Run python syntax compilation check: `python -m py_compile core/data_sources.py core/schemas.py core/state.py agents/bot1_cash.py agents/bot2_options.py agents/executor.py agents/judge.py main.py`
2. Run functional test execution: `python main.py` and verify paper execution runs cleanly without crashes.
3. Write `handoff.md` in `c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\m1_worker_1\handoff.md` documenting all changes, build outputs, and test results.
4. Send a message to parent with the summary.
