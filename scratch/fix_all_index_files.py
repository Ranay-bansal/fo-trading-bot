import os
import shutil

def fix_all():
    base_dir = r"c:\Users\RANAY\Desktop\FO TRADING BOT"
    bg_b64_path = os.path.join(base_dir, "scratch", "bg_b64.txt")
    logo_b64_path = os.path.join(base_dir, "scratch", "logo_b64.txt")
    
    with open(bg_b64_path, "r") as f:
        bg_b64 = f.read().strip()
        
    with open(logo_b64_path, "r") as f:
        logo_b64 = f.read().strip()

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <title>SHADOW TRADERS — F&O Quant Terminal</title>
  <link rel="manifest" href="manifest.json?v=4">
  <meta name="theme-color" content="#090D16">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="Shadow Traders">
  <link rel="apple-touch-icon" href="logo.jpg">
  
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  
  <style>
    :root {{
      --glass-bg: rgba(15, 23, 42, 0.75);
      --glass-bg-hover: rgba(30, 41, 59, 0.85);
      --glass-card-core: rgba(15, 23, 42, 0.85);
      --glass-border: rgba(255, 255, 255, 0.08);
      --glass-border-bright: rgba(56, 189, 248, 0.35);
      --glass-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
      
      --accent-cyan: #38bdf8;
      --accent-blue: #0284c7;
      --accent-purple: #a855f7;
      --accent-green: #10b981;
      --accent-red: #f43f5e;
      --accent-gold: #f59e0b;
      
      --text-white: #f8fafc;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-subtle: #64748b;
      
      --font-body: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
      --font-heading: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    
    body {{
      font-family: var(--font-body);
      color: var(--text-main);
      min-height: 100vh;
      padding: 24px;
      background-color: #090D16;
      background-image: 
        radial-gradient(at 50% 0%, rgba(30, 41, 59, 0.4) 0px, transparent 60%),
        radial-gradient(at 100% 0%, rgba(15, 23, 42, 0.6) 0px, transparent 50%);
      background-attachment: fixed;
      position: relative;
    }}

    .disclaimer-banner {{
      background: rgba(245, 158, 11, 0.06);
      border: 1px solid rgba(245, 158, 11, 0.25);
      color: #FCD34D;
      padding: 10px 20px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 600;
      text-align: center;
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }}

    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      padding: 16px 24px;
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 16px;
      backdrop-filter: blur(16px);
      box-shadow: var(--glass-shadow);
    }}

    .brand-container {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}

    .logo-wrapper {{
      width: 44px;
      height: 44px;
      border-radius: 10px;
      border: 1px solid rgba(255, 255, 255, 0.12);
      overflow: hidden;
    }}

    .shadow-logo {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }}

    .brand-text h1 {{
      font-family: var(--font-heading);
      font-size: 20px;
      font-weight: 800;
      letter-spacing: 0.5px;
      color: var(--text-white);
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .brand-text p {{
      font-size: 11px;
      color: var(--text-muted);
      letter-spacing: 0.5px;
      font-weight: 600;
      text-transform: uppercase;
    }}

    .arise-badge {{
      background: rgba(16, 185, 129, 0.08);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: var(--accent-green);
      padding: 6px 14px;
      border-radius: 999px;
      font-size: 11.5px;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}

    .install-pwa-btn {{
      background: rgba(56, 189, 248, 0.15);
      border: 1px solid rgba(56, 189, 248, 0.35);
      color: var(--accent-cyan);
      font-weight: 600;
      padding: 6px 14px;
      border-radius: 999px;
      cursor: pointer;
      font-size: 11.5px;
      transition: all 0.2s ease;
    }}

    .install-pwa-btn:hover {{
      background: rgba(56, 189, 248, 0.25);
    }}

    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}

    .stat-card {{
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 16px;
      padding: 20px 22px;
      backdrop-filter: blur(16px);
      box-shadow: var(--glass-shadow);
      transition: border-color 0.2s ease;
    }}

    .stat-card:hover {{
      border-color: rgba(255, 255, 255, 0.14);
    }}

    .stat-label {{
      font-size: 11px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.6px;
      margin-bottom: 6px;
    }}

    .stat-value {{
      font-family: var(--font-mono);
      font-size: 24px;
      font-weight: 700;
      color: var(--text-white);
      font-variant-numeric: tabular-nums;
    }}

    .stat-subtext {{
      font-size: 11px;
      color: var(--text-subtle);
      margin-top: 4px;
      font-weight: 500;
    }}

    .tab-nav {{
      display: inline-flex;
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid var(--glass-border);
      padding: 4px;
      border-radius: 999px;
      gap: 4px;
      margin-bottom: 24px;
      overflow-x: auto;
      max-width: 100%;
    }}

    .tab-btn {{
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      padding: 8px 18px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.15s ease;
    }}

    .tab-btn:hover {{
      color: var(--text-white);
      background: rgba(255, 255, 255, 0.05);
    }}

    .tab-btn.active {{
      background: #1E293B;
      border: 1px solid rgba(56, 189, 248, 0.35);
      color: var(--text-white);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }}

    .panel {{
      display: none;
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 16px;
      padding: 24px;
      backdrop-filter: blur(16px);
      box-shadow: var(--glass-shadow);
    }}

    .panel.active {{
      display: block;
      animation: fadeIn 0.25s ease-out;
    }}

    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(4px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    .panel-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 18px;
      padding-bottom: 12px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }}

    .panel-header h2 {{
      font-family: var(--font-heading);
      font-size: 15px;
      font-weight: 700;
      color: var(--text-white);
      letter-spacing: 0.3px;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      white-space: nowrap;
    }}

    th {{
      background: rgba(15, 23, 42, 0.6);
      color: var(--text-muted);
      font-weight: 600;
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 0.6px;
      padding: 12px 14px;
      text-align: left;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }}

    td {{
      padding: 12px 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      color: var(--text-main);
      font-family: var(--font-mono);
      font-variant-numeric: tabular-nums;
      font-weight: 500;
      font-size: 12.5px;
    }}

    tr:hover td {{
      background: rgba(255, 255, 255, 0.02);
    }}

    .badge {{
      display: inline-block;
      padding: 3px 10px;
      border-radius: 999px;
      font-size: 10.5px;
      font-weight: 700;
      font-family: var(--font-body);
      letter-spacing: 0.4px;
      text-transform: uppercase;
    }}

    .badge-buy-ce {{ background: rgba(16, 185, 129, 0.15); color: var(--accent-green); border: 1px solid rgba(16, 185, 129, 0.3); }}
    .badge-buy-pe {{ background: rgba(244, 63, 94, 0.15); color: var(--accent-red); border: 1px solid rgba(244, 63, 94, 0.3); }}
    .badge-scalp {{ background: rgba(56, 189, 248, 0.15); color: var(--accent-cyan); border: 1px solid rgba(56, 189, 248, 0.3); }}
    .badge-fut {{ background: rgba(168, 85, 247, 0.15); color: var(--accent-purple); border: 1px solid rgba(168, 85, 247, 0.3); }}

    .engine-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
    }}

    .engine-card {{
      background: var(--glass-card-core);
      border: 1px solid var(--glass-border);
      border-radius: 12px;
      padding: 18px 20px;
      transition: border-color 0.2s ease;
    }}

    .engine-card:hover {{
      border-color: rgba(56, 189, 248, 0.3);
    }}

    .engine-card h3 {{
      font-family: var(--font-heading);
      font-size: 14px;
      font-weight: 700;
      color: var(--accent-cyan);
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .engine-card p {{
      font-size: 12px;
      color: var(--text-muted);
      line-height: 1.55;
    }}

    @media (max-width: 768px) {{
      body {{ padding: 12px; }}
      header {{ flex-direction: column; gap: 14px; text-align: center; }}
      .brand-container {{ flex-direction: column; }}
      .stats-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>

  <!-- CLEAN DISCLAIMER BANNER -->
  <div class="disclaimer-banner">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style="flex-shrink: 0;">
      <circle cx="12" cy="12" r="10"></circle>
      <line x1="12" y1="8" x2="12" y2="12"></line>
      <line x1="12" y1="16" x2="12.01" y2="16"></line>
    </svg>
    <span>SIMULATION ENVIRONMENT — PAPER TRADING ONLY (INR 5,00,000 CAPITAL POOL)</span>
  </div>

  <!-- HEADER -->
  <header>
    <div class="brand-container">
      <div class="logo-wrapper">
        <img src="{logo_b64}" alt="Shadow Monarch" class="shadow-logo" onerror="this.src='logo.jpg'">
      </div>
      <div class="brand-text">
        <h1>SHADOW TRADERS <span class="badge" style="background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); font-size: 10px;">F&O QUANT TERMINAL</span></h1>
        <p>Autonomous Futures &amp; Options Execution Engine</p>
      </div>
    </div>
    <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
      <button id="pwa-install-btn" class="install-pwa-btn" onclick="installPWA()">
        Install App
      </button>
      <div class="arise-badge">
        <span style="width: 6px; height: 6px; border-radius: 50%; background: var(--accent-green);"></span>
        Options Swarm Active
      </div>
    </div>
  </header>

  <!-- STATS MATRIX -->
  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-label">Total Portfolio Pool</div>
      <div class="stat-value" id="val-total">₹5,00,000.00</div>
      <div class="stat-subtext">Initial Capital Allocation</div>
    </div>

    <div class="stat-card">
      <div class="stat-label">Available Margin</div>
      <div class="stat-value" id="val-available">₹5,00,000.00</div>
      <div class="stat-subtext">Ready for Deployment</div>
    </div>

    <div class="stat-card">
      <div class="stat-label">Realized Intraday P&L</div>
      <div class="stat-value" id="val-pnl" style="color: var(--accent-green);">+₹0.00</div>
      <div class="stat-subtext">Net Realized Return</div>
    </div>

    <div class="stat-card">
      <div class="stat-label">Brokerage Paid</div>
      <div class="stat-value" id="val-brokerage">₹0.00</div>
      <div class="stat-subtext">Standard Intraday Rate</div>
    </div>
  </div>

  <!-- TAB NAVIGATION -->
  <div class="tab-nav">
    <button class="tab-btn active" onclick="switchTab('tab-trades', event)">Executed Trades Log</button>
    <button class="tab-btn" onclick="switchTab('tab-engines', event)">F&O Trade Engines</button>
    <button class="tab-btn" onclick="switchTab('tab-patterns', event)">Pattern &amp; VWAP Hunter</button>
    <button class="tab-btn" onclick="switchTab('tab-committee', event)">3-Way Risk Committee</button>
    <button class="tab-btn" onclick="switchTab('tab-memory', event)">Reflective Memory</button>
  </div>

  <!-- PANEL 1: EXECUTED TRADES LOG -->
  <div id="tab-trades" class="panel active">
    <div class="panel-header">
      <h2>Live F&amp;O Trade Execution Log (Options &amp; Futures)</h2>
      <span class="badge badge-scalp">1m / 5m / 15m Multi-TF</span>
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
              Options Swarm active. Monitoring 1m/5m VWAP bounces, Supertrend trend flips, and strike selections...
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- PANEL 2: F&O TRADE ENGINES -->
  <div id="tab-engines" class="panel">
    <div class="panel-header">
      <h2>6 Specialized F&amp;O Trade Engines</h2>
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
        <h3><span class="badge badge-fut">BUY_FUT</span> Index &amp; Equity Long Futures</h3>
        <p>Long Futures position sizing on strong 15m structural breakouts with NIFTY outperformance (RS > 1.0).</p>
      </div>
      <div class="engine-card">
        <h3><span class="badge badge-fut">SELL_FUT</span> Index &amp; Equity Short Futures</h3>
        <p>Short Futures positioning on structural breakdowns with NIFTY underperformance (RS < 1.0).</p>
      </div>
    </div>
  </div>

  <!-- PANEL 3: 12-PATTERN & VWAP HUNTER -->
  <div id="tab-patterns" class="panel">
    <div class="panel-header">
      <h2>Pattern &amp; VWAP Quantitative Hunter</h2>
    </div>
    <div class="engine-grid">
      <div class="engine-card">
        <h3>Double Bottom (W-Pattern)</h3>
        <p>Dual support test preceding bullish option breakouts (+0.5 Score).</p>
      </div>
      <div class="engine-card">
        <h3>Double Top (M-Pattern)</h3>
        <p>Dual ceiling rejection preceding Put option breakdowns (-0.5 Score).</p>
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
      <h2>3-Way Risk Committee &amp; Subagent Debate Logs</h2>
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
      <tbody id="committee-table-body">
        <tr>
          <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 24px;">No active debate logs for current scan window. Subagent swarm evaluating market signals.</td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- PANEL 5: REFLECTIVE MEMORY -->
  <div id="tab-memory" class="panel">
    <div class="panel-header">
      <h2>Reflective Memory &amp; Trade Lessons</h2>
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
      <tbody id="memory-table-body">
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
        navigator.serviceWorker.register('/sw.js?v=4').then((reg) => {{
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
        os.path.join(base_dir, "index.html")  # Root index.html fallback
    ]

    for target in targets:
        with open(target, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Updated {target}")

    # Service Worker update for cache bust
    sw_code = """const CACHE_NAME = 'shadow-traders-v5';
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

    print("All index.html and sw.js files updated with BROKERAGE PAID label and cache busting!")

if __name__ == "__main__":
    fix_all()
