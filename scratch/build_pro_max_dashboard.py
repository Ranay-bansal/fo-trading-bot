import os

def build_dashboard():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SHADOW TRADERS — F&O Quant Engine & Options Swarm</title>
  <link rel="manifest" href="manifest.json">
  <meta name="theme-color" content="#0284c7">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="Shadow Traders">
  <link rel="apple-touch-icon" href="logo.jpg">
  
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700;800;900&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600;700;800&family=Outfit:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
  
  <style>
    :root {
      --bg-dark: #05070e;
      --bg-surface: #0a0e1a;
      --bg-card-shell: rgba(15, 23, 42, 0.75);
      --bg-card-core: rgba(9, 14, 26, 0.95);
      --border-cyan: rgba(0, 242, 254, 0.25);
      --border-monarch: rgba(157, 78, 221, 0.3);
      --accent-cyan: #00f2fe;
      --accent-monarch: #9d4edd;
      --accent-purple: #7c4dff;
      --accent-green: #00e676;
      --accent-red: #ff5252;
      --accent-gold: #ffd700;
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --font-title: 'Cinzel', serif;
      --font-heading: 'Outfit', sans-serif;
      --font-grotesk: 'Space Grotesk', sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    
    body {
      font-family: 'Inter', sans-serif;
      background: var(--bg-dark);
      color: var(--text-main);
      min-height: 100vh;
      padding: 24px;
      background-image: 
        radial-gradient(circle at 15% 15%, rgba(0, 242, 254, 0.07) 0%, transparent 45%),
        radial-gradient(circle at 85% 85%, rgba(157, 78, 221, 0.09) 0%, transparent 45%),
        linear-gradient(to bottom, rgba(5, 7, 14, 0.95), rgba(5, 7, 14, 0.98));
      background-attachment: fixed;
    }

    /* DISCLAIMER BANNER */
    .disclaimer-banner {
      background: linear-gradient(90deg, rgba(255, 215, 0, 0.12), rgba(0, 242, 254, 0.12));
      border: 1px solid rgba(255, 215, 0, 0.35);
      color: var(--accent-gold);
      padding: 10px 20px;
      border-radius: 12px;
      font-size: 12.5px;
      font-weight: 600;
      text-align: center;
      margin-bottom: 20px;
      letter-spacing: 0.5px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      box-shadow: 0 4px 20px rgba(255, 215, 0, 0.1);
    }

    /* HEADER */
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 28px;
      padding: 18px 28px;
      background: var(--bg-card-shell);
      border: 1px solid var(--border-cyan);
      border-radius: 20px;
      backdrop-filter: blur(24px);
      box-shadow: 0 10px 40px rgba(0, 242, 254, 0.08);
      position: relative;
    }

    .brand-container {
      display: flex;
      align-items: center;
      gap: 18px;
    }

    .logo-wrapper {
      position: relative;
      width: 60px;
      height: 60px;
      border-radius: 16px;
      padding: 2px;
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-monarch));
      box-shadow: 0 0 25px rgba(0, 242, 254, 0.4);
    }

    .shadow-logo {
      width: 100%;
      height: 100%;
      border-radius: 14px;
      object-fit: cover;
      display: block;
      background: #000;
    }

    .brand-text h1 {
      font-family: var(--font-title);
      font-size: 28px;
      font-weight: 900;
      letter-spacing: 1.5px;
      background: linear-gradient(135deg, #ffffff 30%, var(--accent-cyan) 75%, var(--accent-monarch) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      text-shadow: 0 0 35px rgba(0, 242, 254, 0.35);
    }

    .brand-text p {
      font-size: 13px;
      color: var(--text-muted);
      letter-spacing: 0.6px;
      font-family: var(--font-grotesk);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .arise-badge {
      background: linear-gradient(135deg, rgba(0, 242, 254, 0.15), rgba(157, 78, 221, 0.2));
      border: 1px solid var(--accent-cyan);
      color: var(--accent-cyan);
      padding: 8px 18px;
      border-radius: 24px;
      font-family: var(--font-heading);
      font-size: 12.5px;
      font-weight: 700;
      letter-spacing: 1px;
      text-shadow: 0 0 10px rgba(0, 242, 254, 0.5);
    }

    .install-pwa-btn {
      background: linear-gradient(135deg, #00f2fe, #7c4dff);
      color: #05070e;
      font-weight: 800;
      padding: 10px 22px;
      border-radius: 24px;
      border: none;
      cursor: pointer;
      font-family: var(--font-heading);
      font-size: 13px;
      box-shadow: 0 0 20px rgba(0, 242, 254, 0.5);
      transition: all 0.3s cubic-bezier(0.32, 0.72, 0, 1);
    }

    .install-pwa-btn:hover {
      transform: translateY(-2px) scale(1.02);
      box-shadow: 0 0 30px rgba(0, 242, 254, 0.8);
    }

    /* STATS GRID (DOPPELRAND ARCHITECTURE) */
    .stats-grid {
      display: grid;
      grid-template-cols: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }

    .stat-shell {
      background: var(--bg-card-shell);
      border: 1px solid var(--border-cyan);
      border-radius: 18px;
      padding: 2px;
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
      transition: transform 0.3s ease, border-color 0.3s ease;
    }

    .stat-shell:hover {
      transform: translateY(-3px);
      border-color: var(--accent-cyan);
    }

    .stat-core {
      background: var(--bg-card-core);
      border-radius: 16px;
      padding: 20px;
    }

    .stat-label {
      font-size: 12px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 8px;
    }

    .stat-value {
      font-family: var(--font-mono);
      font-size: 24px;
      font-weight: 800;
      color: #fff;
      letter-spacing: -0.5px;
      font-variant-numeric: tabular-nums;
    }

    .stat-subtext {
      font-size: 11.5px;
      color: var(--text-muted);
      margin-top: 6px;
    }

    /* TAB NAVIGATION */
    .tab-nav {
      display: flex;
      gap: 10px;
      margin-bottom: 24px;
      overflow-x: auto;
      padding-bottom: 6px;
    }

    .tab-btn {
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid rgba(255, 255, 255, 0.08);
      color: var(--text-muted);
      padding: 12px 22px;
      border-radius: 14px;
      font-family: var(--font-heading);
      font-size: 13.5px;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.3s ease;
    }

    .tab-btn:hover {
      background: rgba(0, 242, 254, 0.1);
      color: #fff;
      border-color: var(--border-cyan);
    }

    .tab-btn.active {
      background: linear-gradient(135deg, rgba(0, 242, 254, 0.2), rgba(157, 78, 221, 0.25));
      border: 1px solid var(--accent-cyan);
      color: #fff;
      box-shadow: 0 0 20px rgba(0, 242, 254, 0.25);
    }

    /* PANELS */
    .panel {
      display: none;
      background: var(--bg-card-shell);
      border: 1px solid var(--border-cyan);
      border-radius: 20px;
      padding: 24px;
      backdrop-filter: blur(20px);
      box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    }

    .panel.active {
      display: block;
      animation: fadeIn 0.4s ease-out;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      padding-bottom: 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }

    .panel-header h2 {
      font-family: var(--font-heading);
      font-size: 20px;
      font-weight: 700;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    /* TABLES */
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }

    th {
      background: rgba(15, 23, 42, 0.8);
      color: var(--text-muted);
      font-weight: 600;
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 1px;
      padding: 14px 16px;
      text-align: left;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    td {
      padding: 14px 16px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      color: var(--text-main);
      font-family: var(--font-mono);
      font-variant-numeric: tabular-nums;
    }

    tr:hover td {
      background: rgba(0, 242, 254, 0.03);
    }

    .badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 700;
      font-family: var(--font-heading);
      letter-spacing: 0.5px;
    }

    .badge-buy-ce { background: rgba(0, 230, 118, 0.15); color: var(--accent-green); border: 1px solid var(--accent-green); }
    .badge-buy-pe { background: rgba(255, 82, 82, 0.15); color: var(--accent-red); border: 1px solid var(--accent-red); }
    .badge-scalp { background: rgba(0, 242, 254, 0.15); color: var(--accent-cyan); border: 1px solid var(--accent-cyan); }
    .badge-fut { background: rgba(157, 78, 221, 0.2); color: var(--accent-monarch); border: 1px solid var(--accent-monarch); }

    /* ENGINE CARDS GRID */
    .engine-grid {
      display: grid;
      grid-template-cols: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
    }

    .engine-card {
      background: var(--bg-card-core);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 16px;
      padding: 20px;
      transition: all 0.3s ease;
    }

    .engine-card:hover {
      border-color: var(--accent-cyan);
      box-shadow: 0 0 25px rgba(0, 242, 254, 0.15);
    }

    .engine-card h3 {
      font-family: var(--font-heading);
      font-size: 16px;
      font-weight: 700;
      color: var(--accent-cyan);
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .engine-card p {
      font-size: 12.5px;
      color: var(--text-muted);
      line-height: 1.5;
    }

    @media (max-width: 768px) {
      body { padding: 12px; }
      header { flex-direction: column; gap: 14px; text-align: center; }
      .brand-container { flex-direction: column; }
      .stats-grid { grid-template-cols: 1fr; }
    }
  </style>
</head>
<body>

  <!-- DISCLAIMER BANNER -->
  <div class="disclaimer-banner">
    <span>⚠️ SIMULATION MODE — PAPER TRADING ONLY (INR 5,00,000 CAPITAL POOL)</span>
    <span>• FLAT ₹20 ZERODHA BROKERAGE DEDUCTED</span>
  </div>

  <!-- HEADER -->
  <header>
    <div class="brand-container">
      <div class="logo-wrapper">
        <img src="logo.jpg" alt="Shadow Monarch" class="shadow-logo" onerror="this.src='https://raw.githubusercontent.com/Ranay-bansal/fo-trading-bot/main/dashboard/logo.jpg'">
      </div>
      <div class="brand-text">
        <h1>SHADOW TRADERS</h1>
        <p>⚡ F&O High-Frequency Quant Engine & Options Swarm</p>
      </div>
    </div>
    <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
      <button id="pwa-install-btn" class="install-pwa-btn" onclick="installPWA()">
        ⚡ INSTALL SHADOW APP
      </button>
      <div class="arise-badge">ARISE — ⚡ OPTIONS SWARM ACTIVE</div>
    </div>
  </header>

  <!-- STATS MATRIX (DOPPELRAND) -->
  <div class="stats-grid">
    <div class="stat-shell">
      <div class="stat-core">
        <div class="stat-label">Total Portfolio Pool</div>
        <div class="stat-value" id="val-total">₹5,00,000.00</div>
        <div class="stat-subtext">Initial Pool Allocation</div>
      </div>
    </div>

    <div class="stat-shell">
      <div class="stat-core">
        <div class="stat-label">Available Margin</div>
        <div class="stat-value" id="val-available">₹5,00,000.00</div>
        <div class="stat-subtext">Ready for Options Swarm</div>
      </div>
    </div>

    <div class="stat-shell">
      <div class="stat-core">
        <div class="stat-label">Realized Intraday P&L</div>
        <div class="stat-value" id="val-pnl" style="color: var(--accent-green);">+₹0.00</div>
        <div class="stat-subtext">Net Realized Return</div>
      </div>
    </div>

    <div class="stat-shell">
      <div class="stat-core">
        <div class="stat-label">Zerodha Brokerage Paid</div>
        <div class="stat-value" id="val-brokerage">₹0.00</div>
        <div class="stat-subtext">Flat ₹20 Rate Model</div>
      </div>
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
            <th>Zerodha Fees</th>
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
    function switchTab(tabId, evt) {
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      document.querySelectorAll('.panel').forEach(panel => panel.classList.remove('active'));
      
      if (evt && evt.target) {
        evt.target.classList.add('active');
      }
      document.getElementById(tabId).classList.add('active');
    }

    async function updateDashboard() {
      try {
        const res = await fetch('../state/portfolio_state.json');
        if (res.ok) {
          const state = await res.json();
          document.getElementById('val-total').innerText = '₹' + Number(state.pool_total || 500000).toLocaleString('en-IN', {minimumFractionDigits: 2});
          document.getElementById('val-available').innerText = '₹' + Number(state.pool_available || 500000).toLocaleString('en-IN', {minimumFractionDigits: 2});
          
          const pnl = Number(state.daily_pnl_inr || 0);
          const pnlElem = document.getElementById('val-pnl');
          pnlElem.innerText = (pnl >= 0 ? '+₹' : '-₹') + Math.abs(pnl).toLocaleString('en-IN', {minimumFractionDigits: 2});
          pnlElem.style.color = pnl >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
          
          document.getElementById('val-brokerage').innerText = '₹' + Number(state.total_brokerage_paid_inr || 0).toLocaleString('en-IN', {minimumFractionDigits: 2});
        }
      } catch(e) {}
    }

    let deferredPrompt;
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPrompt = e;
      const btn = document.getElementById('pwa-install-btn');
      if (btn) btn.style.display = 'inline-block';
    });

    async function installPWA() {
      if (deferredPrompt) {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        if (outcome === 'accepted') {
          document.getElementById('pwa-install-btn').style.display = 'none';
        }
        deferredPrompt = null;
      }
    }

    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').then((reg) => {
          console.log('Shadow Traders PWA Service Worker Registered:', reg);
        }).catch((err) => {
          console.log('Service Worker Registration Failed:', err);
        });
      });
    }

    updateDashboard();
    setInterval(updateDashboard, 5000);
  </script>
</body>
</html>
"""

    dashboard_file = r"c:\Users\RANAY\Desktop\FO TRADING BOT\dashboard\index.html"
    with open(dashboard_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Built high-end pro max dashboard index.html successfully!")

if __name__ == "__main__":
    build_dashboard()
