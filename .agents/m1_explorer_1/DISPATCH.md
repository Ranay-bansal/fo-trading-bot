## 2026-08-08T06:16:21Z
<USER_REQUEST>
You are M1 Explorer 1 (`teamwork_preview_explorer`).
Working directory: c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\m1_explorer_1
Original request path: c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\ORIGINAL_REQUEST.md
Project specification path: c:\Users\RANAY\Desktop\FO TRADING BOT\PROJECT.md

Task: Formulate the detailed implementation specification for Bot 1 (Equity Intraday Cash Strategy Execution Engine).
Must address:
- Dedicated equity stock signal generator (`Bot1EquityAgent` in `agents/bot1_cash.py`).
- Equity universe definition in `config/settings.yaml` (e.g. top liquid NIFTY50 cash stocks like RELIANCE.NS, HDFCBANK.NS, ICICIBANK.NS, INFY.NS, TCS.NS).
- Cash margin sizing (1x cash margin, position size calculation based on available pool).
- Integration into `main.py` execution pipeline so both Bot 1 (Cash) and Bot 2 (F&O Swarm) run seamlessly.

Read `c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\ORIGINAL_REQUEST.md` and `PROJECT.md`. Inspect `main.py`, `agents/`, `config/settings.yaml`, `core/data_sources.py`.
Write handoff report to `c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\m1_explorer_1\handoff.md` with exact code design, function signatures, and file changes for the Worker.
Update `progress.md` in your folder. When done, write `handoff.md` and send a message back with the summary and path to handoff.md.
</USER_REQUEST>
