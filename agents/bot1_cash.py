import math
import logging
from datetime import datetime
from typing import Dict, Any, List, Union, Optional
import pandas as pd

from core.data_sources import (
    yfinanceWrapper, calculate_rsi, calculate_atr, calculate_adx,
    calculate_vwap, calculate_supertrend
)
from core.schemas import Bot1Signal

logger = logging.getLogger(__name__)

class Bot1EquityAgent:
    """
    Bot 1: Equity Intraday Cash Strategy Execution Engine.
    Generates intraday signals for liquid NIFTY50 cash stocks using multi-indicator scoring
    and 1x cash margin sizing based on available capital pool.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.equity_cfg = config.get("bot1_equity", {})
        self.universe = self.equity_cfg.get("universe", [
            {"symbol": "RELIANCE", "ticker": "RELIANCE.NS", "sector": "ENERGY"},
            {"symbol": "HDFCBANK", "ticker": "HDFCBANK.NS", "sector": "BANK"},
            {"symbol": "ICICIBANK", "ticker": "ICICIBANK.NS", "sector": "BANK"},
            {"symbol": "INFY", "ticker": "INFY.NS", "sector": "IT"},
            {"symbol": "TCS", "ticker": "TCS.NS", "sector": "IT"},
            {"symbol": "BHARTIARTL", "ticker": "BHARTIARTL.NS", "sector": "TELECOM"},
            {"symbol": "MARUTI", "ticker": "MARUTI.NS", "sector": "AUTO"},
            {"symbol": "LT", "ticker": "LT.NS", "sector": "INFRA"},
            {"symbol": "AXISBANK", "ticker": "AXISBANK.NS", "sector": "BANK"},
            {"symbol": "SBIN", "ticker": "SBIN.NS", "sector": "BANK"},
        ])
        self.margin_mult = float(self.equity_cfg.get("cash_margin_multiplier", 1.0))
        self.max_alloc_pct = float(self.equity_cfg.get("max_allocation_per_trade_pct", 15.0)) / 100.0
        self.threshold = float(self.equity_cfg.get("execution_score_threshold", 7.0))

    def run_symbol(self, stock_info: Dict[str, str], timeframe: str, state: Dict[str, Any]) -> Bot1Signal:
        ticker = stock_info["ticker"]
        symbol = stock_info["symbol"]

        df = yfinanceWrapper.fetch_ohlcv(ticker, timeframe=timeframe, period="1d")
        if df.empty or len(df) < 5:
            df = yfinanceWrapper.fetch_ohlcv(ticker, timeframe="15m", period="5d")

        if df.empty or len(df) < 5:
            return Bot1Signal(
                ticker=ticker, symbol=symbol, side="AVOID", spot_cmp=0.0,
                signal_score=0.0, timeframe=timeframe, suggested_entry=0.0,
                suggested_sl=0.0, suggested_target=0.0, quantity=0,
                position_value_inr=0.0, reasoning="Insufficient price data fetched."
            )

        cmp = float(df['Close'].iloc[-1])
        close_prices = df['Close']
        
        # Technical indicators calculation
        ema9 = float(close_prices.ewm(span=9, adjust=False).mean().iloc[-1])
        ema21 = float(close_prices.ewm(span=21, adjust=False).mean().iloc[-1])
        period_len = min(14, max(2, len(df) - 1))
        rsi = float(calculate_rsi(close_prices, period=period_len).iloc[-1])
        adx = float(calculate_adx(df, period=period_len).iloc[-1])
        atr = float(calculate_atr(df, period=period_len).iloc[-1])
        vwap = float(calculate_vwap(df).iloc[-1])
        st_series, st_dir = calculate_supertrend(df, period=min(7, len(df)), multiplier=3.0)
        supertrend_dir = int(st_dir.iloc[-1])

        # Multi-factor technical score calculation (0.0 to 10.0)
        score = 5.0

        # 1. Supertrend & EMA Trend alignment (+/- 1.5)
        if supertrend_dir == 1:
            score += 1.0
        else:
            score -= 1.0

        if ema9 > ema21:
            score += 0.5
        else:
            score -= 0.5

        # 2. VWAP positioning (+/- 0.8)
        if cmp > vwap:
            score += 0.8
        else:
            score -= 0.8

        # 3. Momentum (RSI + ADX) (+/- 1.5)
        if 50.0 <= rsi <= 68.0:
            score += 0.7
        elif rsi > 70.0:
            score -= 0.3
        elif 32.0 <= rsi < 50.0:
            score -= 0.7
        elif rsi < 30.0:
            score += 0.3

        if adx > 20.0:
            score += 0.5 if score >= 5.0 else -0.5

        score = max(0.0, min(10.0, score))

        # Determine trade side based on score threshold
        if score >= self.threshold:
            side = "BUY"
        elif score <= (10.0 - self.threshold):
            side = "SELL"
        else:
            side = "AVOID"

        if side == "AVOID":
            return Bot1Signal(
                ticker=ticker, symbol=symbol, side="AVOID", spot_cmp=round(cmp, 2),
                signal_score=round(score, 2), timeframe=timeframe, suggested_entry=round(cmp, 2),
                suggested_sl=0.0, suggested_target=0.0, quantity=0,
                position_value_inr=0.0, reasoning=f"Signal score {score:.2f} did not reach execution threshold {self.threshold}."
            )

        # 1x Cash Margin Sizing Logic
        pool_avail = float(state.get("pool_available", 500000.0))
        pool_total = float(state.get("pool_total", 500000.0))

        max_trade_cap = min(pool_avail, pool_total * self.max_alloc_pct)
        effective_capital = max_trade_cap * self.margin_mult  # 1x cash margin

        quantity = math.floor(effective_capital / cmp) if cmp > 0 else 0
        if quantity < 1:
            return Bot1Signal(
                ticker=ticker, symbol=symbol, side="AVOID", spot_cmp=round(cmp, 2),
                signal_score=round(score, 2), timeframe=timeframe, suggested_entry=round(cmp, 2),
                suggested_sl=0.0, suggested_target=0.0, quantity=0,
                position_value_inr=0.0, reasoning=f"Insufficient pool (₹{pool_avail:.2f}) to buy 1 share @ ₹{cmp:.2f}."
            )

        position_val = round(quantity * cmp, 2)
        atr_sl_mult = float(self.equity_cfg.get("atr_sl_multiplier", 2.0))
        atr_tgt_mult = float(self.equity_cfg.get("atr_target_multiplier", 3.0))
        stop_dist = max(atr * atr_sl_mult, cmp * 0.01)

        if side == "BUY":
            sl = round(cmp - stop_dist, 2)
            target = round(cmp + (stop_dist * (atr_tgt_mult / atr_sl_mult)), 2)
        else:
            sl = round(cmp + stop_dist, 2)
            target = round(cmp - (stop_dist * (atr_tgt_mult / atr_sl_mult)), 2)

        return Bot1Signal(
            ticker=ticker,
            symbol=symbol,
            side=side,
            spot_cmp=round(cmp, 2),
            signal_score=round(score, 2),
            timeframe=timeframe,
            suggested_entry=round(cmp, 2),
            suggested_sl=sl,
            suggested_target=target,
            quantity=quantity,
            position_value_inr=position_val,
            estimated_brokerage_inr=20.0,
            reasoning=f"Approved {side} signal for {symbol} cash stock. Score: {score:.2f}/10. Qty: {quantity} @ ₹{cmp:.2f} (1x Cash Margin Val: ₹{position_val:.2f})."
        )

    def run(self, arg1: Any, timeframe: str = "5m", state: Optional[Dict[str, Any]] = None) -> Union[List[Bot1Signal], Optional[Bot1Signal]]:
        """
        Supports two invocation patterns:
        1. agent.run(state, timeframe="5m") -> List[Bot1Signal]  (Universe scan)
        2. agent.run(ticker, timeframe="5m", state=state_dict) -> Optional[Bot1Signal] (Single ticker scan)
        """
        if isinstance(arg1, str):
            # Single ticker mode
            ticker = arg1
            effective_state = state or {}
            symbol = ticker.replace(".NS", "").replace("^", "")
            stock_info = next((s for s in self.universe if s["ticker"] == ticker), {"symbol": symbol, "ticker": ticker})
            sig = self.run_symbol(stock_info, timeframe=timeframe, state=effective_state)
            return sig if sig.side != "AVOID" else None
        else:
            # Universe scan mode (arg1 is state)
            effective_state = arg1 if isinstance(arg1, dict) else {}
            logger.info(f"--- Running Bot 1 (Equity Intraday Cash Engine) Scan ({timeframe}) ---")
            signals = []
            for stock_info in self.universe:
                sig = self.run_symbol(stock_info, timeframe=timeframe, state=effective_state)
                if sig.side != "AVOID":
                    signals.append(sig)
            logger.info(f"[Bot 1 Equity Agent] Found {len(signals)} actionable cash signals on {timeframe} timeframe.")
            return signals
