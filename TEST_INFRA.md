# E2E Test Infra: Shadow Traders Quant Trading Platform

## Test Philosophy
- Opaque-box, requirement-driven. No dependency on implementation design.
- Methodology: Category-Partition + BVA + Pairwise + Workload Testing.

## Feature Inventory
| # | Feature | Source (requirement) | Tier 1 | Tier 2 | Tier 3 |
|---|---------|---------------------|:------:|:------:|:------:|
| 1 | Bot 1 Equity Cash Engine & Paper Execution | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 2 | Bot 2 F&O Options Swarm Engine & Paper Execution | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 3 | 3-Way Risk Committee Debaters | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 4 | Zero-Latency Bar-by-Bar Signal & Execution | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 5 | Glassmorphism Dashboard UI & State Hydration | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 6 | PWA Offline Installation Compliance | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 7 | Vercel Static Deployment Compliance | ORIGINAL_REQUEST §AC3 | 5 | 5 | ✓ |

## Test Architecture
- Test runner: `unittest` test suite in `tests/`
- Command: `python -m unittest discover -s tests -p "test_*.py"`
- Pass/Fail semantics: All assertions must pass cleanly, exit code 0.

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Full Intraday Scan & Trade Execution Cycle (Bot 1 + Bot 2 + 3-Way Debaters) | F1, F2, F3, F4 | High |
| 2 | Dynamic State Hydration & Zero Undefined Variable Errors on UI Dashboard | F5, F7 | Medium |
| 3 | PWA Service Worker Registration & Offline Caching Validation | F6 | Medium |
| 4 | Continuous Position SL/TP Exit Monitoring & State Ledger Verification | F1, F2, F4 | High |
| 5 | End-to-End Paper Trade & Committee Debate Log Generation to UI Render | F1, F2, F3, F5 | High |

## Coverage Thresholds
- Tier 1: ≥5 per feature (35 test cases)
- Tier 2: ≥5 per feature (35 test cases)
- Tier 3: Pairwise combinations (10 test cases)
- Tier 4: ≥5 realistic application scenarios (5 test cases)
- **Total E2E Target: ≥85 test cases**
