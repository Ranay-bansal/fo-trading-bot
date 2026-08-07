import os

def build_ultra_modern_ui():
    base_dir = r"c:\Users\RANAY\Desktop\FO TRADING BOT"
    logo_b64_path = os.path.join(base_dir, "scratch", "logo_b64.txt")
    
    with open(logo_b64_path, "r") as f:
        logo_b64 = f.read().strip()

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <title>SHADOW TRADERS — Institutional F&O Quant Terminal</title>
  <link rel="manifest" href="manifest.json?v=6">
  <meta name="theme-color" content="#0f172a">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="apple-touch-icon" href="logo.jpg">
  
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  
  <style>
    :root {{
      --glass-surface: rgba(15, 23, 42, 0.45);
      --glass-surface-hover: rgba(30, 41, 59, 0.6);
      --glass-card: rgba(15, 23, 42, 0.55);
      --glass-border: rgba(255, 255, 255, 0.12);
      --glass-border-hover: rgba(56, 189, 248, 0.4);
      --glass-shadow: 0 20px 50px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.1);
      
      --accent-cyan: #38bdf8;
      --accent-blue: #60a5fa;
      --accent-purple: #c084fc;
      --accent-green: #4ade80;
      --accent-red: #f87171;
      --accent-amber: #fbbf24;
      
      --text-heading: #f8fafc;
      --text-body: #cbd5e1;
      --text-muted: #94a3b8;
      --text-subtle: #64748b;
      
      --font-sans: 'Inter', 'Plus Jakarta Sans', sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    
    body {{
      font-family: var(--font-sans);
      color: var(--text-body);
      min-height: 100vh;
      padding: 28px 36px;
      background-image: url('background.jpg');
      background-size: cover;
      background-position: center;
      background-repeat: no-repeat;
      background-attachment: fixed;
      position: relative;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }}

    body::before {{
      content: '';
      position: fixed;
      inset: 0;
      background: radial-gradient(circle at 50% 0%, rgba(15, 23, 42, 0.2), rgba(3, 7, 18, 0.65));
      z-index: -1;
      pointer-events: none;
    }}

    /* CLEAN TOP BANNER */
    .sim-banner {{
      background: rgba(15, 23, 42, 0.55);
      border: 1px solid rgba(251, 191, 36, 0.3);
      color: var(--accent-amber);
      padding: 9px 20px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
      letter-spacing: 0.4px;
      margin-bottom: 24px;
      backdrop-filter: blur(16px);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }}

    /* HEADER */
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 28px;
      padding: 16px 24px;
      background: var(--glass-surface);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      backdrop-filter: blur(20px);
      box-shadow: var(--glass-shadow);
    }}

    .brand-group {{
      display: flex;
      align-items: center;
      gap: 16px;
    }}

    .logo-frame {{
      width: 48px;
      height: 48px;
      border-radius: 14px;
      padding: 1.5px;
      background: linear-gradient(135deg, rgba(56, 189, 248, 0.6), rgba(192, 132, 252, 0.6));
    }}

    .brand-logo {{
      width: 100%;
      height: 100%;
      border-radius: 12.5px;
      object-fit: cover;
      display: block;
      background: #090d16;
    }}

    .brand-meta h1 {{
      font-size: 20px;
      font-weight: 600;
      letter-spacing: -0.2px;
      color: var(--text-heading);
    }}

    .brand-meta p {{
      font-size: 12.5px;
      color: var(--text-muted);
      font-weight: 400;
      margin-top: 1px;
    }}

    .header-actions {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .badge-status {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(56, 189, 248, 0.1);
      border: 1px solid rgba(56, 189, 248, 0.25);
      color: var(--accent-cyan);
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 500;
    }}

    .btn-install {{
      display: inline-flex;
      align-items: center;
      gap: 7px;
      background: linear-gradient(135deg, var(--accent-cyan), #0284c7);
      color: #040914;
      font-weight: 600;
      padding: 8px 18px;
      border-radius: 18px;
      border: none;
      cursor: pointer;
      font-size: 12.5px;
      box-shadow: 0 4px 14px rgba(56, 189, 248, 0.25);
      transition: all 0.2s ease;
    }}

    .btn-install:hover {{
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(56, 189, 248, 0.4);
    }}

    /* STATS MATRIX */
    .stats-row {{
      display: grid;
      grid-template-cols: repeat(4, 1fr);
      gap: 18px;
      margin-bottom: 28px;
    }}

    .stat-box {{
      background: var(--glass-surface);
      border: 1px solid var(--glass-border);
      border-radius: 18px;
      padding: 20px 22px;
      backdrop-filter: blur(20px);
      box-shadow: var(--glass-shadow);
      transition: all 0.25s ease;
    }}

    .stat-box:hover {{
      border-color: var(--glass-border-hover);
      background: var(--glass-surface-hover);
      transform: translateY(-2px);
    }}

    .stat-title {{
      font-size: 12px;
      font-weight: 500;
      color: var(--text-muted);
      margin-bottom: 10px;
    }}

    .stat-number {{
      font-family: var(--font-mono);
      font-size: 22px;
      font-weight: 600;
      color: var(--text-heading);
      letter-spacing: -0.5px;
      font-variant-numeric: tabular-nums;
    }}

    .stat-desc {{
      font-size: 11.5px;
      color: var(--text-subtle);
      margin-top: 6px;
      font-weight: 400;
    }}

    /* TAB NAVIGATION */
    .tab-bar {{
      display: flex;
      gap: 10px;
      margin-bottom: 24px;
      overflow-x: auto;
    }}

    .tab-item {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: var(--glass-surface);
      border: 1px solid var(--glass-border);
      color: var(--text-muted);
      padding: 10px 18px;
      border-radius: 14px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      white-space: nowrap;
      backdrop-filter: blur(16px);
      transition: all 0.2s ease;
    }}

    .tab-item:hover {{
      background: var(--glass-surface-hover);
      color: var(--text-heading);
      border-color: var(--glass-border-hover);
    }}

    .tab-item.active {{
      background: rgba(56, 189, 248, 0.15);
      border-color: var(--accent-cyan);
      color: var(--text-heading);
      box-shadow: 0 0 16px rgba(56, 189, 248, 0.2);
    }}

    .icon-svg {{
      width: 16px;
      height: 16px;
      stroke-width: 1.8;
      stroke: currentColor;
      fill: none;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}

    /* PANELS */
    .panel {{
      display: none;
      background: var(--glass-surface);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      padding: 24px;
      backdrop-filter: blur(20px);
      box-shadow: var(--glass-shadow);
    }}

    .panel.active {{
      display: block;
      animation: fadeIn 0.3s ease;
    }}

    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(4px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    .panel-top {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      padding-bottom: 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }}

    .panel-top h2 {{
      font-size: 16px;
      font-weight: 600;
      color: var(--text-heading);
      display: flex;
      align-items: center;
      gap: 9px;
    }}

    /* TABLES */
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}

    th {{
      background: rgba(15, 23, 42, 0.6);
      color: var(--text-muted);
      font-weight: 500;
      font-size: 11.5px;
      letter-spacing: 0.4px;
      padding: 12px 16px;
      text-align: left;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }}

    td {{
      padding: 13px 16px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      color: var(--text-body);
      font-family: var(--font-mono);
      font-variant-numeric: tabular-nums;
      font-weight: 400;
      font-size: 12.5px;
    }}

    tr:hover td {{
      background: rgba(56, 189, 248, 0.04);
    }}

    .tag {{
      display: inline-flex;
      align-items: center;
      padding: 3px 10px;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 500;
      font-family: var(--font-sans);
    }}

    .tag-call {{ background: rgba(74, 222, 128, 0.12); color: var(--accent-green); border: 1px solid rgba(74, 222, 128, 0.3); }}
    .tag-put {{ background: rgba(248, 113, 113, 0.12); color: var(--accent-red); border: 1px solid rgba(248, 113, 113, 0.3); }}
    .tag-scalp {{ background: rgba(56, 189, 248, 0.12); color: var(--accent-cyan); border: 1px solid rgba(56, 189, 248, 0.3); }}
    .tag-fut {{ background: rgba(192, 132, 252, 0.12); color: var(--accent-purple); border: 1px solid rgba(192, 132, 252, 0.3); }}

    /* ENGINE CARDS */
    .grid-engines {{
      display: grid;
      grid-template-cols: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
    }}

    .card-engine {{
      background: var(--glass-card);
      border: 1px solid var(--glass-border);
      border-radius: 16px;
      padding: 20px;
      backdrop-filter: blur(16px);
      transition: all 0.2s ease;
    }}

    .card-engine:hover {{
      border-color: var(--glass-border-hover);
      transform: translateY(-2px);
    }}

    .card-engine h3 {{
      font-size: 14.5px;
      font-weight: 600;
      color: var(--text-heading);
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .card-engine p {{
      font-size: 12.5px;
      color: var(--text-muted);
      line-height: 1.5;
      font-weight: 400;
    }}

    @media (max-width: 900px) {{
      .stats-row {{ grid-template-cols: repeat(2, 1fr); }}
    }}
    @media (max-width: 600px) {{
      body {{ padding: 16px; }}
      header {{ flex-direction: column; gap: 14px; text-align: center; }}
      .brand-group {{ flex-direction: column; }}
      .stats-row {{ grid-template-cols: 1fr; }}
    }}
  </style>
</head>
<body>

  <!-- CLEAN TOP BANNER -->
  <div class="sim-banner">
    <svg class="icon-svg" viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
    <span>SIMULATION MODE — PAPER TRADING ONLY (INR 5,00,000 CAPITAL POOL)</span>
  </div>

  <!-- HEADER -->
  <header>
    <div class="brand-group">
      <div class="logo-frame">
        <img src="{logo_b64}" alt="Shadow Traders" class="brand-logo" onerror="this.src='logo.jpg'">
      </div>
      <div class="brand-meta">
        <h1>SHADOW TRADERS</h1>
        <p>Institutional F&O Quant Engine & Options Swarm</p>
      </div>
    </div>
    <div class="header-actions">
      <button id="pwa-install-btn" class="btn-install" onclick="installPWA()">
        <svg class="icon-svg" viewBox="0 0 24 24"><rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/></svg>
        <span>Install App</span>
      </button>
      <div class="badge-status">
        <svg class="icon-svg" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        <span>Options Swarm Active</span>
      </div>
    </div>
  </header>

  <!-- STATS MATRIX -->
  <div class="stats-row">
    <div class="stat-box">
      <div class="stat-title">Total Portfolio Capital</div>
      <div class="stat-number" id="val-total">₹5,00,000.00</div>
      <div class="stat-desc">Initial Pool Allocation</div>
    </div>

    <div class="stat-box">
      <div class="stat-title">Available Margin</div>
      <div class="stat-number" id="val-available">₹5,00,000.00</div>
      <div class="stat-desc">Ready for Options Deployment</div>
    </div>

    <div class="stat-box">
      <div class="stat-title">Realized Intraday Return</div>
      <div class="stat-number" id="val-pnl" style="color: var(--accent-green);">+₹0.00</div>
      <div class="stat-desc">Net Realized P&L</div>
    </div>

    <div class="stat-box">
      <div class="stat-title">Brokerage Paid</div>
      <div class="stat-number" id="val-brokerage">₹0.00</div>
      <div class="stat-desc">Standard Intraday Rate</div>
    </div>
  </div>

  <!-- TAB NAVIGATION (LUXURY SVG VECTOR ICONS) -->
  <div class="tab-bar">
    <button class="tab-item active" onclick="switchTab('tab-trades', event)">
      <svg class="icon-svg" viewBox="0 0 24 24"><path d="m4 17 6-6-6-6"/><path d="M12 19h8"/></svg>
      <span>Executed Trades</span>
    </button>
    
    <button class="tab-item" onclick="switchTab('tab-engines', event)">
      <svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 2v4"/><path d="M12 18v4"/><path d="M4 12h4"/><path d="M18 12h4"/></svg>
      <span>F&O Trade Engines</span>
    </button>
    
    <button class="tab-item" onclick="switchTab('tab-patterns', event)">
      <svg class="icon-svg" viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
      <span>Pattern & VWAP Hunter</span>
    </button>
    
    <button class="tab-item" onclick="switchTab('tab-committee', event)">
      <svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>
      <span>Risk Committee</span>
    </button>
    
    <button class="tab-item" onclick="switchTab('tab-memory', event)">
      <svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><polyline points="12 6 12 12 16 14"/></svg>
      <span>Reflective Memory</span>
    </button>
  </div>

  <!-- PANEL 1: EXECUTED TRADES -->
  <div id="tab-trades" class="panel active">
    <div class="panel-top">
      <h2>
        <svg class="icon-svg" viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
        <span>Live F&O Trade Execution Log</span>
      </h2>
      <span class="tag tag-scalp">Multi-Timeframe Active (1m / 5m / 15m)</span>
    </div>
    <div style="overflow-x: auto;">
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Contract Instrument</th>
            <th>Engine Type</th>
            <th>Quantity</th>
            <th>Entry Price</th>
            <th>Exit Price</th>
            <th>Quant Score</th>
            <th>Fees</th>
            <th>Net Realized P&L</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody id="trade-log-body">
          <tr>
            <td colspan="10" style="text-align: center; color: var(--text-muted); padding: 32px 0;">
              Options Swarm active. Monitoring VWAP support bounces, Supertrend flips, and Black-Scholes greeks...
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- PANEL 2: F&O ENGINES -->
  <div id="tab-engines" class="panel">
    <div class="panel-top">
      <h2>
        <svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 2v4"/><path d="M12 18v4"/><path d="M4 12h4"/><path d="M18 12h4"/></svg>
        <span>6 Specialized High-Frequency F&O Strategy Engines</span>
      </h2>
    </div>
    <div class="grid-engines">
      <div class="card-engine">
        <h3><span class="tag tag-call">BUY_CE</span> Call Option Momentum</h3>
        <p>Executes ATM/ITM Call Option purchases upon 5m Supertrend bullish flips with VWAP support confirmation. Target: +25.0% premium gain.</p>
      </div>
      <div class="card-engine">
        <h3><span class="tag tag-put">BUY_PE</span> Put Option Breakdown</h3>
        <p>Executes ATM/ITM Put Option purchases on 5m Supertrend bearish flips and VWAP resistance rejection. Target: +25.0% premium gain.</p>
      </div>
      <div class="card-engine">
        <h3><span class="tag tag-scalp">SCALP_CE</span> 1m High-Velocity Call Scalper</h3>
        <p>1-Minute High-Frequency Scalper capturing rapid 10-15% option premium spikes during high volatility sessions.</p>
      </div>
      <div class="card-engine">
        <h3><span class="tag tag-scalp">SCALP_PE</span> 1m High-Velocity Put Scalper</h3>
        <p>1-Minute High-Frequency Put Scalper for fast intraday market drops protected by ATR trailing stop-loss bounds.</p>
      </div>
      <div class="card-engine">
        <h3><span class="tag tag-fut">BUY_FUT</span> Index & Equity Long Futures</h3>
        <p>Long Futures positioning on 15m structural candle breakouts confirmed by NIFTY relative strength outperformance (RS > 1.0).</p>
      </div>
      <div class="card-engine">
        <h3><span class="tag tag-fut">SELL_FUT</span> Index & Equity Short Futures</h3>
        <p>Short Futures positioning on structural breakdowns with NIFTY underperformance (RS < 1.0).</p>
      </div>
    </div>
  </div>

  <!-- PANEL 3: PATTERNS -->
  <div id="tab-patterns" class="panel">
    <div class="panel-top">
      <h2>
        <svg class="icon-svg" viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
        <span>12-Pattern & VWAP Quantitative Hunter</span>
      </h2>
    </div>
    <div class="grid-engines">
      <div class="card-engine">
        <h3>Double Bottom (W-Pattern)</h3>
        <p>Identifies dual support retests preceding explosive bullish option breakouts (+0.5 conviction boost).</p>
      </div>
      <div class="card-engine">
        <h3>Double Top (M-Pattern)</h3>
        <p>Identifies dual resistance rejections preceding aggressive Put option breakdowns (-0.5 conviction modifier).</p>
      </div>
      <div class="card-engine">
        <h3>Opening Range Breakout (ORB-15m)</h3>
        <p>Monitors 15m session high/low range expansions backed by institutional volume spikes.</p>
      </div>
      <div class="card-engine">
        <h3>VWAP Support Bounce</h3>
        <p>Filters price retests against Intraday VWAP line with high volume confirmation.</p>
      </div>
    </div>
  </div>

  <!-- PANEL 4: RISK COMMITTEE -->
  <div id="tab-committee" class="panel">
    <div class="panel-top">
      <h2>
        <svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>
        <span>3-Way Risk Committee & Subagent Debate Logs</span>
      </h2>
    </div>
    <table>
      <thead>
        <tr>
          <th>Symbol</th>
          <th>Bull Conviction (Scout)</th>
          <th>Bear Risk (Technician)</th>
          <th>Fact-Checker Approval (Judge)</th>
          <th>Risk Override Status</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 28px 0;">No active debate logs for current scan window. Subagent swarm evaluating market signals.</td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- PANEL 5: REFLECTIVE MEMORY -->
  <div id="tab-memory" class="panel">
    <div class="panel-top">
      <h2>
        <svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><polyline points="12 6 12 12 16 14"/></svg>
        <span>Reflective Memory & Trade Lessons</span>
      </h2>
    </div>
    <table>
      <thead>
        <tr>
          <th>Ticker Symbol</th>
          <th>Prior Trade Outcome</th>
          <th>Memory Conviction Modifier</th>
          <th>Learned Strategy Insight</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td colspan="4" style="text-align: center; color: var(--text-muted); padding: 28px 0;">Reflective memory ledger active. Lessons recorded automatically upon trade exits.</td>
        </tr>
      </tbody>
    </table>
  </div>

  <script>
    function switchTab(tabId, evt) {{
      document.querySelectorAll('.tab-item').forEach(btn => btn.classList.remove('active'));
      document.querySelectorAll('.panel').forEach(panel => panel.classList.remove('active'));
      
      if (evt && evt.currentTarget) {{
        evt.currentTarget.classList.add('active');
      }}
      document.getElementById(tabId).classList.add('active');
    }}

    async function updateDashboard() {{
      try {{
        const res = await fetch('../state/portfolio_state.json');
        if (res.ok) {{
          const state = await res.json();
          document.getElementById('val-total').innerText = '₹' + Number(state.pool_total || 500000).toLocaleString('en-IN', {{minimumFractionDigits: 2}});
          document.getElementById('val-available').innerText = '₹' + Number(state.pool_available || 500000).toLocaleString('en-IN', {{minimumFractionDigits: 2}});
          
          const pnl = Number(state.daily_pnl_inr || 0);
          const pnlElem = document.getElementById('val-pnl');
          pnlElem.innerText = (pnl >= 0 ? '+₹' : '-₹') + Math.abs(pnl).toLocaleString('en-IN', {{minimumFractionDigits: 2}});
          pnlElem.style.color = pnl >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
          
          document.getElementById('val-brokerage').innerText = '₹' + Number(state.total_brokerage_paid_inr || 0).toLocaleString('en-IN', {{minimumFractionDigits: 2}});
        }}
      }} catch(e) {{}}
    }}

    let deferredPrompt;
    window.addEventListener('beforeinstallprompt', (e) => {{
      e.preventDefault();
      deferredPrompt = e;
      const btn = document.getElementById('pwa-install-btn');
      if (btn) btn.style.display = 'inline-flex';
    }});

    async function installPWA() {{
      if (deferredPrompt) {{
        deferredPrompt.prompt();
        const {{ outcome }} = await deferredPrompt.userChoice;
        if (outcome === 'accepted') {{
          document.getElementById('pwa-install-btn').style.display = 'none';
        }}
        deferredPrompt = null;
      }}
    }}

    if ('serviceWorker' in navigator) {{
      window.addEventListener('load', () => {{
        navigator.serviceWorker.register('/sw.js?v=6').then((reg) => {{
          console.log('Shadow Traders PWA Service Worker Registered:', reg);
        }}).catch((err) => {{
          console.log('Service Worker Registration Failed:', err);
        }});
      }});
    }}

    updateDashboard();
    setInterval(updateDashboard, 5000);
  </script>
</body>
</html>
"""

    targets = [
        os.path.join(base_dir, "dashboard", "index.html"),
        os.path.join(base_dir, "public", "index.html"),
        os.path.join(base_dir, "index.html")
    ]

    for target in targets:
        with open(target, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Updated {target}")

    # Service Worker update for cache bust v6
    sw_code = """const CACHE_NAME = 'shadow-traders-v6';
const ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/logo.jpg',
  '/background.jpg',
  '/icon-192.png',
  '/icon-512.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
"""
    with open(os.path.join(base_dir, "dashboard", "sw.js"), "w", encoding="utf-8") as f:
        f.write(sw_code)
    with open(os.path.join(base_dir, "public", "sw.js"), "w", encoding="utf-8") as f:
        f.write(sw_code)

    print("Ultra-modern SaaS UI built successfully across all locations!")

if __name__ == "__main__":
    build_ultra_modern_ui()
