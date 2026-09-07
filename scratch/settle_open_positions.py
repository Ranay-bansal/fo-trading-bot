import os
import sys
import json
import logging
import yaml

# Ensure root directory is on pythonpath
root_dir = r"c:\Users\RANAY\Desktop\FO TRADING BOT"
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.state import load_fo_state, save_fo_state
from agents.executor import FOExecutorAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("SettlementScript")

def main():
    config_path = os.path.join(root_dir, "config", "settings.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    state = load_fo_state()
    open_positions = state.get("open_positions", [])
    logger.info(f"Loaded portfolio state. Found {len(open_positions)} open positions.")

    if not open_positions:
        logger.info("No open positions found. Nothing to settle.")
        return

    executor = FOExecutorAgent(config)
    exited_trades = executor.squareoff_all(state)
    logger.info(f"Successfully settled {len(exited_trades)} positions.")
    
    # Reload and verify
    updated_state = load_fo_state()
    logger.info("Updated Portfolio Summary:")
    logger.info(f"  Pool Total: ₹{updated_state.get('pool_total', 0):,.2f}")
    logger.info(f"  Pool Available: ₹{updated_state.get('pool_available', 0):,.2f}")
    logger.info(f"  Pool Deployed: ₹{updated_state.get('pool_deployed', 0):,.2f}")
    logger.info(f"  Open Positions: {len(updated_state.get('open_positions', []))}")
    logger.info(f"  Daily Realized P&L: ₹{updated_state.get('daily_pnl_inr', 0):,.2f} ({updated_state.get('daily_pnl_pct', 0):.2f}%)")

if __name__ == "__main__":
    main()
