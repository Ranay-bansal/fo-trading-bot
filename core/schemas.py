from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class FOScoutOutput(BaseModel):
    ticker: str
    symbol: str
    is_index: bool
    spot_cmp: float
    rvol: float
    price_change_pct: float
    lot_size: int
    strike_step: float
    scout_rank: int
    scout_modifier: float = 0.0

class TrendData(BaseModel):
    dma20_position: str
    dma50_position: str
    dma_slope: str
    ema_state: str

class MomentumData(BaseModel):
    rsi: float
    rsi_state: str
    adx: float
    adx_state: str

class VolatilityData(BaseModel):
    atr: float
    atr_pct: float
    bb_squeeze: bool

class FOTechnicianOutput(BaseModel):
    ticker: str
    timeframe_signal: str
    trend: TrendData
    momentum: MomentumData
    volatility: VolatilityData
    support: float
    resistance: float
    vix: float
    vix_regime: str
    technical_score: float
    stance: str  # "bullish" / "bearish" / "neutral"
    patterns_detected: List[str] = []
    suggested_spot_entry: float
    suggested_spot_sl: float
    suggested_spot_target: float
    risk_reward_ratio: float

class FOContractData(BaseModel):
    contract_type: str  # "OPTION_CE" / "OPTION_PE" / "FUTURES"
    symbol: str
    strike_price: float
    expiry_dte: int
    lot_size: int
    lots_qty: int
    total_shares: int
    option_premium: float
    delta: float
    gamma: float
    theta_per_day: float
    vega: float
    premium_value_inr: float
    estimated_brokerage_inr: float = 20.0
    estimated_total_cost_inr: float

class FOJudgeOutput(BaseModel):
    ticker: str
    run_timestamp: datetime
    verdict: str  # "BUY_CE" / "BUY_PE" / "BUY_FUT" / "SELL_FUT" / "WATCHLIST" / "AVOID" / "REJECT"
    waterfall_score: float
    confidence: float
    contract: FOContractData
    position_sizing_inr: float
    reasoning: str
    hard_reject_reason: Optional[str] = None

class FOOpenPosition(BaseModel):
    ticker: str
    contract_type: str
    symbol: str
    strike_price: float
    lots: int
    total_shares: int
    entry_premium: float
    entry_spot: float
    sl_spot: float
    target_spot: float
    entered_at: datetime
    megabull_order_id: str
    brokerage_paid_inr: float = 20.0

class FOPortfolioState(BaseModel):
    last_updated: Optional[datetime] = None
    pool_total: float = 500000.0
    pool_available: float = 500000.0
    pool_deployed: float = 0.0
    daily_pnl_inr: float = 0.0
    daily_pnl_pct: float = 0.0
    total_brokerage_paid_inr: float = 0.0
    trades_today: int = 0
    open_positions: List[FOOpenPosition] = []
