import math
import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

def _cdf(x: float) -> float:
    """Standard normal cumulative distribution function using math.erf."""
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def _pdf(x: float) -> float:
    """Standard normal probability density function."""
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

class OptionsEngine:
    """
    Institutional Options Pricing Engine:
    - Black-Scholes Option Premium & Greeks (Delta, Gamma, Theta, Vega)
    - Strike Selector (ATM / ITM Call & Put)
    - Futures Contract Pricing
    - Statutory Brokerage & Cost Deductions (₹20 flat brokerage + STT + Exchange fees)
    """

    def __init__(self, risk_free_rate: float = 0.065):
        self.r = risk_free_rate  # 6.5% RBI Risk-Free Rate

    def calculate_bs_price_and_greeks(
        self, spot: float, strike: float, dte: float, iv_pct: float, option_type: str = "CE"
    ) -> Dict[str, float]:
        """
        Calculates Black-Scholes option price and Greeks for CE or PE options.
        """
        if spot <= 0 or strike <= 0 or dte <= 0 or iv_pct <= 0:
            # Fallback intrinsic value if inputs invalid
            intrinsic = max(0.0, spot - strike) if option_type == "CE" else max(0.0, strike - spot)
            return {"price": max(1.0, intrinsic), "delta": 0.5, "gamma": 0.0, "theta_per_day": 0.0, "vega": 0.0}

        T = dte / 365.0
        sigma = max(0.05, iv_pct / 100.0)

        d1 = (math.log(spot / strike) + (self.r + (sigma ** 2) / 2.0) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        if option_type.upper() == "CE":
            price = spot * _cdf(d1) - strike * math.exp(-self.r * T) * _cdf(d2)
            delta = _cdf(d1)
        else:
            price = strike * math.exp(-self.r * T) * _cdf(-d2) - spot * _cdf(-d1)
            delta = _cdf(d1) - 1.0

        gamma = _pdf(d1) / (spot * sigma * math.sqrt(T))
        theta = -(spot * _pdf(d1) * sigma) / (2 * math.sqrt(T)) - self.r * strike * math.exp(-self.r * T) * _cdf(d2 if option_type == "CE" else -d2)
        theta_per_day = theta / 365.0
        vega = spot * _pdf(d1) * math.sqrt(T) / 100.0

        return {
            "price": round(max(0.5, price), 2),
            "delta": round(delta, 4),
            "gamma": round(gamma, 6),
            "theta_per_day": round(theta_per_day, 2),
            "vega": round(vega, 2)
        }

    def select_strike(self, spot: float, strike_step: float, stance: str = "bullish", itm_depth: int = 1) -> float:
        """
        Selects ATM or ITM strike based on spot price and step size.
        """
        atm_strike = round(spot / strike_step) * strike_step
        if stance == "bullish":
            # For CE, ITM strike is lower than spot
            return max(strike_step, atm_strike - (itm_depth * strike_step))
        else:
            # For PE, ITM strike is higher than spot
            return atm_strike + (itm_depth * strike_step)

    def calculate_futures_price(self, spot: float, dte: float) -> float:
        """
        Calculates Futures price based on cost-of-carry model.
        """
        T = max(1.0, dte) / 365.0
        fut_price = spot * math.exp(self.r * T)
        return round(fut_price, 2)

    def calculate_trade_costs(self, turnover_inr: float, is_sell: bool = False, contract_type: str = "OPTION") -> Dict[str, float]:
        """
        Calculates brokerage (₹20 flat) + STT + Exchange fees + GST.
        """
        brokerage = 20.0  # Flat ₹20 per trade
        
        # STT (Securities Transaction Tax)
        stt = 0.0
        if is_sell:
            if contract_type == "OPTION":
                stt = turnover_inr * 0.000625  # 0.0625% on option premium sell
            else:
                stt = turnover_inr * 0.000125  # 0.0125% on futures sell
                
        exchange_fee = turnover_inr * 0.00053  # Exchange transaction fee
        gst = (brokerage + exchange_fee) * 0.18  # 18% GST
        sebi_charges = turnover_inr * 0.000001  # SEBI turnover fee
        
        total_cost = brokerage + stt + exchange_fee + gst + sebi_charges
        return {
            "brokerage": round(brokerage, 2),
            "stt": round(stt, 2),
            "exchange_fee": round(exchange_fee, 2),
            "gst": round(gst, 2),
            "total_cost": round(total_cost, 2)
        }
