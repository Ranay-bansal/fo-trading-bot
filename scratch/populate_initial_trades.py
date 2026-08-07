import os
import csv
import json
from datetime import datetime

ROOT_DIR = r"c:\Users\RANAY\Desktop\FO TRADING BOT"
TRADE_LOG = os.path.join(ROOT_DIR, "state", "trade_log.csv")
STATE_FILE = os.path.join(ROOT_DIR, "state", "portfolio_state.json")

sample_trades = [
    {
        "run_id": "NIFTY_BUY_CE_20260807_093000",
        "ticker": "^NSEI",
        "symbol": "NIFTY",
        "verdict": "BUY_CE",
        "contract_type": "OPTION_CE",
        "strike_price": 24200,
        "lots": 2,
        "total_shares": 50,
        "spot_entry": 24210.50,
        "option_premium": 145.20,
        "spot_sl": 23847.34,
        "spot_target": 24755.24,
        "waterfall_score": 8.85,
        "position_value_inr": 7260.00,
        "brokerage_fee_inr": 20.00,
        "total_cost_inr": 24.54,
        "executed_at": "2026-08-07T09:30:00Z",
        "exit_price": 178.50,
        "exit_reason": "target_hit",
        "realized_pnl_inr": 1665.00,
        "realized_pnl_pct": 22.93
    },
    {
        "run_id": "BANKNIFTY_BUY_PE_20260807_101500",
        "ticker": "^NSEBANK",
        "symbol": "BANKNIFTY",
        "verdict": "BUY_PE",
        "contract_type": "OPTION_PE",
        "strike_price": 52000,
        "lots": 2,
        "total_shares": 30,
        "spot_entry": 51950.00,
        "option_premium": 280.00,
        "spot_sl": 52729.25,
        "spot_target": 50781.12,
        "waterfall_score": 8.40,
        "position_value_inr": 8400.00,
        "brokerage_fee_inr": 20.00,
        "total_cost_inr": 25.25,
        "executed_at": "2026-08-07T10:15:00Z",
        "exit_price": 342.00,
        "exit_reason": "target_hit",
        "realized_pnl_inr": 1860.00,
        "realized_pnl_pct": 22.14
    },
    {
        "run_id": "RELIANCE_BUY_CE_20260807_110000",
        "ticker": "RELIANCE.NS",
        "symbol": "RELIANCE",
        "verdict": "BUY_CE",
        "contract_type": "OPTION_CE",
        "strike_price": 2000,
        "lots": 1,
        "total_shares": 250,
        "spot_entry": 2005.00,
        "option_premium": 42.00,
        "spot_sl": 1974.92,
        "spot_target": 2050.12,
        "waterfall_score": 8.10,
        "position_value_inr": 10500.00,
        "brokerage_fee_inr": 20.00,
        "total_cost_inr": 26.56,
        "executed_at": "2026-08-07T11:00:00Z",
        "exit_price": 35.50,
        "exit_reason": "sl_hit",
        "realized_pnl_inr": -1625.00,
        "realized_pnl_pct": -15.48
    },
    {
        "run_id": "DLF_BUY_PE_20260807_114500",
        "ticker": "DLF.NS",
        "symbol": "DLF",
        "verdict": "BUY_PE",
        "contract_type": "OPTION_PE",
        "strike_price": 650,
        "lots": 1,
        "total_shares": 825,
        "spot_entry": 648.50,
        "option_premium": 18.50,
        "spot_sl": 658.23,
        "spot_target": 633.90,
        "waterfall_score": 8.65,
        "position_value_inr": 15262.50,
        "brokerage_fee_inr": 20.00,
        "total_cost_inr": 29.54,
        "executed_at": "2026-08-07T11:45:00Z",
        "exit_price": 24.80,
        "exit_reason": "target_hit",
        "realized_pnl_inr": 5197.50,
        "realized_pnl_pct": 34.05
    }
]

os.makedirs(os.path.dirname(TRADE_LOG), exist_ok=True)
fieldnames = list(sample_trades[0].keys())
with open(TRADE_LOG, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in sample_trades:
        writer.writerow(row)

# Update State File
tot_pnl = sum(r["realized_pnl_inr"] for r in sample_trades)
tot_brokerage = len(sample_trades) * 20.0

state = {
    "last_updated": datetime.utcnow().isoformat() + "Z",
    "pool_total": 500000.0,
    "pool_available": 500000.0 + tot_pnl - tot_brokerage,
    "pool_deployed": 0.0,
    "daily_pnl_inr": tot_pnl,
    "daily_pnl_pct": round((tot_pnl / 500000.0) * 100.0, 2),
    "total_brokerage_paid_inr": tot_brokerage,
    "trades_today": len(sample_trades),
    "open_positions": []
}

with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump(state, f, indent=2)

print(f"Sample trades populated. Total Net PnL: INR {tot_pnl}, Total Brokerage: INR {tot_brokerage}")
