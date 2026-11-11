"""
AlphaDesk — Official NSE MCP Streamable HTTP Client Adapter (core/nse_mcp.py)
Fetches live tick quotes, day high/low, VWAP, and India VIX from:
  https://mcp.nseindia.in/cmmkt/mcp
100% official exchange feed, zero login credentials, zero scraping.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any

try:
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

logger = logging.getLogger("NseMcpStream")
CM_MKT_URL = "https://mcp.nseindia.in/cmmkt/mcp"


async def _async_call_tool(tool_name: str, arguments: Dict[str, Any], timeout: float = 4.0) -> Optional[str]:
    if not MCP_AVAILABLE:
        return None
    try:
        async with streamable_http_client(CM_MKT_URL) as (r, w):
            async with ClientSession(r, w) as session:
                await session.initialize()
                res = await asyncio.wait_for(session.call_tool(tool_name, arguments), timeout=timeout)
                if res and res.content:
                    return res.content[0].text
    except Exception as exc:
        logger.debug(f"NSE MCP tool '{tool_name}' failed or timed out: {exc}")
    return None


def fetch_live_stock_quote(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Fetches real-time stock quote from NSE MCP.
    Returns dict with last_price, high_price, low_price, open_price, prev_close, volume, vwap.
    Returns None on any error or timeout (safe for non-blocking fallback).
    """
    clean_sym = ticker.replace(".NS", "").replace(".BO", "").strip().upper()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            raw = loop.run_until_complete(_async_call_tool("cm_get_stock_quote", {"symbol": clean_sym}))
        finally:
            loop.close()

        if not raw:
            return None

        data = json.loads(raw)
        stk = data.get("stock", {})
        if not stk or not stk.get("lastTradedPrice"):
            return None

        ltp = float(stk.get("lastTradedPrice"))
        if ltp <= 0:
            return None

        open_p = float(stk.get("openPrice") or ltp)
        high_p = float(stk.get("highPrice") or ltp)
        low_p = float(stk.get("lowPrice") or ltp)
        prev_c = float(stk.get("preClosePrice") or ltp)
        pct_c = float(stk.get("perChange") or 0.0)
        vol = int(stk.get("volume") or 0)
        val_cr = float(stk.get("value") or 0.0)
        vwap = (
            round((val_cr * 10_000_000.0) / vol, 2)
            if (vol > 0 and val_cr > 0)
            else round((high_p + low_p + ltp) / 3.0, 2)
        )

        return {
            "symbol": clean_sym,
            "last_price": ltp,
            "open_price": open_p,
            "high_price": high_p,
            "low_price": low_p,
            "prev_close": prev_c,
            "pct_change": pct_c,
            "volume": vol,
            "vwap": vwap,
        }
    except Exception as e:
        logger.debug(f"NSE MCP quote error for {clean_sym}: {e}")
        return None


def fetch_live_vix() -> Optional[float]:
    """
    Fetches official live India VIX from NSE MCP.
    Returns float (e.g. 17.58) or None on fallback.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            raw = loop.run_until_complete(_async_call_tool("cm_get_index_quote", {"indexName": "INDIA VIX"}))
        finally:
            loop.close()

        if not raw:
            return None

        data = json.loads(raw)
        idx = data.get("index", {})
        last_val = idx.get("last")
        if last_val is not None and float(last_val) > 0:
            return float(last_val)
    except Exception as e:
        logger.debug(f"NSE MCP VIX error: {e}")
    return None
