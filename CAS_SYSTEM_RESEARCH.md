# SEBI Closing Auction Session (CAS) — Comprehensive Quantitative & Algorithmic Research Report

## Executive Summary
This document outlines the architectural research, regulatory mandate, market microstructure impact, and quantitative adaptation required for algorithmic equity and F&O trading bots operating on the National Stock Exchange of India (NSE) and Bombay Stock Exchange (BSE) under the **Closing Auction Session (CAS)** regime.

---

## 1. Background & Market Imperative

Historically, the official closing price of equity shares and indices in the Indian cash market was derived via a **30-Minute Volume Weighted Average Price (VWAP)** between 3:00 PM and 3:30 PM IST.

### Vulnerabilities of the 30-Minute VWAP:
1. **Banging the Close:** Large institutional or speculative players could aggressively place market orders in the final 3-5 minutes of trading (3:25–3:30 PM) to distort the VWAP, skewing index closing values and option settlement payoffs.
2. **Execution Drift for Passive Indexers:** Passive ETFs and benchmark-tracking mutual funds faced tracking errors because continuous order matching during high-volatility closing minutes creates substantial slippage against the final VWAP.
3. **Global Alignment:** Tier-1 exchanges (NYSE, NASDAQ, London Stock Exchange, Tokyo Stock Exchange, Hong Kong HKEX) universally employ multilateral call auctions at the close to discover a single, manipulation-resistant clearing price.

---

## 2. Closing Auction Session (CAS) Architecture & Timeline

Under the standardized CAS framework, the end-of-day market schedule is structured into sequential micro-phases:

| Session Window (IST) | Market Phase | Segment | Allowed Order Actions & System Dynamics |
| :--- | :--- | :--- | :--- |
| **09:15 – 15:15** | Continuous Trading | Cash & Derivatives | Standard continuous order matching (Price-Time priority). Regular algorithmic trading. |
| **15:00** | **Algorithmic Entry Cutoff** | Bot Rule | **Strict cutoff:** All automated new intraday entry signals cease. Bot enters exit-management-only mode. |
| **15:10 – 15:14** | **Pre-CAS Intraday Square-Off** | Cash (Bot 1) | Bot executes automated square-offs for all intraday cash positions before spot continuous halt. |
| **15:15** | **Continuous Spot Close** | Cash Segment | Normal continuous order matching halts for equity underlying shares. |
| **15:15 – 15:25** | **CAS: Order Accumulation** | Cash Segment | Orders entered, modified, or canceled. No matching occurs. Indicative equilibrium price and volume broadcasted in real time. Random closure between 15:24–15:25. |
| **15:25 – 15:30** | **CAS: Order Matching** | Cash Segment | Single equilibrium price discovery based on maximum executable volume. All matched orders execute at this uniform price. |
| **15:30 – 15:35** | **CAS: Buffer / Post-Auction** | Cash Segment | Reconciliation of trade confirmations and dissemination of official closing prices. |
| **15:15 – 15:40** | **Extended F&O Window** | Derivatives (Bot 2) | **Derivatives trading remains active until 15:40 IST.** Allows market makers and arbitrage desks to adjust delta, hedge basis, and square off derivative contracts against the discovered CAS price. |
| **15:35 – 15:38** | **F&O EOD Auto Square-Off** | Derivatives (Bot 2) | Bot squares off intraday option scalps and futures positions before the 15:40 IST derivatives market halt. |

---

## 3. Equilibrium Price Discovery Mechanism in CAS

During the 15:15 – 15:25 order accumulation window, orders are aggregated into cumulative demand and supply schedules. The discovered equilibrium price is established by evaluating three strict criteria in order of priority:
1. **Maximum Executable Volume:** Price that clears the highest volume of combined buy and sell orders.
2. **Minimum Unmatched Volume (Surplus/Imbalance):** Minimizing unmatched order imbalance.
3. **Proximity to Pre-Close Reference Price:** Closest to the last continuous traded price at 15:15.

---

## 4. Quantitative Implications for Bot 1 & Bot 2

### A. Intraday Liquidity Cliff & Order Slippage
Continuous market liquidity drops precipitously between 15:05 and 15:15 as market makers withdraw continuous quotes to prepare for the auction. `intraday_scan_end` is shifted to **15:00 IST**. No new orders are permitted in the final 15 minutes of continuous trading. Intraday auto square-off is strictly enforced at **15:10 IST**.

### B. Cash vs. Synthetic Basis Arbitrage in the 15:30–15:40 Window
The cash market closing price is locked at 15:30 IST, but stock and index futures and options continue trading until 15:40 IST. If the CAS equilibrium price for a stock clears higher/lower than continuous close, options immediately reprice during 15:30–15:40. The bot's risk monitor tracks this basis to avoid adverse option exits.

### C. Pin Risk & Option Gamma near Expiry
Holding OTM/ATM options between 15:15 and 15:35 exposes capital to extreme gamma swings based on the single-tick CAS auction result. Bot 2 enforces option scalp exits prior to 15:14 IST or during the controlled 15:30–15:35 post-auction window, avoiding overnight physical delivery assignment obligations for in-the-money stock options.

---

## 5. Summary of Implemented Code Upgrades

1. **`config/settings.yaml` (Bot 1 & Bot 2):**
   - Added dedicated `cas_session` configuration block.
   - Updated `intraday_scan_end` to `15:00 IST`.
   - Updated `eod_squareoff_time` / `eod_squareoff_cash_ist` to `15:10 IST`.
   - Configured `eod_squareoff_fo_ist` to `15:35 IST`.
2. **GitHub Actions (`eod_squareoff.yml`):**
   - Scheduled dual cron triggers: `09:40 UTC` (15:10 IST) for cash equity and `10:05 UTC` (15:35 IST) for extended derivatives.
3. **Execution Guardrails (`main.py`):**
   - Enforced pre-CAS warning and exit-only mode when `now_ist >= 15:00`.
