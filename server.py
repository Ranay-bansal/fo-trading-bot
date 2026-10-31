import os
import sys
import json
import logging
import subprocess
import threading
import time
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [FOServer] - %(levelname)s - %(message)s")
logger = logging.getLogger("RenderFOServer")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", 8080))
BOT_SECRET = os.environ.get("BOT_WEBHOOK_SECRET", "alphadesk_fo_secret_key_2026")
IST = timezone(timedelta(hours=5, minutes=30))

def run_fo_bot(args: list = None) -> dict:
    """Executes main.py with the specified arguments and returns execution summary."""
    now_ist = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
    args = args or []
    cmd = [sys.executable, os.path.join(ROOT_DIR, "main.py")] + args
    cmd_str = " ".join(cmd)
    logger.info(f"Triggering FO bot: '{cmd_str}' at {now_ist}")
    
    start_t = time.time()
    res = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True)
    duration = round(time.time() - start_t, 2)
    
    success = (res.returncode == 0)
    stdout_lines = [l for l in res.stdout.splitlines() if l.strip()]
    stderr_lines = [l for l in res.stderr.splitlines() if l.strip()]
    
    summary = {
        "command": cmd_str,
        "success": success,
        "return_code": res.returncode,
        "duration_sec": duration,
        "timestamp_ist": now_ist,
        "stdout_tail": stdout_lines[-20:],
        "stderr_tail": stderr_lines[-10:] if not success else []
    }
    logger.info(f"Completed in {duration}s. Success: {success}")
    return summary

class FOBotRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, data: dict):
        response = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response)

    def _is_authenticated(self) -> bool:
        """Verifies Bearer token, X-API-Key, or ?key= query param."""
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            if token == BOT_SECRET:
                return True
        api_key = self.headers.get("X-API-Key", "").strip()
        if api_key and api_key == BOT_SECRET:
            return True
        query = urlparse(self.path).query
        if query:
            params = parse_qs(query)
            if params.get("key", [""])[0] == BOT_SECRET:
                return True
        return False

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        now_ist = datetime.now(IST)

        # Health check endpoint (Render uses this for 200 OK)
        if path in ["/", "/health"]:
            state_file = os.path.join(ROOT_DIR, "state", "portfolio_state.json")
            state_data = {}
            if os.path.exists(state_file):
                try:
                    with open(state_file, "r", encoding="utf-8") as f:
                        state_data = json.load(f)
                except Exception:
                    pass

            is_market_hours = (now_ist.weekday() < 5 and 
                              ((now_ist.hour > 9 or (now_ist.hour == 9 and now_ist.minute >= 15)) and 
                               (now_ist.hour < 15 or (now_ist.hour == 15 and now_ist.minute <= 30))))

            self._send_json(200, {
                "status": "online",
                "service": "AlphaDesk F&O Quant Swarm Trading Bot",
                "platform": "Render Cloud Runner",
                "server_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
                "is_market_open": is_market_hours,
                "portfolio_summary": {
                    "pool_total": state_data.get("pool_total", 500000.0),
                    "pool_available": state_data.get("pool_available", 500000.0),
                    "open_positions": len(state_data.get("open_positions", [])),
                    "daily_pnl_inr": state_data.get("daily_pnl_inr", 0.0),
                    "trades_today": state_data.get("trades_today", 0),
                    "kill_switch_active": state_data.get("kill_switch_active", False),
                    "kill_switch_reason": state_data.get("kill_switch_reason")
                }
            })
            return

        # View latest trades (secured)
        if path == "/trades":
            if not self._is_authenticated():
                self._send_json(401, {"error": "Unauthorized. Provide valid Bearer token or ?key="})
                return
            csv_path = os.path.join(ROOT_DIR, "state", "trade_log.csv")
            trades = []
            if os.path.exists(csv_path):
                import csv
                with open(csv_path, "r", encoding="utf-8") as f:
                    reader = list(csv.DictReader(f))
                    trades = [r for r in reader if r.get("executed_price") or r.get("price")][-30:]
            self._send_json(200, {"total_trades": len(trades), "recent_trades": trades})
            return

        # View portfolio state (secured)
        if path == "/state":
            if not self._is_authenticated():
                self._send_json(401, {"error": "Unauthorized. Provide valid Bearer token or ?key="})
                return
            state_file = os.path.join(ROOT_DIR, "state", "portfolio_state.json")
            data = {}
            if os.path.exists(state_file):
                with open(state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            self._send_json(200, data)
            return

        self._send_json(404, {"error": "Not Found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if not self._is_authenticated():
            self._send_json(401, {"error": "Unauthorized. Provide valid Bearer token, X-API-Key, or ?key="})
            return

        # 1. Trigger Standard F&O Quant Scan
        if path == "/scan":
            args = []
            if query.get("force_weekend", ["0"])[0] in ["1", "true"]:
                args.append("--force-weekend")
            result = run_fo_bot(args=args)
            status = 200 if result["success"] else 500
            self._send_json(status, result)
            return

        # 2. Trigger Square-off
        if path == "/squareoff":
            result = run_fo_bot(args=["--squareoff"])
            status = 200 if result["success"] else 500
            self._send_json(status, result)
            return

        # 3. Trigger Kill-switch override
        if path == "/killswitch":
            action = query.get("action", ["halt"])[0]
            result = run_fo_bot(args=["--kill-switch", action])
            status = 200 if result["success"] else 500
            self._send_json(status, result)
            return

        self._send_json(404, {"error": "Endpoint Not Found. Supported: POST /scan, POST /squareoff, POST /killswitch"})

def start_server():
    server = HTTPServer(("0.0.0.0", PORT), FOBotRequestHandler)
    logger.info(f"=== AlphaDesk F&O Render Cloud Web Server listening on port {PORT} ===")
    logger.info(f"Endpoints available:")
    logger.info(f"  GET  /health      -> Public health check")
    logger.info(f"  POST /scan        -> Run F&O quant pipeline (Secured)")
    logger.info(f"  POST /squareoff   -> Square-off all positions (Secured)")
    logger.info(f"  POST /killswitch  -> Halt/Resume killswitch (Secured)")
    logger.info(f"  GET  /trades      -> View recent trade log (Secured)")
    logger.info(f"  GET  /state       -> View portfolio state (Secured)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        server.server_close()

if __name__ == "__main__":
    start_server()
