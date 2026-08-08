# BRIEFING — 2026-08-08T06:33:55Z

## Mission
Implement Milestone 2: 3-Way Risk Committee Debaters (Newsdesk, Bull Debater, Bear Debater, Judge Consensus Protocol, schemas, and state persistence).

## 🔒 My Identity
- Archetype: implementer, qa, specialist
- Roles: implementer, qa, specialist
- Working directory: c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\m2_worker_1
- Original parent: 718b86ec-cb08-411c-b616-e59d94964d1d
- Milestone: Milestone 2 — 3-Way Risk Committee Debaters

## 🔒 Key Constraints
- DO NOT CHEAT. All implementations must be genuine.
- No hardcoded test results or mock shortcuts.
- Maintain backward-compatible `run()` signature in FOJudgeAgent.
- Atomic `.tmp` file writing with fallback for Windows file locks in `state.py`.
- Risk Committee Override veto enforcement rules: Bear Risk >= 7.5, Catalyst Risk >= 8.0, Macro Risk >= 8.5, or VIX >= 28.0.

## Current Parent
- Conversation ID: 718b86ec-cb08-411c-b616-e59d94964d1d
- Updated: 2026-08-08T06:33:55Z

## Task Summary
- **What to build**: 
  1. `core/schemas.py`: Add `NewsdeskOutput`, `BullDebaterOutput`, `BearDebaterOutput`, `CommitteeDebateRecord`, update `FOJudgeOutput`.
  2. `core/state.py`: Add `COMMITTEE_DEBATE_LOG_FILE` and `append_to_committee_debate_log`.
  3. `agents/newsdesk.py`: `NewsdeskAgent`.
  4. `agents/bull_debater.py`: `BullDebaterAgent`.
  5. `agents/bear_debater.py`: `BearDebaterAgent`.
  6. `agents/judge.py`: `FOJudgeAgent` refactoring for 3-Way Risk Committee Debate Protocol.
- **Success criteria**: All tests in `tests/test_debaters.py` and `tests/` pass, syntax compilation passes, pipeline test `main.py` succeeds.
- **Interface contracts**: PROJECT.md and M2 Explorer handoff.

## Key Decisions Made
- Initial setup.

## Artifact Index
- c:\Users\RANAY\Desktop\FO TRADING BOT\.agents\m2_worker_1\handoff.md — Final handoff report

## Change Tracker
- **Files modified**: None yet
- **Build status**: TBD
- **Pending issues**: None

## Quality Status
- **Build/test result**: TBD
- **Lint status**: TBD
- **Tests added/modified**: TBD

## Loaded Skills
- None
