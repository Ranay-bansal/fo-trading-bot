import json
import os
import csv
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(ROOT_DIR, "state", "portfolio_state.json")
TRADE_LOG_FILE = os.path.join(ROOT_DIR, "state", "trade_log.csv")

DEFAULT_STATE = {
    "last_updated": None,
    "pool_total": 500000.0,
    "pool_available": 500000.0,
    "pool_deployed": 0.0,
    "daily_pnl_inr": 0.0,
    "daily_pnl_pct": 0.0,
    "total_brokerage_paid_inr": 0.0,
    "trades_today": 0,
    "open_positions": []
}

def load_fo_state() -> Dict[str, Any]:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading F&O state: {e}")
    return DEFAULT_STATE.copy()

def save_fo_state(state: Dict[str, Any]) -> None:
    state["last_updated"] = datetime.utcnow().isoformat() + "Z"
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def append_to_fo_trade_log(row: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(TRADE_LOG_FILE), exist_ok=True)
    file_exists = os.path.exists(TRADE_LOG_FILE)
    fieldnames = [
        "run_id", "ticker", "symbol", "verdict", "contract_type", "strike_price",
        "lots", "total_shares", "spot_entry", "option_premium", "spot_sl", "spot_target",
        "waterfall_score", "position_value_inr", "brokerage_fee_inr", "total_cost_inr",
        "executed_at", "exit_price", "exit_reason", "realized_pnl_inr", "realized_pnl_pct"
    ]
    with open(TRADE_LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in fieldnames})
