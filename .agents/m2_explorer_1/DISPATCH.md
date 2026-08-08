## 2026-08-08T06:32:00Z
You are M2 Explorer 1 (`teamwork_preview_explorer`).
Working directory: c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\m2_explorer_1
Original request path: c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\ORIGINAL_REQUEST.md
Project specification path: c:\Users\RANAY\Desktop\FO TRADING BOT\PROJECT.md

Task: Formulate the detailed implementation specification for Milestone 2 — 3-Way Risk Committee Debaters (Scout, Technician, Newsdesk, Bull, Bear, and Judge Consensus Debate Protocol).
Must address:
1. `agents/newsdesk.py`: `NewsdeskAgent` calculating news sentiment, catalyst risk, market regime, and macro risk scores (0.0 to 10.0) with fallback.
2. `agents/bull_debater.py`: `BullDebaterAgent` formulating upside arguments, conviction score, target rationale, and key catalysts.
3. `agents/bear_debater.py`: `BearDebaterAgent` formulating downside risk counter-arguments, bear risk score, stop-loss risks, and market headwinds.
4. `agents/judge.py`: Refactor `FOJudgeAgent` to conduct a 3-way committee debate protocol combining Scout, Technician, Newsdesk, Bull, and Bear stances into a consensus score, Fact-Checker approval, and Risk Override status.
5. `core/state.py` & `core/schemas.py`: Add `CommitteeDebateRecord` schema and `append_to_committee_debate_log(record)` persisting debates to `state/committee_debate_log.json`.

Read `c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\ORIGINAL_REQUEST.md` and `PROJECT.md`. Inspect `agents/scout.py`, `agents/technician.py`, `agents/judge.py`, `core/schemas.py`, `core/state.py`.
Write handoff report to `c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\m2_explorer_1\handoff.md` with exact code designs, function signatures, and file changes for the Worker.
Update `progress.md` in your folder and send a message back.
