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
COMMITTEE_DEBATE_LOG_FILE = os.path.join(ROOT_DIR, "state", "committee_debate_log.json")

DASH_STATE_DIR = os.path.join(ROOT_DIR, "dashboard", "state")
DASH_STATE_FILE = os.path.join(DASH_STATE_DIR, "portfolio_state.json")
DASH_TRADE_LOG_FILE = os.path.join(DASH_STATE_DIR, "trade_log.csv")
DASH_DEBATE_LOG_FILE = os.path.join(DASH_STATE_DIR, "committee_debate_log.json")

REFLECTIVE_MEMORY_FILE = os.path.join(ROOT_DIR, "state", "reflective_memory.json")
DASH_MEMORY_FILE = os.path.join(DASH_STATE_DIR, "reflective_memory.json")
PUB_STATE_DIR = os.path.join(ROOT_DIR, "public", "state")
PUB_MEMORY_FILE = os.path.join(PUB_STATE_DIR, "reflective_memory.json")

DEFAULT_STATE = {
    "last_updated": None,
    "pool_total": 500000.0,
    "pool_available": 500000.0,
    "pool_deployed": 0.0,
    "daily_pnl_inr": 0.0,
    "daily_pnl_pct": 0.0,
    "total_brokerage_paid_inr": 0.0,
    "trades_today": 0,
    "open_positions": [],
    "kill_switch_active": False,
    "kill_switch_reason": None
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
    try:
        state["last_updated"] = datetime.utcnow().isoformat() + "Z"
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        temp_file = STATE_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)
        try:
            os.replace(temp_file, STATE_FILE)
        except (PermissionError, OSError):
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, default=str)
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

        # Mirror state to dashboard/state for zero-friction Vercel hosting
        try:
            os.makedirs(DASH_STATE_DIR, exist_ok=True)
            with open(DASH_STATE_FILE, "w", encoding="utf-8") as df:
                json.dump(state, df, indent=2, default=str)
        except Exception as dash_err:
            logger.warning(f"Error mirroring state to dashboard: {dash_err}")

    except Exception as e:
        logger.error(f"Error saving F&O state to {STATE_FILE}: {e}")

def append_to_fo_trade_log(row: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(TRADE_LOG_FILE), exist_ok=True)
        file_has_content = os.path.exists(TRADE_LOG_FILE) and os.path.getsize(TRADE_LOG_FILE) > 0
        fieldnames = [
            "run_id", "ticker", "symbol", "verdict", "contract_type", "strike_price",
            "lots", "total_shares", "spot_entry", "option_premium", "spot_sl", "spot_target",
            "waterfall_score", "position_value_inr", "brokerage_fee_inr", "total_cost_inr",
            "executed_at", "exit_price", "exit_reason", "realized_pnl_inr", "realized_pnl_pct"
        ]
        with open(TRADE_LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_has_content:
                writer.writeheader()
            writer.writerow({k: row.get(k, "") for k in fieldnames})

        # Mirror trade log to dashboard/state
        try:
            os.makedirs(DASH_STATE_DIR, exist_ok=True)
            dash_has_content = os.path.exists(DASH_TRADE_LOG_FILE) and os.path.getsize(DASH_TRADE_LOG_FILE) > 0
            with open(DASH_TRADE_LOG_FILE, "a", newline="", encoding="utf-8") as df:
                dash_writer = csv.DictWriter(df, fieldnames=fieldnames)
                if not dash_has_content:
                    dash_writer.writeheader()
                dash_writer.writerow({k: row.get(k, "") for k in fieldnames})
        except Exception as dash_csv_err:
            logger.warning(f"Error mirroring trade log to dashboard: {dash_csv_err}")
    except Exception as e:
        logger.error(f"Error appending trade log to {TRADE_LOG_FILE}: {e}")

def append_to_committee_debate_log(record: Any) -> None:
    try:
        os.makedirs(os.path.dirname(COMMITTEE_DEBATE_LOG_FILE), exist_ok=True)
        if hasattr(record, "model_dump"):
            rec_dict = record.model_dump()
        elif hasattr(record, "dict"):
            rec_dict = record.dict()
        elif isinstance(record, dict):
            rec_dict = record.copy()
        else:
            rec_dict = dict(record)

        if "timestamp" in rec_dict and isinstance(rec_dict["timestamp"], datetime):
            rec_dict["timestamp"] = rec_dict["timestamp"].isoformat() + "Z"

        logs = []
        if os.path.exists(COMMITTEE_DEBATE_LOG_FILE):
            try:
                with open(COMMITTEE_DEBATE_LOG_FILE, "r", encoding="utf-8") as f:
                    logs = json.load(f)
                    if not isinstance(logs, list):
                        logs = []
            except Exception:
                logs = []

        logs.append(rec_dict)
        if len(logs) > 200:
            logs = logs[-200:]

        temp_file = COMMITTEE_DEBATE_LOG_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, default=str)
        try:
            os.replace(temp_file, COMMITTEE_DEBATE_LOG_FILE)
        except (PermissionError, OSError):
            with open(COMMITTEE_DEBATE_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2, default=str)
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"Error appending to committee debate log {COMMITTEE_DEBATE_LOG_FILE}: {e}")


def load_reflective_memory() -> Dict[str, Any]:
    """Loads ticker-level reflective memory log."""
    try:
        if os.path.exists(REFLECTIVE_MEMORY_FILE):
            with open(REFLECTIVE_MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load reflective memory: {e}")
    return {}

def save_reflective_memory(memory: Dict[str, Any]) -> None:
    """Saves ticker-level reflective memory log and mirrors to web folders."""
    try:
        os.makedirs(os.path.dirname(REFLECTIVE_MEMORY_FILE), exist_ok=True)
        with open(REFLECTIVE_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2, default=str)
        
        # Mirror to dashboard/state
        try:
            os.makedirs(DASH_STATE_DIR, exist_ok=True)
            with open(DASH_MEMORY_FILE, "w", encoding="utf-8") as df:
                json.dump(memory, df, indent=2, default=str)
        except Exception:
            pass

        # Mirror to public/state
        try:
            os.makedirs(PUB_STATE_DIR, exist_ok=True)
            with open(PUB_MEMORY_FILE, "w", encoding="utf-8") as pf:
                json.dump(memory, pf, indent=2, default=str)
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Failed to save reflective memory: {e}")

def record_trade_reflection(ticker: str, verdict: str, outcome: str, reflection_text: str, memory_modifier: float = 0.0) -> None:
    """Records a post-trade decision or outcome reflection for a specific ticker."""
    memory = load_reflective_memory()
    ticker_history = memory.get(ticker, {
        "ticker": ticker,
        "symbol": ticker.replace(".NS", "").replace("^", ""),
        "total_evaluations": 0,
        "history": [],
        "last_verdict": None,
        "last_outcome": None,
        "last_reflection": None,
        "memory_modifier": 0.0
    })

    ticker_history["total_evaluations"] += 1
    ticker_history["last_verdict"] = verdict
    ticker_history["last_outcome"] = outcome
    ticker_history["last_reflection"] = reflection_text
    ticker_history["memory_modifier"] = memory_modifier

    ticker_history["history"].append({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "verdict": verdict,
        "outcome": outcome,
        "memory_modifier": memory_modifier,
        "reflection": reflection_text
    })

    ticker_history["history"] = ticker_history["history"][-10:]
    memory[ticker] = ticker_history
    save_reflective_memory(memory)
