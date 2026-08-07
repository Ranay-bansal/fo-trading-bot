import os
import yaml
import math
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
from typing import Dict, Any, List

from core.options_engine import OptionsEngine
from core.data_sources import calculate_rsi, calculate_atr, calculate_adx, calculate_vwap, calculate_supertrend

def run_fo_backtest():
    print("================================================================")
    print("   ALPHA DESK SHADOW TRADERS — F&O QUANT BACKTEST ENGINE (V2)")
    print("================================================================")

    options_engine = OptionsEngine()
    initial_capital = 500000.0  # ₹5 Lakhs
    available_capital = initial_capital
    deployed_capital = 0.0
    brokerage_fee_per_order = 20.0  # ₹20 flat

    universe = [
        {"ticker": "^NSEI", "symbol": "NIFTY", "lot_size": 25, "step": 50},
        {"ticker": "^NSEBANK", "symbol": "BANKNIFTY", "lot_size": 15, "step": 100},
        {"ticker": "RELIANCE.NS", "symbol": "RELIANCE", "lot_size": 250, "step": 20},
        {"ticker": "TCS.NS", "symbol": "TCS", "lot_size": 175, "step": 20},
        {"ticker": "INFY.NS", "symbol": "INFY", "lot_size": 400, "step": 10},
        {"ticker": "ICICIBANK.NS", "symbol": "ICICIBANK", "lot_size": 700, "step": 10},
        {"ticker": "HDFCBANK.NS", "symbol": "HDFCBANK", "lot_size": 550, "step": 10},
        {"ticker": "DLF.NS", "symbol": "DLF", "lot_size": 825, "step": 10},
        {"ticker": "TATASTEEL.NS", "symbol": "TATASTEEL", "lot_size": 5500, "step": 2},
        {"ticker": "SBIN.NS", "symbol": "SBIN", "lot_size": 750, "step": 5}
    ]

    trades_log = []

    for item in universe:
        ticker = item["ticker"]
        symbol = item["symbol"]
        lot_size = item["lot_size"]
        step = item["step"]

        print(f"[Backtest Engine] Fetching 15m historical data for {symbol}...")
        df = yf.download(ticker, period="1mo", interval="15m", progress=False)
        if df.empty or len(df) < 30:
            continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]

        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
        close = df['Close']
        high = df['High']
        low = df['Low']

        # Indicators
        ema9 = close.ewm(span=9, adjust=False).mean()
        ema21 = close.ewm(span=21, adjust=False).mean()
        rsi = calculate_rsi(close)
        atr = calculate_atr(df)
        adx = calculate_adx(df)
        vwap = calculate_vwap(df)
        st_series, st_dir = calculate_supertrend(df, period=7, multiplier=3.0)

        in_position = False
        pos_details = {}
        last_trade_date = None

        for i in range(25, len(df) - 1):
            curr_date = df.index[i].date()
            cmp = float(close.iloc[i])
            curr_st = int(st_dir.iloc[i])
            curr_vwap = float(vwap.iloc[i])
            curr_atr = float(atr.iloc[i])
            curr_rsi = float(rsi.iloc[i])

            # Max 1 trade per symbol per session
            if last_trade_date == curr_date:
                continue

            # Entry condition with strict 8.0 Waterfall Score threshold
            if not in_position:
                score = 5.0
                if curr_st == 1: score += 1.2
                else: score -= 1.2

                if cmp > curr_vwap: score += 1.0
                else: score -= 1.0

                if ema9.iloc[i] > ema21.iloc[i]: score += 1.0
                else: score -= 1.0

                if 45 <= curr_rsi <= 65: score += 0.8
                if adx.iloc[i] >= 22: score += 0.5

                verdict = "AVOID"
                if score >= 8.0:
                    verdict = "BUY_CE"
                elif score <= 2.0:
                    verdict = "BUY_PE"

                if verdict in ["BUY_CE", "BUY_PE"]:
                    option_type = "CE" if verdict == "BUY_CE" else "PE"
                    strike = options_engine.select_strike(cmp, step, stance="bullish" if option_type == "CE" else "bearish", itm_depth=1)
                    bs_res = options_engine.calculate_bs_price_and_greeks(cmp, strike, dte=7, iv_pct=14.5, option_type=option_type)
                    premium = bs_res["price"]

                    cost_per_lot = premium * lot_size
                    max_alloc = min(available_capital * 0.15, 75000.0)
                    lots = max(1, math.floor(max_alloc / cost_per_lot)) if cost_per_lot > 0 else 1
                    total_shares = lots * lot_size
                    pos_val = premium * total_shares

                    # Cost Viability Gate
                    entry_costs = options_engine.calculate_trade_costs(pos_val, is_sell=False, contract_type="OPTION")
                    round_trip_cost = (brokerage_fee_per_order * 2.0) + entry_costs["total_cost"]
                    expected_gain = pos_val * 0.15

                    if expected_gain < (round_trip_cost * 2.0):
                        continue  # Skip low-margin trade

                    in_position = True
                    last_trade_date = curr_date
                    pos_details = {
                        "symbol": symbol,
                        "verdict": verdict,
                        "option_type": option_type,
                        "strike": strike,
                        "lots": lots,
                        "total_shares": total_shares,
                        "entry_spot": cmp,
                        "entry_premium": premium,
                        "delta": bs_res["delta"],
                        "entry_idx": i,
                        "entry_time": df.index[i],
                        "entry_brokerage": entry_costs["brokerage"]
                    }

            # Exit Condition
            elif in_position:
                entry_spot = pos_details["entry_spot"]
                delta = pos_details["delta"]
                entry_premium = pos_details["entry_premium"]
                total_shares = pos_details["total_shares"]
                option_type = pos_details["option_type"]

                spot_change = (cmp - entry_spot) if option_type == "CE" else (entry_spot - cmp)
                approx_premium_change = spot_change * abs(delta)
                curr_premium = max(0.5, entry_premium + approx_premium_change)
                prem_gain_pct = ((curr_premium - entry_premium) / entry_premium) * 100.0

                bars_held = i - pos_details["entry_idx"]

                # Target (+25% premium gain) or SL (-10% premium drop) or EOD
                if prem_gain_pct >= 25.0 or prem_gain_pct <= -10.0 or bars_held >= 12:
                    exit_val = curr_premium * total_shares
                    entry_val = entry_premium * total_shares

                    exit_costs = options_engine.calculate_trade_costs(exit_val, is_sell=True, contract_type="OPTION")
                    exit_brokerage = exit_costs["brokerage"]
                    total_trade_brokerage = pos_details["entry_brokerage"] + exit_brokerage

                    gross_pnl = exit_val - entry_val
                    net_pnl = gross_pnl - total_trade_brokerage
                    pnl_pct = (net_pnl / entry_val) * 100.0 if entry_val > 0 else 0.0

                    available_capital += net_pnl

                    trades_log.append({
                        "symbol": symbol,
                        "verdict": pos_details["verdict"],
                        "strike": pos_details["strike"],
                        "lots": pos_details["lots"],
                        "entry_premium": entry_premium,
                        "exit_premium": round(curr_premium, 2),
                        "gross_pnl": round(gross_pnl, 2),
                        "brokerage_paid": round(total_trade_brokerage, 2),
                        "net_pnl": round(net_pnl, 2),
                        "pnl_pct": round(pnl_pct, 2),
                        "exit_reason": "target_hit" if prem_gain_pct >= 25.0 else ("sl_hit" if prem_gain_pct <= -10.0 else "time_exit")
                    })
                    in_position = False

    # Backtest Performance Metrics Calculation
    print("\n================================================================")
    print("              F&O QUANT BACKTEST RESULTS SUMMARY (V2)")
    print("================================================================")

    if not trades_log:
        print("No trades met the strict Waterfall Score (8.0) and Cost-Gate criteria.")
        return

    df_trades = pd.DataFrame(trades_log)
    winning_trades = df_trades[df_trades["net_pnl"] > 0]
    losing_trades = df_trades[df_trades["net_pnl"] < 0]

    total_trades = len(df_trades)
    win_rate = (len(winning_trades) / total_trades) * 100.0 if total_trades > 0 else 0.0
    total_net_pnl = df_trades["net_pnl"].sum()
    total_gross_pnl = df_trades["gross_pnl"].sum()
    total_brokerage = df_trades["brokerage_paid"].sum()
    net_return_pct = (total_net_pnl / initial_capital) * 100.0

    gross_wins = winning_trades["net_pnl"].sum() if not winning_trades.empty else 0.0
    gross_losses = abs(losing_trades["net_pnl"].sum()) if not losing_trades.empty else 1.0
    profit_factor = gross_wins / gross_losses if gross_losses > 0 else gross_wins

    avg_win = winning_trades["net_pnl"].mean() if not winning_trades.empty else 0.0
    avg_loss = losing_trades["net_pnl"].mean() if not losing_trades.empty else 0.0

    df_trades["cum_pnl"] = df_trades["net_pnl"].cumsum()
    df_trades["equity"] = initial_capital + df_trades["cum_pnl"]
    df_trades["peak"] = df_trades["equity"].cummax()
    df_trades["drawdown"] = (df_trades["equity"] - df_trades["peak"]) / df_trades["peak"] * 100.0
    max_drawdown = df_trades["drawdown"].min()

    print(f" Initial Capital Pool        : INR {initial_capital:,.2f}")
    print(f" Final Portfolio Value       : INR {available_capital:,.2f}")
    print(f" Total Net Realized Return   : INR {total_net_pnl:+,.2f} ({net_return_pct:+.2f}%)")
    print(f" Total Trades Executed       : {total_trades}")
    print(f" Winning Trades              : {len(winning_trades)}")
    print(f" Losing Trades               : {len(losing_trades)}")
    print(f" Win Rate                    : {win_rate:.2f}%")
    print(f" Profit Factor               : {profit_factor:.2f}")
    print(f" Average Winning Trade       : INR {avg_win:+,.2f}")
    print(f" Average Losing Trade        : INR {avg_loss:+,.2f}")
    print(f" Total Brokerage Paid (INR)  : INR {total_brokerage:,.2f}")
    print(f" Max Drawdown                : {max_drawdown:.2f}%")
    print("================================================================")

    df_trades.to_csv(os.path.join(os.path.dirname(__file__), "backtest_fo_results.csv"), index=False)
    print("Detailed F&O backtest trade log saved to backtest_fo_results.csv")

if __name__ == "__main__":
    run_fo_backtest()
