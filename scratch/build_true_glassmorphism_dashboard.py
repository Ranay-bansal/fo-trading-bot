import os
import shutil

def build_glassmorphism_ui():
    base_dir = r"c:\Users\RANAY\Desktop\FO TRADING BOT"
    logo_b64_path = os.path.join(base_dir, "scratch", "logo_b64.txt")
    
    with open(logo_b64_path, "r") as f:
        logo_b64 = f.read().strip()

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SHADOW TRADERS — F&O Glassmorphism Quant Terminal</title>
  <link rel="manifest" href="manifest.json">
  <meta name="theme-color" content="#0284c7">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="Shadow Traders">
  <link rel="apple-touch-icon" href="logo.jpg">
  
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700;800&family=Outfit:wght@600;700;800;900&family=Space+Grotesk:wght@600;700&display=swap" rel="stylesheet">
  
  <style>
    :root {{
      /* TRUE FROSTED GLASSMORPHISM TO SHOW WALLPAPER */
      --glass-bg: rgba(10, 16, 30, 0.48);
      --glass-bg-hover: rgba(15, 23, 42, 0.65);
      --glass-card-core: rgba(15, 23, 42, 0.55);
      --glass-border: rgba(255, 255, 255, 0.28);
      --glass-border-bright: rgba(0, 242, 254, 0.5);
      --glass-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.45), inset 0 1px 1px 0 rgba(255, 255, 255, 0.25);
      
      --accent-cyan: #00f2fe;
      --accent-blue: #38bdf8;
      --accent-purple: #a855f7;
      --accent-green: #22c55e;
      --accent-red: #ef4444;
      --accent-gold: #fbbf24;
      
      --text-white: #ffffff;
      --text-main: #f1f5f9;
      --text-muted: #cbd5e1;
      --text-subtle: #94a3b8;
      
      --font-title: 'Cinzel', serif;
      --font-body: 'Plus Jakarta Sans', sans-serif;
      --font-heading: 'Outfit', sans-serif;
      --font-grotesk: 'Space Grotesk', sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    
    body {{
      font-family: var(--font-body);
      color: var(--text-main);
      min-height: 100vh;
      padding: 24px;
      background-image: url('background.jpg');
      background-size: cover;
      background-position: center;
      background-repeat: no-repeat;
      background-attachment: fixed;
      position: relative;
    }}

    /* SUBTLE WALLPAPER PROTECTION OVERLAY */
    body::before {{
      content: '';
      position: fixed;
      inset: 0;
      background: rgba(5, 8, 16, 0.25);
      z-index: -1;
      pointer-events: none;
    }}

    /* DISCLAIMER BANNER (TRANSLUCENT GLASS) */
    .disclaimer-banner {{
      background: rgba(15, 23, 42, 0.55);
      border: 1px solid rgba(251, 191, 36, 0.5);
      color: var(--accent-gold);
      padding: 10px 24px;
      border-radius: 16px;
      font-size: 13px;
      font-weight: 700;
      text-align: center;
      margin-bottom: 22px;
      letter-spacing: 0.5px;
      backdrop-filter: blur(14px) saturate(180%);
      box-shadow: var(--glass-shadow);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }}

    /* HEADER (FROSTED GLASSMORPHISM) */
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 28px;
      padding: 18px 28px;
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 24px;
      backdrop-filter: blur(16px) saturate(180%);
      box-shadow: var(--glass-shadow);
    }}

    .brand-container {{
      display: flex;
      align-items: center;
      gap: 18px;
    }}

    .logo-wrapper {{
      width: 62px;
      height: 62px;
      border-radius: 18px;
      padding: 2px;
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
      box-shadow: 0 0 20px rgba(0, 242, 254, 0.4);
    }}

    .shadow-logo {{
      width: 100%;
      height: 100%;
      border-radius: 16px;
      object-fit: cover;
      display: block;
      background: #000;
    }}

    .brand-text h1 {{
      font-family: var(--font-title);
      font-size: 29px;
      font-weight: 900;
      letter-spacing: 1.5px;
      background: linear-gradient(135deg, #ffffff 30%, var(--accent-cyan) 75%, var(--accent-purple) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      text-shadow: 0 0 30px rgba(0, 242, 254, 0.3);
    }}

    .brand-text p {{
      font-size: 13px;
      color: var(--text-muted);
      letter-spacing: 0.6px;
      font-family: var(--font-grotesk);
      font-weight: 600;
    }}

    .arise-badge {{
      background: rgba(0, 242, 254, 0.15);
      border: 1px solid var(--accent-cyan);
      color: var(--accent-cyan);
      padding: 8px 18px;
      border-radius: 24px;
      font-family: var(--font-heading);
      font-size: 12.5px;
      font-weight: 700;
      letter-spacing: 0.8px;
      box-shadow: 0 0 15px rgba(0, 242, 254, 0.2);
    }}

    .install-pwa-btn {{
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
      color: #05070e;
      font-weight: 800;
      padding: 10px 22px;
      border-radius: 24px;
      border: none;
      cursor: pointer;
      font-family: var(--font-heading);
      font-size: 13px;
      box-shadow: 0 0 20px rgba(0, 242, 254, 0.4);
      transition: all 0.3s cubic-bezier(0.32, 0.72, 0, 1);
    }}

    .install-pwa-btn:hover {{
      transform: translateY(-2px) scale(1.02);
      box-shadow: 0 0 30px rgba(0, 242, 254, 0.7);
    }}

    /* STATS MATRIX (FROSTED GLASS) */
    .stats-grid {{
      display: grid;
      grid-template-cols: repeat(auto-fit, minmax(220px, 1fr));
      gap: 18px;
      margin-bottom: 28px;
    }}

    .stat-card {{
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 22px;
      padding: 22px;
      backdrop-filter: blur(16px) saturate(180%);
      box-shadow: var(--glass-shadow);
      transition: transform 0.3s ease, border-color 0.3s ease;
    }}

    .stat-card:hover {{
      transform: translateY(-3px);
      border-color: var(--accent-cyan);
      background: var(--glass-bg-hover);
    }}

    .stat-label {{
      font-size: 12px;
      font-weight: 700;
      color: var(--text-subtle);
      text-transform: uppercase;
      letter-spacing: 0.8px;
      margin-bottom: 8px;
    }}

    .stat-value {{
      font-family: var(--font-mono);
      font-size: 25px;
      font-weight: 800;
      color: var(--text-white);
      letter-spacing: -0.5px;
      font-variant-numeric: tabular-nums;
    }}

    .stat-subtext {{
      font-size: 11.5px;
      color: var(--text-subtle);
      margin-top: 6px;
      font-weight: 500;
    }}

    /* TAB NAVIGATION */
    .tab-nav {{
      display: flex;
      gap: 12px;
      margin-bottom: 24px;
      overflow-x: auto;
      padding-bottom: 6px;
    }}

    .tab-btn {{
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      color: var(--text-muted);
      padding: 12px 24px;
      border-radius: 16px;
      font-family: var(--font-heading);
      font-size: 13.5px;
      font-weight: 700;
      cursor: pointer;
      white-space: nowrap;
      backdrop-filter: blur(16px);
      box-shadow: var(--glass-shadow);
      transition: all 0.3s ease;
    }}

    .tab-btn:hover {{
      background: var(--glass-bg-hover);
      color: var(--text-white);
      border-color: var(--glass-border-bright);
    }}

    .tab-btn.active {{
      background: linear-gradient(135deg, rgba(0, 242, 254, 0.25), rgba(168, 85, 247, 0.3));
      border: 1px solid var(--accent-cyan);
      color: var(--text-white);
      box-shadow: 0 0 25px rgba(0, 242, 254, 0.35);
    }}

    /* PANELS (FROSTED GLASSMORPHISM) */
    .panel {{
      display: none;
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 24px;
      padding: 26px;
      backdrop-filter: blur(16px) saturate(180%);
      box-shadow: var(--glass-shadow);
    }}

    .panel.active {{
      display: block;
      animation: fadeIn 0.4s ease-out;
    }}

    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(8px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    .panel-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      padding-bottom: 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }}

    .panel-header h2 {{
      font-family: var(--font-heading);
      font-size: 20px;
      font-weight: 800;
      color: var(--text-white);
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    /* TABLES */
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}

    th {{
      background: rgba(15, 23, 42, 0.6);
      color: var(--text-subtle);
      font-weight: 700;
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 1px;
      padding: 14px 16px;
      text-align: left;
      border-bottom: 1px solid rgba(255, 255, 255, 0.12);
    }}

    td {{
      padding: 14px 16px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      color: var(--text-main);
      font-family: var(--font-mono);
      font-variant-numeric: tabular-nums;
      font-weight: 600;
    }}

    tr:hover td {{
      background: rgba(0, 242, 254, 0.05);
    }}

    .badge {{
      display: inline-block;
      padding: 4px 12px;
      border-radius: 10px;
      font-size: 11px;
      font-weight: 800;
      font-family: var(--font-heading);
      letter-spacing: 0.5px;
    }}

    .badge-buy-ce {{ background: rgba(34, 197, 94, 0.2); color: var(--accent-green); border: 1px solid var(--accent-green); }}
    .badge-buy-pe {{ background: rgba(239, 68, 68, 0.2); color: var(--accent-red); border: 1px solid var(--accent-red); }}
    .badge-scalp {{ background: rgba(0, 242, 254, 0.2); color: var(--accent-cyan); border: 1px solid var(--accent-cyan); }}
    .badge-fut {{ background: rgba(168, 85, 247, 0.2); color: var(--accent-purple); border: 1px solid var(--accent-purple); }}

    /* ENGINE CARDS GRID */
    .engine-grid {{
      display: grid;
      grid-template-cols: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
    }}

    .engine-card {{
      background: var(--glass-card-core);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      padding: 22px;
      backdrop-filter: blur(12px);
      box-shadow: var(--glass-shadow);
      transition: all 0.3s ease;
    }}

    .engine-card:hover {{
      transform: translateY(-2px);
      border-color: var(--accent-cyan);
      box-shadow: 0 0 25px rgba(0, 242, 254, 0.2);
    }}

    .engine-card h3 {{
      font-family: var(--font-heading);
      font-size: 16.5px;
      font-weight: 800;
      color: var(--accent-cyan);
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .engine-card p {{
      font-size: 13px;
      color: var(--text-muted);
      line-height: 1.5;
      font-weight: 500;
    }}

    @media (max-width: 768px) {{
      body {{ padding: 12px; }}
      header {{ flex-direction: column; gap: 14px; text-align: center; }}
      .brand-container {{ flex-direction: column; }}
      .stats-grid {{ grid-template-cols: 1fr; }}
    }}
  </style>
</head>
<body>

  <!-- CLEAN DISCLAIMER BANNER -->
  <div class="disclaimer-banner">
    <span>⚠️ SIMULATION MODE — PAPER TRADING ONLY (INR 5,00,000 CAPITAL POOL)</span>
  </div>

  <!-- HEADER -->
  <header>
    <div class="brand-container">
      <div class="logo-wrapper">
        <img src="{logo_b64}" alt="Shadow Monarch" class="shadow-logo" onerror="this.src='logo.jpg'">
      </div>
      <div class="brand-text">
        <h1>SHADOW TRADERS</h1>
        <p>⚡ F&O Quant Engine & Options Swarm</p>
      </div>
    </div>
    <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
      <button id="pwa-install-btn" class="install-pwa-btn" onclick="installPWA()">
        ⚡ INSTALL SHADOW APP
      </button>
      <div class="arise-badge">ARISE — ⚡ OPTIONS SWARM ACTIVE</div>
    </div>
  </header>

  <!-- STATS MATRIX (FROSTED GLASS) -->
  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-label">Total Portfolio Pool</div>
      <div class="stat-value" id="val-total">₹5,00,000.00</div>
      <div class="stat-subtext">Initial Capital Allocation</div>
    </div>

    <div class="stat-card">
      <div class="stat-label">Available Margin</div>
      <div class="stat-value" id="val-available">₹5,00,000.00</div>
      <div class="stat-subtext">Ready for Options Swarm</div>
    </div>

    <div class="stat-card">
      <div class="stat-label">Realized Intraday P&L</div>
      <div class="stat-value" id="val-pnl" style="color: var(--accent-green);">+₹0.00</div>
      <div class="stat-subtext">Net Realized Return</div>
    </div>

    <div class="stat-card">
      <div class="stat-label">Transaction Fee Costs</div>
      <div class="stat-value" id="val-brokerage">₹0.00</div>
      <div class="stat-subtext">Statutory Deductions</div>
    </div>
  </div>

  <!-- TAB NAVIGATION -->
  <div class="tab-nav">
    <button class="tab-btn active" onclick="switchTab('tab-trades', event)">⚔️ Executed Trades Log</button>
    <button class="tab-btn" onclick="switchTab('tab-engines', event)">🎯 F&O Trade Engines</button>
    <button class="tab-btn" onclick="switchTab('tab-patterns', event)">📊 12-Pattern & VWAP Hunter</button>
    <button class="tab-btn" onclick="switchTab('tab-committee', event)">🏛️ 3-Way Risk Committee</button>
    <button class="tab-btn" onclick="switchTab('tab-memory', event)">🔮 Reflective Memory</button>
  </div>

  <!-- PANEL 1: EXECUTED TRADES LOG -->
  <div id="tab-trades" class="panel active">
    <div class="panel-header">
      <h2>⚔️ Live F&O Trade Execution Log (Options & Futures)</h2>
      <span class="badge badge-scalp">1m / 5m / 15m Multi-TF Active</span>
    </div>
    <div style="overflow-x: auto;">
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Instrument / Contract</th>
            <th>Strategy Type</th>
            <th>Quantity</th>
            <th>Entry Price</th>
            <th>Exit Price</th>
            <th>Quant Score</th>
            <th>Transaction Costs</th>
            <th>Net Realized P&L</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody id="trade-log-body">
          <tr>
            <td colspan="10" style="text-align: center; color: var(--text-muted); padding: 30px;">
              ⚡ Options Swarm active. Monitoring 1m/5m VWAP bounces, Supertrend trend flips, and Black-Scholes strike selections...
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- PANEL 2: F&O TRADE ENGINES -->
  <div id="tab-engines" class="panel">
    <div class="panel-header">
      <h2>🎯 6 Specialized High-Frequency F&O Trade Engines</h2>
    </div>
    <div class="engine-grid">
      <div class="engine-card">
        <h3><span class="badge badge-buy-ce">BUY_CE</span> Call Option Momentum</h3>
        <p>Target: ATM/ITM Call Option Buy on 5m Supertrend Bullish Flip + VWAP Support Bounce. Profit Target: +25.0% Premium gain.</p>
      </div>
      <div class="engine-card">
        <h3><span class="badge badge-buy-pe">BUY_PE</span> Put Option Breakdown</h3>
        <p>Target: ATM/ITM Put Option Buy on 5m Supertrend Bearish Flip + VWAP Resistance Rejection. Profit Target: +25.0% Premium gain.</p>
      </div>
      <div class="engine-card">
        <h3><span class="badge badge-scalp">SCALP_CE</span> 1m High-Velocity Call Scalp</h3>
        <p>1-Minute High-Frequency Scalper capturing quick 10-15% option premium spikes during opening volatility.</p>
      </div>
      <div class="engine-card">
        <h3><span class="badge badge-scalp">SCALP_PE</span> 1m High-Velocity Put Scalp</h3>
        <p>1-Minute High-Frequency Put Scalper for fast intraday breakdowns with tight ATR trailing stop-loss protection.</p>
      </div>
      <div class="engine-card">
        <h3><span class="badge badge-fut">BUY_FUT</span> Index & Equity Long Futures</h3>
        <p>Long Futures position sizing on strong 15m structural breakouts with NIFTY outperformance (RS > 1.0).</p>
      </div>
      <div class="engine-card">
        <h3><span class="badge badge-fut">SELL_FUT</span> Index & Equity Short Futures</h3>
        <p>Short Futures positioning on structural breakdowns with NIFTY underperformance (RS < 1.0).</p>
      </div>
    </div>
  </div>

  <!-- PANEL 3: 12-PATTERN & VWAP HUNTER -->
  <div id="tab-patterns" class="panel">
    <div class="panel-header">
      <h2>📊 12-Pattern & VWAP Quantitative Hunter</h2>
    </div>
    <div class="engine-grid">
      <div class="engine-card">
        <h3>Double Bottom (W-Pattern)</h3>
        <p>Dual support test preceding explosive bullish option breakouts (+0.5 Score).</p>
      </div>
      <div class="engine-card">
        <h3>Double Top (M-Pattern)</h3>
        <p>Dual ceiling rejection preceding aggressive Put option breakdowns (-0.5 Score).</p>
      </div>
      <div class="engine-card">
        <h3>Opening Range Breakout (ORB-15m)</h3>
        <p>Monitors 15m session high/low breakouts with volume expansion.</p>
      </div>
      <div class="engine-card">
        <h3>VWAP Support Bounce</h3>
        <p>Price retests Intraday VWAP line with high volume confirmation.</p>
      </div>
    </div>
  </div>

  <!-- PANEL 4: 3-WAY RISK COMMITTEE -->
  <div id="tab-committee" class="panel">
    <div class="panel-header">
      <h2>🏛️ 3-Way Risk Committee & Subagent Debate Logs</h2>
    </div>
    <table>
      <thead>
        <tr>
          <th>Symbol</th>
          <th>Bull Conviction (Scout)</th>
          <th>Bear Risk (Technician)</th>
          <th>Fact-Checker Status (Judge)</th>
          <th>Risk Committee Override</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 24px;">No active debate logs for current scan window. Subagent swarm evaluating market signals.</td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- PANEL 5: REFLECTIVE MEMORY -->
  <div id="tab-memory" class="panel">
    <div class="panel-header">
      <h2>🔮 Reflective Memory & Trade Lessons</h2>
    </div>
    <table>
      <thead>
        <tr>
          <th>Ticker Symbol</th>
          <th>Prior Outcome</th>
          <th>Memory Modifier</th>
          <th>Learned Lesson</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td colspan="4" style="text-align: center; color: var(--text-muted); padding: 24px;">Reflective memory ledger active. Lessons recorded automatically upon trade exits.</td>
        </tr>
      </tbody>
    </table>
  </div>

  <script>
    function switchTab(tabId, evt) {{
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      document.querySelectorAll('.panel').forEach(panel => panel.classList.remove('active'));
      
      if (evt && evt.target) {{
        evt.target.classList.add('active');
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
      if (btn) btn.style.display = 'inline-block';
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
        navigator.serviceWorker.register('/sw.js').then((reg) => {{
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

    with open(os.path.join(base_dir, "dashboard", "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)
        
    with open(os.path.join(base_dir, "public", "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

    print("Built True Frosted Glassmorphism UI successfully!")

if __name__ == "__main__":
    build_glassmorphism_ui()
