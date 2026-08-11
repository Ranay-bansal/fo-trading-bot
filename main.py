import os
import yaml
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from core.state import load_fo_state, save_fo_state
from core.data_sources import yfinanceWrapper, StreamingTickSimulator, BarEvent
from agents.bot1_cash import Bot1EquityAgent
from agents.bot2_options import Bot2OptionSwarmAgent
from agents.scout import FOScoutAgent
from agents.technician import FOTechnicianAgent
from agents.judge import FOJudgeAgent
from agents.executor import FOExecutorAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("QuantOrchestrator")

state_lock = threading.Lock()

def load_config() -> Dict[str, Any]:
    root_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(root_dir, "config", "settings.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_quant_pipeline() -> None:
    """
    Standard quantitative trading pipeline pass running Bot 1 (Equity Cash)
    and Bot 2 (F&O Swarm) across multi-timeframe cycles.
    """
    logger.info("=== STARTING SHADOW TRADERS QUANT PIPELINE (BOT 1 CASH & BOT 2 F&O SWARM) ===")
    config = load_config()
    state = load_fo_state()

    ist_tz = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(ist_tz)
    
    executor = FOExecutorAgent(config)
    executor.monitor_positions(state)

    if now_ist.weekday() < 5 and (now_ist.hour > 13 or (now_ist.hour == 13 and now_ist.minute >= 30)):
        logger.warning("Scan triggered after 1:30 PM IST entry cutoff (Running paper mode simulation).")

    timeframes = ["5m", "1m", "15m"]

    # --- BOT 1: EQUITY INTRADAY CASH STRATEGY EXECUTION ENGINE ---
    if config.get("bot1_equity", {}).get("enabled", True):
        logger.info("--- [BOT 1] Executing Equity Intraday Cash Strategy Engine ---")
        bot1_agent = Bot1EquityAgent(config)
        for tf in timeframes:
            cash_signals = bot1_agent.run(state, timeframe=tf)
            if isinstance(cash_signals, list):
                for sig in cash_signals:
                    if sig and sig.side != "AVOID":
                        logger.info(f"[Bot 1 Cash Triggered] {sig.symbol} ({tf}): {sig.side} (Score: {sig.signal_score}/10, Qty: {sig.quantity})")
                        executor.execute_cash(sig, state)

    # --- BOT 2: F&O OPTIONS SWARM STRATEGY EXECUTION ENGINE ---
    logger.info("--- [BOT 2] Executing F&O Options Swarm Engine ---")
    scout = FOScoutAgent(config)
    technician = FOTechnicianAgent(config)
    judge = FOJudgeAgent(config)

    vix_val = yfinanceWrapper.fetch_vix()
    logger.info(f"India VIX: {vix_val:.2f}")

    for tf in timeframes:
        logger.info(f"--- Running F&O Scan Cycle on {tf} timeframe ---")
        candidates = scout.run(timeframe=tf)
        for cand in candidates:
            tech_out = technician.run(cand, timeframe=tf, vix_val=vix_val)
            judge_out = judge.run(cand, tech_out, state, timeframe=tf)

            if judge_out and judge_out.verdict != "AVOID":
                logger.info(f"[Bot 2 F&O Triggered] {cand.symbol} ({tf}): Verdict = {judge_out.verdict} (Score: {judge_out.waterfall_score}/10)")
                executor.execute(judge_out, state)

    save_fo_state(state)
    logger.info("=== QUANT PIPELINE COMPLETED SUCCESSFULLY ===")

def run_continuous_stream(simulate_live: bool = False, delay_seconds: float = 0.0) -> None:
    """
    Continuous Zero-Latency Bar-by-Bar Parallel Stream Execution Loop.
    Executes Bot 1 (Equity Cash) and Bot 2 (F&O Swarm) concurrently.
    """
    logger.info("=== STARTING ZERO-LATENCY PARALLEL STREAM EXECUTION ENGINE ===")
    config = load_config()
    state = load_fo_state()

    bot1_agent = Bot1EquityAgent(config)
    bot2_agent = Bot2OptionSwarmAgent(config)
    executor = FOExecutorAgent(config)

    # Collect universe tickers
    fo_indices = [item["ticker"] for item in config.get("fo_universe", {}).get("indices", [])]
    fo_stocks = [item["ticker"] for item in config.get("fo_universe", {}).get("stocks", [])]
    cash_universe = config.get("bot1_equity", {}).get("universe", [])
    cash_stocks = [item["ticker"] for item in cash_universe] if cash_universe else ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "TCS.NS"]

    all_tickers = list(set(fo_indices + fo_stocks + cash_stocks))
    
    simulator = StreamingTickSimulator(
        tickers=all_tickers,
        timeframes=["5m"],
        period="1d",
        simulate_live=simulate_live,
        delay_seconds=delay_seconds
    )

    logger.info(f"Preloading streaming data for {len(all_tickers)} tickers...")
    simulator.preload()

    vix_val = yfinanceWrapper.fetch_vix()
    logger.info(f"Initial India VIX: {vix_val:.2f}")

    with ThreadPoolExecutor(max_workers=2) as thread_pool:
        for bar_evt in simulator.stream_bars(timeframe="5m"):
            logger.info(f"[Bar Stream] {bar_evt.ticker} @ {bar_evt.timestamp} | Close={bar_evt.close}")

            # 1. Continuous Position Monitoring (SL/TP check)
            with state_lock:
                executor.monitor_positions(state, bar_evt)

            # 2. Parallel Strategy Execution (Bot 1 and Bot 2)
            futures = {}

            # Submit Bot 1 (Equity Cash) task if ticker in cash universe
            if bar_evt.ticker in cash_stocks:
                futures[thread_pool.submit(bot1_agent.run, bar_evt.ticker, "5m", state.copy())] = "Bot1"

            # Submit Bot 2 (F&O Options Swarm) task if ticker in F&O universe
            if bar_evt.ticker in (fo_indices + fo_stocks):
                futures[thread_pool.submit(bot2_agent.run, bar_evt.ticker, "5m", state.copy(), vix_val, bar_evt)] = "Bot2"

            # 3. Gather Signals & Execute under Lock
            for fut in as_completed(futures):
                bot_name = futures[fut]
                try:
                    res = fut.result()
                    if res:
                        with state_lock:
                            if bot_name == "Bot1" and hasattr(res, "side") and res.side != "AVOID":
                                logger.info(f"[Bot1 Cash Signal] Executing {res.side} for {res.symbol}")
                                executor.execute_cash(res, state)
                            elif bot_name == "Bot2" and hasattr(res, "verdict") and res.verdict not in ["AVOID", "REJECT", "WATCHLIST"]:
                                logger.info(f"[Bot2 F&O Signal] Executing {res.verdict} for {res.ticker}")
                                executor.execute(res, state)
                except Exception as e:
                    logger.error(f"[{bot_name} Thread Error]: {e}")

            # 4. Save state
            with state_lock:
                save_fo_state(state)

    logger.info("=== ZERO-LATENCY PARALLEL STREAM EXECUTION COMPLETED ===")

def run_fo_pipeline() -> None:
    """Backward compatibility alias for F&O pipeline runner."""
    run_quant_pipeline()

if __name__ == "__main__":
    run_quant_pipeline()
