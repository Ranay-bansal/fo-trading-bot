## 2026-08-08T10:50:34Z
Task: Implement Milestone 2 — 3-Way Risk Committee Debaters (Scout, Technician, Newsdesk, Bull, Bear, and Judge Consensus Debate Protocol).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Please read `c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\ORIGINAL_REQUEST.md`, `c:\Users\RANAY\Desktop\FO TRADING BOT\PROJECT.md`, and `c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\m2_explorer_1\handoff.md`.

Implement the following files:
1. `core/schemas.py`: Add `NewsdeskOutput`, `BullDebaterOutput`, `BearDebaterOutput`, `CommitteeDebateRecord`, and update `FOJudgeOutput`.
2. `core/state.py`: Add `COMMITTEE_DEBATE_LOG_FILE` and `append_to_committee_debate_log(record)` with atomic `.tmp` file writing and fallback for Windows file locks.
3. `agents/newsdesk.py`: Create `NewsdeskAgent` calculating news sentiment, catalyst risk, market regime, and macro risk scores (0.0 to 10.0) with yfinance exception fallback.
4. `agents/bull_debater.py`: Create `BullDebaterAgent` formulating upside arguments, conviction score, target rationale, and catalysts.
5. `agents/bear_debater.py`: Create `BearDebaterAgent` formulating downside counter-arguments, bear risk score, stop-loss risks, and market headwinds.
6. `agents/judge.py`: Refactor `FOJudgeAgent` to conduct 3-Way Risk Committee Debate Protocol combining Scout, Technician, Newsdesk, Bull, and Bear stances into a weighted Consensus Score, Fact-Checker approval verification, Risk Committee Override veto enforcement (when Bear Risk >= 7.5, Catalyst Risk >= 8.0, Macro Risk >= 8.5, or VIX >= 28.0), and automatic log persistence to `state/committee_debate_log.json`. Maintain backward-compatible `run()` signature.

After implementing:
1. Run syntax compilation check: `python -m py_compile agents/newsdesk.py agents/bull_debater.py agents/bear_debater.py agents/judge.py core/schemas.py core/state.py`
2. Run debater test suite: `python -m unittest tests/test_debaters.py`
3. Run full E2E test suite: `python -m unittest discover -s tests -p "test_*.py"`
4. Run pipeline test: `python main.py`
5. Write `handoff.md` in `c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\m2_worker_2\handoff.md` and send a message back with the summary.
