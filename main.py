import os
import yaml
import logging
from datetime import datetime, timezone, timedelta
from core.state import load_fo_state, save_fo_state
from core.data_sources import yfinanceWrapper
from agents.scout import FOScoutAgent
from agents.technician import FOTechnicianAgent
from agents.judge import FOJudgeAgent
from agents.executor import FOExecutorAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("FOOrchestrator")

def load_config():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(root_dir, "config", "settings.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_fo_pipeline():
    logger.info("=== STARTING ALPHA DESK F&O QUANT PIPELINE RUN ===")
    config = load_config()
    state = load_fo_state()

    # Time cutoff check (1:30 PM IST)
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(ist_tz)
    
    executor = FOExecutorAgent(config)
    executor.monitor_positions(state)

    if now_ist.hour > 13 or (now_ist.hour == 13 and now_ist.minute >= 30):
        logger.warning("F&O scan triggered after 1:30 PM IST entry cutoff. No new entries allowed.")
        save_fo_state(state)
        return

    scout = FOScoutAgent(config)
    technician = FOTechnicianAgent(config)
    judge = FOJudgeAgent(config)

    vix_val = yfinanceWrapper.fetch_vix()
    logger.info(f"India VIX: {vix_val:.2f}")

    candidates = scout.run()
    for cand in candidates:
        logger.info(f"[F&O Pipeline] Evaluating {cand.symbol} Spot @ ₹{cand.spot_cmp}...")
        tech_out = technician.run(cand, vix_val=vix_val)
        judge_out = judge.run(cand, tech_out, state)

        logger.info(f"[F&O Verdict] {cand.symbol}: {judge_out.verdict} (Waterfall Score: {judge_out.waterfall_score}/10)")

        if judge_out.verdict in ["BUY_CE", "BUY_PE"]:
            executor.execute(judge_out, state)

    save_fo_state(state)
    logger.info("=== F&O QUANT PIPELINE RUN COMPLETED ===")

if __name__ == "__main__":
    run_fo_pipeline()
