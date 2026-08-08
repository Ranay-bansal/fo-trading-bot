# Project: Shadow Traders Quant Trading Platform

## Architecture
- **Bot 1 Strategy Engine (Equity Intraday Cash)**: Dedicated equity stock signal generator, cash margin position sizing (1x cash margin), zero-latency bar-by-bar stream/mock tick engine, real-time stop-loss & target monitoring.
- **Bot 2 Strategy Engine (F&O Options Swarm)**: Options & futures signal generation, Black-Scholes pricing, lot size calculation, zero-latency bar-by-bar execution, real-time SL/TP monitoring.
- **3-Way Risk Committee Debaters**: ScoutAgent (opportunity identification), TechnicianAgent (chart/momentum risk), NewsdeskAgent (catalyst/sentiment risk), BullDebaterAgent (upside rationale), BearDebaterAgent (downside risk), and JudgeAgent (consensus debate protocol & risk override).
- **Paper Trading Execution & State Hydration**: `core/state.py`, `state/portfolio_state.json`, `state/trade_log.csv`, `state/committee_debate_log.json`. Real-time position monitoring & live exit execution without hardcoded fake gains.
- **High-Performance Glassmorphism Dashboard UI**: Single-page UI (`index.html`, `public/index.html`, `dashboard/index.html` synced via `scratch/fix_all_index_files.py`), Plus Jakarta Sans & Inter typography, Lucide SVG icons, real-time hydration for top KPIs, executed trades table (`#trade-log-body`), 3-way risk debate table (`#committee-table-body`), and reflective memory table (`#memory-table-body`). Zero falsy 0 balance bugs.
- **PWA Offline Compliance**: `manifest.json`, `sw.js`, and static assets at root, `public/`, and `dashboard/` with valid asset paths and Service Worker offline caching.
- **Test Infrastructure & Vercel Deployments**: Formal test suite (unit + E2E integration tests in `tests/`), Vercel static deployment config without 404 path issues.

## Feature Inventory
Every feature from the Survey phase is mapped below to its assigned milestone.
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Bot 1 Equity Intraday Cash Engine | Equity cash signal generation, cash margin sizing, zero-latency bar-by-bar execution, paper trades | M1 | R1, survey |
| 2 | Bot 2 F&O Options Swarm Engine | Options/Futures signal generation, Black-Scholes pricing, zero-latency bar execution, paper trades | M1 | R1, survey |
| 3 | 3-Way Risk Committee Debaters | Scout, Technician, Newsdesk, Bull, Bear debaters and consensus protocol in Judge | M2 | R1, survey |
| 4 | Paper Execution & Real-Time Position Monitor | Real-time SL/TP trigger monitoring, live exit pricing, state persistence (`portfolio_state.json`, `trade_log.csv`, `committee_debate_log.json`) | M1 | R1, AC1, survey |
| 5 | Glassmorphism Dashboard UI & State Hydration | Hydrate top KPI stat cards (fixing falsy 0 balance bug), render executed trades log (`#trade-log-body`), 3-way debate log (`#committee-table-body`), and reflective memory (`#memory-table-body`) without undefined variable errors | M3 | R2, AC2, survey |
| 6 | PWA Offline Installation Compliance | Root `manifest.json`, `sw.js`, icon assets, and working Service Worker cache registration | M3 | R2, AC2, survey |
| 7 | Static Build Sync & Vercel Deployment Setup | Ensure `scratch/fix_all_index_files.py` syncs state fetch paths (`./state/...`) and `public/` assets cleanly so Vercel deployments serve cleanly | M4 | AC3, survey |
| 8 | Formal Test Suite & E2E Test Runner | Unit and integration test suite (`tests/test_engine.py`, `tests/test_ui.py`, `tests/test_pwa.py`, etc.) for Bot 1 & Bot 2 execution, state hydration, and committee debate logs | M5 | AC1, AC2, AC3 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Core Strategy Execution Engine (Bot 1 & Bot 2) | Equity Intraday Cash & F&O Options Swarm engines, zero-latency bar execution, paper trading SL/TP position monitoring | none | DONE |
| 2 | 3-Way Risk Committee Debaters | Scout, Technician, Newsdesk, Bull, Bear debaters & consensus debate protocol | M1 | PLANNED |
| 3 | Glassmorphism Dashboard UI, Hydration & PWA | Fix hydration JS (trade log, debate log, memory log, falsy balance bug), PWA root assets & SW | M1, M2 | PLANNED |
| 4 | Static Build & Vercel Deployment Sync | Sync root/public/dashboard index files, verify Vercel deployment static asset paths | M3 | PLANNED |
| 5 | Final Milestone: E2E Test Suite & Adversarial Hardening | Pass 100% of E2E tests (Tiers 1-4) and Tier 5 white-box adversarial coverage hardening | M1, M2, M3, M4 | PLANNED |

## Interface Contracts
### Bot 1 & Bot 2 Engine ↔ State / Debaters
- `Bot1EquityAgent`: `run(ticker, timeframe, state) -> Signal`
- `Bot2OptionSwarmAgent`: `run(ticker, timeframe, state) -> Signal`
- `CommitteeDebaterSwarm`: `debate(candidate, tech_out, news_out) -> CommitteeResult` (containing Scout, Technician, Newsdesk, Bull, Bear stances and Judge override)
- `FOExecutorAgent`: `execute(signal, state)`, `monitor_positions(state, bar_data)` (evaluates SL/TP triggers in real time)
- State JSON format: `portfolio_state.json` containing `pool_total`, `pool_available`, `pool_deployed`, `daily_pnl_inr`, `daily_pnl_pct`, `total_brokerage_paid_inr`, `open_positions`
- Trade CSV format: `trade_log.csv` containing `timestamp,bot_id,symbol,trade_type,quantity,entry_price,exit_price,pnl_inr,status`
- Debate JSON format: `committee_debate_log.json` containing `timestamp,symbol,scout_stance,tech_stance,news_stance,bull_stance,bear_stance,judge_verdict`

### State Files ↔ Dashboard UI (`index.html`)
- `fetch('./state/portfolio_state.json')` -> updates `#val-total`, `#val-available`, `#val-pnl`, `#val-brokerage` (using `??` nullish coalescing to prevent falsy 0 balance bug)
- `fetch('./state/trade_log.csv')` -> parses CSV and populates `#trade-log-body`
- `fetch('./state/committee_debate_log.json')` -> populates `#committee-table-body`
- `fetch('./state/reflective_memory.json')` -> populates `#memory-table-body`

## Code Layout
- `agents/`: `bot1_cash.py`, `bot2_options.py`, `scout.py`, `technician.py`, `newsdesk.py`, `bull_debater.py`, `bear_debater.py`, `judge.py`, `executor.py`
- `core/`: `data_sources.py`, `state.py`, `indicators.py`, `options_engine.py`
- `state/`: `portfolio_state.json`, `trade_log.csv`, `committee_debate_log.json`, `reflective_memory.json`
- Root / `public/` / `dashboard/`: `index.html`, `manifest.json`, `sw.js`, `background.jpg`, `logo.jpg`, `icon-192.png`, `icon-512.png`, `vercel.json`
- `scratch/`: `fix_all_index_files.py`, `sync_public.py`
- `tests/`: E2E and Unit test suite
