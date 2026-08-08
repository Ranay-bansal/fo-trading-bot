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
    spot_entry: float = 0.0

class Bot1Signal(BaseModel):
    ticker: str
    symbol: str
    side: str  # "BUY" / "SELL" / "AVOID"
    spot_cmp: float
    signal_score: float
    timeframe: str
    suggested_entry: float
    suggested_sl: float
    suggested_target: float
    quantity: int
    position_value_inr: float
    estimated_brokerage_inr: float = 20.0
    reasoning: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class NewsdeskOutput(BaseModel):
    ticker: str
    symbol: str
    news_sentiment_score: float = 5.0  # 0.0 to 10.0 (5.0 neutral)
    catalyst_risk_score: float = 3.0   # 0.0 to 10.0
    market_regime: str = "rangebound"   # "bullish", "bearish", "volatile", "rangebound"
    macro_risk_score: float = 4.0      # 0.0 to 10.0
    overall_news_score: float = 5.0    # 0.0 to 10.0
    stance: str = "neutral"            # "bullish", "bearish", "neutral"
    headline_summaries: List[str] = Field(default_factory=list)
    catalyst_events: List[str] = Field(default_factory=list)

class BullDebaterOutput(BaseModel):
    ticker: str
    symbol: str
    conviction_score: float = 5.0      # 0.0 to 10.0
    upside_arguments: List[str] = Field(default_factory=list)
    target_rationale: str = ""
    key_catalysts: List[str] = Field(default_factory=list)
    suggested_target_multiplier: float = 1.05
    stance: str = "bullish"

class BearDebaterOutput(BaseModel):
    ticker: str
    symbol: str
    bear_risk_score: float = 3.0       # 0.0 to 10.0
    downside_arguments: List[str] = Field(default_factory=list)
    stop_loss_risks: str = ""
    market_headwinds: List[str] = Field(default_factory=list)
    suggested_sl_buffer_pct: float = 0.015
    stance: str = "bearish"

class CommitteeDebateRecord(BaseModel):
    timestamp: str
    symbol: str
    ticker: str
    scout_stance: str
    tech_stance: str
    news_stance: str
    bull_stance: str
    bear_stance: str
    consensus_score: float
    fact_checker_approved: bool
    risk_override_status: str
    judge_verdict: str
    reasoning: str

class FOJudgeOutput(BaseModel):
    ticker: str
    run_timestamp: datetime
    verdict: str  # "BUY_CE" / "BUY_PE" / "BUY_FUT" / "SELL_FUT" / "SCALP_CE" / "SCALP_PE" / "WATCHLIST" / "AVOID" / "REJECT"
    waterfall_score: float
    confidence: float
    contract: FOContractData
    position_sizing_inr: float
    reasoning: str
    hard_reject_reason: Optional[str] = None
    consensus_score: Optional[float] = None
    fact_checker_approved: bool = True
    risk_override_status: str = "NO_OVERRIDE"  # "NO_OVERRIDE" / "RISK_OVERRIDE_TRIGGERED"
    scout_stance: Optional[str] = None
    tech_stance: Optional[str] = None
    news_stance: Optional[str] = None
    bull_stance: Optional[str] = None
    bear_stance: Optional[str] = None

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
