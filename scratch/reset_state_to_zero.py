import os
import csv
import json
from datetime import datetime, timezone

ROOT_DIR = r"c:\Users\RANAY\Desktop\FO TRADING BOT"
STATE_FILE = os.path.join(ROOT_DIR, "state", "portfolio_state.json")
TRADE_LOG = os.path.join(ROOT_DIR, "state", "trade_log.csv")

# Reset State
state = {
    "last_updated": datetime.now(timezone.utc).isoformat(),
    "pool_total": 500000.0,
    "pool_available": 500000.0,
    "pool_deployed": 0.0,
    "daily_pnl_inr": 0.0,
    "daily_pnl_pct": 0.0,
    "total_brokerage_paid_inr": 0.0,
    "trades_today": 0,
    "open_positions": []
}

os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump(state, f, indent=2)

# Reset CSV Trade Log to header only
fieldnames = [
    "run_id", "ticker", "symbol", "verdict", "contract_type", "strike_price",
    "lots", "total_shares", "spot_entry", "option_premium", "spot_sl", "spot_target",
    "waterfall_score", "position_value_inr", "brokerage_fee_inr", "total_cost_inr",
    "executed_at", "exit_price", "exit_reason", "realized_pnl_inr", "realized_pnl_pct"
]

with open(TRADE_LOG, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

print("Portfolio State and Trade Log reset to zero successfully.")
