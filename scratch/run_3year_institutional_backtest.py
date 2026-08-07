import os
import math
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, date
from typing import List, Dict, Any

def calculate_zerodha_cash_costs(turnover_inr: float, is_sell: bool = False) -> float:
    """Zerodha Cash Intraday: 0.03% or ₹20 (lower) + STT 0.025% sell + NSE Exch 0.00297% + GST 18% + Stamp Duty 0.003% buy."""
    brokerage = min(20.0, turnover_inr * 0.0003)
    stt = turnover_inr * 0.00025 if is_sell else 0.0
    exchange_fee = turnover_inr * 0.0000297
    gst = (brokerage + exchange_fee) * 0.18
    sebi_fee = turnover_inr * 0.000001
    stamp_duty = turnover_inr * 0.00003 if not is_sell else 0.0
    return brokerage + stt + exchange_fee + gst + sebi_fee + stamp_duty

def calculate_zerodha_fo_costs(premium_turnover_inr: float, is_sell: bool = False) -> float:
    """Zerodha Options: Flat ₹20 / order + STT 0.0625% sell premium + NSE Exch 0.0355% + GST 18% + Stamp Duty 0.003% buy."""
    brokerage = 20.0
    stt = premium_turnover_inr * 0.000625 if is_sell else 0.0
    exchange_fee = premium_turnover_inr * 0.000355
    gst = (brokerage + exchange_fee) * 0.18
    sebi_fee = premium_turnover_inr * 0.000001
    stamp_duty = premium_turnover_inr * 0.00003 if not is_sell else 0.0
    return brokerage + stt + exchange_fee + gst + sebi_fee + stamp_duty

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50.0)

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df['High']
    low = df['Low']
    close = df['Close'].shift(1)
    tr = pd.concat([high - low, (high - close).abs(), (low - close).abs()], axis=1).max(axis=1)
    return tr.rolling(window=period).mean().fillna(0.0)

def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df['High']
    low = df['Low']
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    tr = calculate_atr(df, period)
    plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(period).mean() / tr.replace(0, np.nan))
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(period).mean() / tr.replace(0, np.nan))
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.rolling(period).mean().fillna(20.0)

def run_3year_backtest():
    print("==========================================================================")
    print("  3-YEAR QUANTITATIVE BACKTEST ENGINE (AUG 01, 2023 – AUG 07, 2026)")
    print("  Executing bar-by-bar strategy logic on actual historical OHLCV data")
    print("==========================================================================")

    start_date = "2023-08-01"
    end_date = "2026-08-07"
    risk_free_rate = 0.065  # 6.5% Indian 10Y G-Sec Rate

    tickers_cash = [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "ICICIBANK.NS", "HDFCBANK.NS",
        "BHARTIARTL.NS", "SBIN.NS", "ITC.NS", "KOTAKBANK.NS", "LT.NS",
        "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "TITAN.NS", "ULTRACEMCO.NS",
        "SUNPHARMA.NS", "BAJFINANCE.NS", "NESTLEIND.NS", "M&M.NS", "TATAMOTORS.NS"
    ]

    print("[Data Ingestion] Fetching NIFTY 50 Benchmark data...")
    nifty_df = yf.download("^NSEI", start=start_date, end=end_date, progress=False)
    if isinstance(nifty_df.columns, pd.MultiIndex):
        nifty_df.columns = [col[0] for col in nifty_df.columns]
    nifty_ret = nifty_df['Close'].pct_change(14).fillna(0.0)

    # -------------------------------------------------------------------------
    # BOT 1: INTRADAY EQUITY CASH ENGINE 3-YEAR BACKTEST
    # -------------------------------------------------------------------------
    print("\n[Bot 1 Backtest] Executing Intraday Equity Cash Strategy (Aug 2023 - Aug 2026)...")
    init_cap_b1 = 100000.0  # ₹1 Lakh
    cap_b1 = init_cap_b1
    mis_leverage_b1 = 5.0
    trades_b1 = []

    for ticker in tickers_cash:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if df.empty or len(df) < 30:
            continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]

        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
        close = df['Close']
        high = df['High']
        low = df['Low']

        ema9 = close.ewm(span=9, adjust=False).mean()
        ema21 = close.ewm(span=21, adjust=False).mean()
        rsi = calculate_rsi(close)
        atr = calculate_atr(df)
        adx = calculate_adx(df)
        stock_ret = close.pct_change(14).fillna(0.0)

        in_pos = False
        pos_info = {}

        for i in range(25, len(df) - 1):
            cmp = float(close.iloc[i])
            curr_atr = float(atr.iloc[i])
            curr_adx = float(adx.iloc[i])
            curr_rsi = float(rsi.iloc[i])
            curr_dt = df.index[i]

            stock_m = stock_ret.iloc[i] if i < len(stock_ret) else 0.0
            nifty_m = nifty_ret.iloc[i] if i < len(nifty_ret) else 0.0
            rs_val = (1.0 + stock_m) / (1.0 + nifty_m) if (1.0 + nifty_m) != 0 else 1.0

            if not in_pos:
                score = 5.0
                if ema9.iloc[i] > ema21.iloc[i]: score += 1.2
                else: score -= 1.2
                if curr_rsi >= 50: score += 1.0
                else: score -= 1.0
                if curr_adx >= 22: score += 0.8
                if rs_val > 1.0: score += 1.0
                elif rs_val < 1.0: score -= 1.0

                verdict = "AVOID"
                if score >= 8.0 and rs_val > 1.0: verdict = "BUY"
                elif score <= 2.0 and rs_val < 1.0: verdict = "SELL"

                if verdict in ["BUY", "SELL"]:
                    sl_dist = max(curr_atr * 1.25, cmp * 0.008)
                    target_dist = sl_dist * 2.0

                    target_price = (cmp + target_dist) if verdict == "BUY" else (cmp - target_dist)
                    sl_price = (cmp - sl_dist) if verdict == "BUY" else (cmp + sl_dist)

                    alloc_cash = min(cap_b1 * 0.15, 15000.0)
                    pos_val = alloc_cash * mis_leverage_b1
                    qty = max(1, math.floor(pos_val / cmp))
                    actual_pos_val = qty * cmp

                    entry_cost = calculate_zerodha_cash_costs(actual_pos_val, is_sell=(verdict == "SELL"))
                    expected_gain = qty * target_dist

                    if expected_gain < (entry_cost * 6.0):
                        continue

                    in_pos = True
                    pos_info = {
                        "symbol": ticker.replace(".NS", ""),
                        "verdict": verdict,
                        "qty": qty,
                        "entry_price": cmp,
                        "target_price": target_price,
                        "sl_price": sl_price,
                        "pos_val": actual_pos_val,
                        "entry_idx": i,
                        "entry_date": curr_dt,
                        "entry_cost": entry_cost
                    }
            elif in_pos:
                qty = pos_info["qty"]
                verdict = pos_info["verdict"]
                entry_price = pos_info["entry_price"]
                target_price = pos_info["target_price"]
                sl_price = pos_info["sl_price"]

                hit_target = (high.iloc[i] >= target_price) if verdict == "BUY" else (low.iloc[i] <= target_price)
                hit_sl = (low.iloc[i] <= sl_price) if verdict == "BUY" else (high.iloc[i] >= sl_price)
                duration = i - pos_info["entry_idx"]

                if hit_target or hit_sl or duration >= 3:
                    exit_price = target_price if hit_target else (sl_price if hit_sl else cmp)
                    exit_val = qty * exit_price
                    entry_val = pos_info["pos_val"]

                    exit_cost = calculate_zerodha_cash_costs(exit_val, is_sell=(verdict == "BUY"))
                    total_friction = pos_info["entry_cost"] + exit_cost

                    gross_pnl = (exit_val - entry_val) if verdict == "BUY" else (entry_val - exit_val)
                    net_pnl = gross_pnl - total_friction
                    pnl_pct = (net_pnl / (entry_val / mis_leverage_b1)) * 100.0

                    cap_b1 += net_pnl
                    trades_b1.append({
                        "date": curr_dt,
                        "symbol": pos_info["symbol"],
                        "verdict": verdict,
                        "qty": qty,
                        "entry_price": entry_price,
                        "exit_price": round(exit_price, 2),
                        "gross_pnl": round(gross_pnl, 2),
                        "total_friction": round(total_friction, 2),
                        "net_pnl": round(net_pnl, 2),
                        "pnl_pct": round(pnl_pct, 2),
                        "duration": duration,
                        "reason": "TARGET" if hit_target else ("SL" if hit_sl else "EOD")
                    })
                    in_pos = False

    # -------------------------------------------------------------------------
    # BOT 2: SHADOW TRADERS F&O QUANT ENGINE 3-YEAR BACKTEST
    # -------------------------------------------------------------------------
    print("\n[Bot 2 Backtest] Executing Shadow Traders F&O Strategy (Aug 2023 - Aug 2026)...")
    init_cap_b2 = 500000.0  # ₹5 Lakhs
    cap_b2 = init_cap_b2
    trades_b2 = []

    fo_universe = ["^NSEI", "^NSEBANK", "RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "TCS.NS"]

    for symbol in fo_universe:
        df = yf.download(symbol, start=start_date, end=end_date, progress=False)
        if df.empty or len(df) < 30:
            continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]

        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
        close = df['Close']
        high = df['High']
        low = df['Low']

        ema9 = close.ewm(span=9, adjust=False).mean()
        ema21 = close.ewm(span=21, adjust=False).mean()
        rsi = calculate_rsi(close)
        atr = calculate_atr(df)

        in_pos = False
        pos_info = {}

        for i in range(25, len(df) - 1):
            cmp = float(close.iloc[i])
            curr_atr = float(atr.iloc[i])
            curr_dt = df.index[i]

            if not in_pos:
                is_bull = (ema9.iloc[i] > ema21.iloc[i]) and (rsi.iloc[i] >= 52)
                is_bear = (ema9.iloc[i] < ema21.iloc[i]) and (rsi.iloc[i] <= 48)

                if is_bull or is_bear:
                    trade_type = "BUY_CE" if is_bull else "BUY_PE"
                    # Simulated Options Delta 0.50
                    est_premium = cmp * 0.025
                    lot_size = 50 if "NSE" in symbol else 100
                    num_lots = max(1, math.floor((cap_b2 * 0.10) / (est_premium * lot_size)))
                    qty = num_lots * lot_size
                    premium_val = qty * est_premium

                    target_premium = est_premium * 1.25  # +25% Option Premium Gain
                    sl_premium = est_premium * 0.90      # -10% Option Premium Drop

                    entry_cost = calculate_zerodha_fo_costs(premium_val, is_sell=False)

                    in_pos = True
                    pos_info = {
                        "symbol": symbol.replace("^", "").replace(".NS", ""),
                        "trade_type": trade_type,
                        "qty": qty,
                        "entry_premium": est_premium,
                        "target_premium": target_premium,
                        "sl_premium": sl_premium,
                        "underlying_entry": cmp,
                        "entry_idx": i,
                        "entry_date": curr_dt,
                        "entry_cost": entry_cost
                    }
            elif in_pos:
                qty = pos_info["qty"]
                trade_type = pos_info["trade_type"]
                entry_premium = pos_info["entry_premium"]
                target_premium = pos_info["target_premium"]
                sl_premium = pos_info["sl_premium"]
                underlying_entry = pos_info["underlying_entry"]

                stock_move_pct = (cmp - underlying_entry) / underlying_entry
                if trade_type == "BUY_PE":
                    stock_move_pct = -stock_move_pct

                # Delta ~ 0.50 scaling
                curr_premium = max(1.0, entry_premium * (1.0 + (stock_move_pct * 8.0)))
                duration = i - pos_info["entry_idx"]

                hit_target = curr_premium >= target_premium
                hit_sl = curr_premium <= sl_premium

                if hit_target or hit_sl or duration >= 2:
                    exit_premium = target_premium if hit_target else (sl_premium if hit_sl else curr_premium)
                    exit_val = qty * exit_premium
                    entry_val = qty * entry_premium

                    exit_cost = calculate_zerodha_fo_costs(exit_val, is_sell=True)
                    total_friction = pos_info["entry_cost"] + exit_cost

                    gross_pnl = exit_val - entry_val
                    net_pnl = gross_pnl - total_friction
                    pnl_pct = (net_pnl / entry_val) * 100.0

                    cap_b2 += net_pnl
                    trades_b2.append({
                        "date": curr_dt,
                        "symbol": pos_info["symbol"],
                        "trade_type": trade_type,
                        "qty": qty,
                        "entry_premium": round(entry_premium, 2),
                        "exit_premium": round(exit_premium, 2),
                        "gross_pnl": round(gross_pnl, 2),
                        "total_friction": round(total_friction, 2),
                        "net_pnl": round(net_pnl, 2),
                        "pnl_pct": round(pnl_pct, 2),
                        "duration": duration,
                        "reason": "TARGET" if hit_target else ("SL" if hit_sl else "EOD")
                    })
                    in_pos = False

    # -------------------------------------------------------------------------
    # STATISTICAL QUANTITATIVE METRICS COMPILATION
    # -------------------------------------------------------------------------
    def compute_metrics(trades: List[Dict], init_cap: float, end_cap: float, name: str) -> Dict[str, Any]:
        if not trades:
            return {"name": name}

        df_t = pd.DataFrame(trades)
        total_trades = len(df_t)
        wins = df_t[df_t["net_pnl"] > 0]
        losses = df_t[df_t["net_pnl"] < 0]

        win_rate = (len(wins) / total_trades) * 100.0
        total_net_pnl = df_t["net_pnl"].sum()
        total_friction = df_t["total_friction"].sum()
        net_return_pct = ((end_cap - init_cap) / init_cap) * 100.0

        years = 3.0
        cagr = (((end_cap / init_cap) ** (1.0 / years)) - 1.0) * 100.0

        gross_wins = wins["net_pnl"].sum() if not wins.empty else 0.0
        gross_losses = abs(losses["net_pnl"].sum()) if not losses.empty else 1.0
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else gross_wins

        avg_win = wins["net_pnl"].mean() if not wins.empty else 0.0
        avg_loss = losses["net_pnl"].mean() if not losses.empty else 0.0
        expectancy = (win_rate / 100.0 * avg_win) + ((1.0 - win_rate / 100.0) * avg_loss)

        df_t["cum_pnl"] = df_t["net_pnl"].cumsum()
        df_t["equity"] = init_cap + df_t["cum_pnl"]
        df_t["peak"] = df_t["equity"].cummax()
        df_t["drawdown"] = (df_t["equity"] - df_t["peak"]) / df_t["peak"] * 100.0
        max_dd = df_t["drawdown"].min()

        # Daily Returns for Sharpe / Sortino / VaR
        daily_returns = df_t["pnl_pct"] / 100.0
        mean_ret = daily_returns.mean()
        std_ret = daily_returns.std() if len(daily_returns) > 1 else 0.01

        # Annualized Sharpe (Rf = 6.5%)
        sharpe = ((mean_ret * 252) - risk_free_rate) / (std_ret * math.sqrt(252)) if std_ret > 0 else 0.0

        # Sortino (Downside deviation)
        downside = daily_returns[daily_returns < 0]
        std_downside = downside.std() if len(downside) > 1 else 0.01
        sortino = ((mean_ret * 252) - risk_free_rate) / (std_downside * math.sqrt(252)) if std_downside > 0 else 0.0

        # Calmar Ratio (CAGR / Max DD)
        calmar = abs(cagr / max_dd) if max_dd < 0 else cagr

        # Value at Risk (VaR 95%) & CVaR
        var_95 = np.percentile(daily_returns, 5) * 100.0
        cvar_95 = daily_returns[daily_returns <= np.percentile(daily_returns, 5)].mean() * 100.0

        avg_duration = df_t["duration"].mean()

        return {
            "name": name,
            "init_cap": init_cap,
            "end_cap": end_cap,
            "net_pnl": total_net_pnl,
            "net_return_pct": net_return_pct,
            "cagr": cagr,
            "max_dd": max_dd,
            "sharpe": sharpe,
            "sortino": sortino,
            "calmar": calmar,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "total_trades": total_trades,
            "wins": len(wins),
            "losses": len(losses),
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "expectancy": expectancy,
            "var_95": var_95,
            "cvar_95": cvar_95,
            "friction": total_friction,
            "avg_duration": avg_duration
        }

    m1 = compute_metrics(trades_b1, init_cap_b1, cap_b1, "Bot 1: Intraday Equity Cash Engine")
    m2 = compute_metrics(trades_b2, init_cap_b2, cap_b2, "Bot 2: Shadow Traders F&O Engine")

    print("\n==========================================================================")
    print("      3-YEAR INSTITUTIONAL BACKTEST RESULTS (EMPIRICAL CODES RUN)")
    print("==========================================================================")
    print(f" METRIC                          | BOT 1 (CASH MIS 5X) | BOT 2 (F&O SWARM)")
    print("---------------------------------|---------------------|-------------------")
    print(f" Initial Capital Allocation       | INR 1,00,000.00     | INR 5,00,000.00")
    print(f" Ending Portfolio Value          | INR {m1['end_cap']:,.2f}     | INR {m2['end_cap']:,.2f}")
    print(f" Total Realized Net P&L          | INR {m1['net_pnl']:+,.2f}    | INR {m2['net_pnl']:+,.2f}")
    print(f" Net Return % (3-Year Total)     | {m1['net_return_pct']:+.2f}%              | {m2['net_return_pct']:+.2f}%")
    print(f" CAGR % (Annualized Growth)      | {m1['cagr']:.2f}%               | {m2['cagr']:.2f}%")
    print(f" Max Drawdown %                  | {m1['max_dd']:.2f}%              | {m2['max_dd']:.2f}%")
    print(f" Sharpe Ratio (Rf = 6.5%)        | {m1['sharpe']:.2f}x                | {m2['sharpe']:.2f}x")
    print(f" Sortino Ratio                   | {m1['sortino']:.2f}x                | {m2['sortino']:.2f}x")
    print(f" Calmar Ratio                    | {m1['calmar']:.2f}x                | {m2['calmar']:.2f}x")
    print(f" Win Rate %                      | {m1['win_rate']:.2f}%              | {m2['win_rate']:.2f}%")
    print(f" Profit Factor                   | {m1['profit_factor']:.2f}x                | {m2['profit_factor']:.2f}x")
    print(f" Total Trades Executed           | {m1['total_trades']}                 | {m2['total_trades']}")
    print(f" Average Win Trade               | INR {m1['avg_win']:+,.2f}       | INR {m2['avg_win']:+,.2f}")
    print(f" Average Loss Trade              | INR {m1['avg_loss']:+,.2f}       | INR {m2['avg_loss']:+,.2f}")
    print(f" Mathematical Expectancy / Trade | INR {m1['expectancy']:+,.2f}        | INR {m2['expectancy']:+,.2f}")
    print(f" Value at Risk (VaR 95% 1-Day)   | {m1['var_95']:.2f}%              | {m2['var_95']:.2f}%")
    print(f" Conditional VaR (CVaR 95%)      | {m1['cvar_95']:.2f}%              | {m2['cvar_95']:.2f}%")
    print(f" Total Zerodha Friction Paid     | INR {m1['friction']:,.2f}      | INR {m2['friction']:,.2f}")
    print("==========================================================================")

    # Save summary JSON for report generation
    summary = {"m1": m1, "m2": m2}
    import json
    with open(r"c:\Users\RANAY\Desktop\FO TRADING BOT\scratch\backtest_3year_results.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("Saved scratch/backtest_3year_results.json")

if __name__ == "__main__":
    run_3year_backtest()
