import os
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_PATH = os.path.join(ROOT_DIR, 'config', 'fo_universe_cache.json')
CACHE_TTL_HOURS = 24

NSE_FO_LOTS_URL = 'https://archives.nseindia.com/content/fo/fo_mktlots.csv'
NSE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nseindia.com/',
}

NSE_INDEX_DERIVATIVES = [
    {'ticker': '^NSEI',      'symbol': 'NIFTY',      'name': 'NIFTY 50',             'lot_size': 25,  'strike_step': 50},
    {'ticker': '^NSEBANK',   'symbol': 'BANKNIFTY',  'name': 'BANK NIFTY',           'lot_size': 15,  'strike_step': 100},
    {'ticker': '^CNXFIN',    'symbol': 'FINNIFTY',   'name': 'NIFTY Financial Svcs', 'lot_size': 25,  'strike_step': 50},
    {'ticker': '^NSMIDCP',   'symbol': 'MIDCPNIFTY', 'name': 'NIFTY MidCap Select',  'lot_size': 50,  'strike_step': 25},
    {'ticker': '^NSMIDCP50', 'symbol': 'NIFTYNXT50', 'name': 'NIFTY Next 50',        'lot_size': 25,  'strike_step': 50},
]

INDUSTRY_TO_SECTOR = {
    'bank': 'BANK', 'banking': 'BANK', 'finance': 'FINANCE', 'insurance': 'FINANCE',
    'nbfc': 'FINANCE', 'software': 'IT', 'technology': 'IT', 'telecom': 'TELECOM',
    'auto': 'AUTO', 'automobile': 'AUTO', 'pharma': 'PHARMA', 'healthcare': 'PHARMA',
    'hospital': 'PHARMA', 'metal': 'METAL', 'steel': 'METAL', 'aluminium': 'METAL',
    'fmcg': 'FMCG', 'consumer': 'FMCG', 'food': 'FMCG', 'energy': 'ENERGY',
    'oil': 'ENERGY', 'gas': 'ENERGY', 'power': 'ENERGY', 'realty': 'REALTY',
    'real estate': 'REALTY', 'infra': 'INFRA', 'infrastructure': 'INFRA',
    'engineering': 'INFRA', 'cement': 'INFRA', 'chemical': 'CHEMICAL',
    'textile': 'TEXTILE', 'media': 'MEDIA',
}

def _infer_sector(industry_str):
    s = (industry_str or '').lower()
    for keyword, sector in INDUSTRY_TO_SECTOR.items():
        if keyword in s:
            return sector
    return 'DIVERSIFIED'

def _infer_strike_step(price):
    if price < 100:   return 2.5
    if price < 500:   return 5.0
    if price < 1000:  return 10.0
    if price < 2500:  return 25.0
    if price < 5000:  return 50.0
    if price < 10000: return 100.0
    return 250.0

BOOTSTRAP_FO_STOCKS = [
    {'symbol': 'RELIANCE',   'ticker': 'RELIANCE.NS',   'lot_size': 250,  'strike_step': 20,  'sector': 'ENERGY'},
    {'symbol': 'HDFCBANK',   'ticker': 'HDFCBANK.NS',   'lot_size': 550,  'strike_step': 10,  'sector': 'BANK'},
    {'symbol': 'ICICIBANK',  'ticker': 'ICICIBANK.NS',  'lot_size': 700,  'strike_step': 10,  'sector': 'BANK'},
    {'symbol': 'INFY',       'ticker': 'INFY.NS',       'lot_size': 400,  'strike_step': 20,  'sector': 'IT'},
    {'symbol': 'TCS',        'ticker': 'TCS.NS',        'lot_size': 175,  'strike_step': 50,  'sector': 'IT'},
    {'symbol': 'KOTAKBANK',  'ticker': 'KOTAKBANK.NS',  'lot_size': 400,  'strike_step': 10,  'sector': 'BANK'},
    {'symbol': 'LT',         'ticker': 'LT.NS',         'lot_size': 175,  'strike_step': 25,  'sector': 'INFRA'},
    {'symbol': 'AXISBANK',   'ticker': 'AXISBANK.NS',   'lot_size': 625,  'strike_step': 5,   'sector': 'BANK'},
    {'symbol': 'SBIN',       'ticker': 'SBIN.NS',       'lot_size': 1500, 'strike_step': 5,   'sector': 'BANK'},
    {'symbol': 'BHARTIARTL', 'ticker': 'BHARTIARTL.NS', 'lot_size': 475,  'strike_step': 20,  'sector': 'TELECOM'},
    {'symbol': 'WIPRO',      'ticker': 'WIPRO.NS',      'lot_size': 1500, 'strike_step': 5,   'sector': 'IT'},
    {'symbol': 'HCLTECH',    'ticker': 'HCLTECH.NS',    'lot_size': 700,  'strike_step': 10,  'sector': 'IT'},
    {'symbol': 'MARUTI',     'ticker': 'MARUTI.NS',     'lot_size': 100,  'strike_step': 100, 'sector': 'AUTO'},
    {'symbol': 'TATAMOTORS', 'ticker': 'TATAMOTORS.NS', 'lot_size': 1400, 'strike_step': 5,   'sector': 'AUTO'},
    {'symbol': 'BAJFINANCE', 'ticker': 'BAJFINANCE.NS', 'lot_size': 125,  'strike_step': 50,  'sector': 'FINANCE'},
    {'symbol': 'BAJAJFINSV', 'ticker': 'BAJAJFINSV.NS', 'lot_size': 500,  'strike_step': 20,  'sector': 'FINANCE'},
    {'symbol': 'ADANIENT',   'ticker': 'ADANIENT.NS',   'lot_size': 625,  'strike_step': 10,  'sector': 'INFRA'},
    {'symbol': 'ADANIPORTS', 'ticker': 'ADANIPORTS.NS', 'lot_size': 1250, 'strike_step': 5,   'sector': 'INFRA'},
    {'symbol': 'HINDALCO',   'ticker': 'HINDALCO.NS',   'lot_size': 1400, 'strike_step': 10,  'sector': 'METAL'},
    {'symbol': 'TATASTEEL',  'ticker': 'TATASTEEL.NS',  'lot_size': 5500, 'strike_step': 2.5, 'sector': 'METAL'},
    {'symbol': 'JSWSTEEL',   'ticker': 'JSWSTEEL.NS',   'lot_size': 1350, 'strike_step': 5,   'sector': 'METAL'},
    {'symbol': 'DLF',        'ticker': 'DLF.NS',        'lot_size': 825,  'strike_step': 10,  'sector': 'REALTY'},
    {'symbol': 'NTPC',       'ticker': 'NTPC.NS',       'lot_size': 2250, 'strike_step': 5,   'sector': 'ENERGY'},
    {'symbol': 'POWERGRID',  'ticker': 'POWERGRID.NS',  'lot_size': 2300, 'strike_step': 5,   'sector': 'ENERGY'},
    {'symbol': 'ONGC',       'ticker': 'ONGC.NS',       'lot_size': 1925, 'strike_step': 5,   'sector': 'ENERGY'},
    {'symbol': 'COALINDIA',  'ticker': 'COALINDIA.NS',  'lot_size': 2100, 'strike_step': 5,   'sector': 'ENERGY'},
    {'symbol': 'BPCL',       'ticker': 'BPCL.NS',       'lot_size': 1800, 'strike_step': 5,   'sector': 'ENERGY'},
    {'symbol': 'SUNPHARMA',  'ticker': 'SUNPHARMA.NS',  'lot_size': 350,  'strike_step': 20,  'sector': 'PHARMA'},
    {'symbol': 'DRREDDY',    'ticker': 'DRREDDY.NS',    'lot_size': 125,  'strike_step': 50,  'sector': 'PHARMA'},
    {'symbol': 'CIPLA',      'ticker': 'CIPLA.NS',      'lot_size': 650,  'strike_step': 10,  'sector': 'PHARMA'},
    {'symbol': 'DIVISLAB',   'ticker': 'DIVISLAB.NS',   'lot_size': 200,  'strike_step': 50,  'sector': 'PHARMA'},
    {'symbol': 'APOLLOHOSP', 'ticker': 'APOLLOHOSP.NS', 'lot_size': 125,  'strike_step': 50,  'sector': 'PHARMA'},
    {'symbol': 'HINDUNILVR', 'ticker': 'HINDUNILVR.NS', 'lot_size': 300,  'strike_step': 20,  'sector': 'FMCG'},
    {'symbol': 'ITC',        'ticker': 'ITC.NS',        'lot_size': 1600, 'strike_step': 5,   'sector': 'FMCG'},
    {'symbol': 'NESTLEIND',  'ticker': 'NESTLEIND.NS',  'lot_size': 50,   'strike_step': 100, 'sector': 'FMCG'},
    {'symbol': 'BRITANNIA',  'ticker': 'BRITANNIA.NS',  'lot_size': 100,  'strike_step': 100, 'sector': 'FMCG'},
    {'symbol': 'TATACONSUM', 'ticker': 'TATACONSUM.NS', 'lot_size': 900,  'strike_step': 10,  'sector': 'FMCG'},
    {'symbol': 'TITAN',      'ticker': 'TITAN.NS',      'lot_size': 375,  'strike_step': 20,  'sector': 'FMCG'},
    {'symbol': 'ASIANPAINT', 'ticker': 'ASIANPAINT.NS', 'lot_size': 200,  'strike_step': 50,  'sector': 'CHEMICAL'},
    {'symbol': 'ULTRACEMCO', 'ticker': 'ULTRACEMCO.NS', 'lot_size': 100,  'strike_step': 100, 'sector': 'INFRA'},
    {'symbol': 'SHREECEM',   'ticker': 'SHREECEM.NS',   'lot_size': 25,   'strike_step': 200, 'sector': 'INFRA'},
    {'symbol': 'GRASIM',     'ticker': 'GRASIM.NS',     'lot_size': 250,  'strike_step': 25,  'sector': 'INFRA'},
    {'symbol': 'INDUSINDBK', 'ticker': 'INDUSINDBK.NS', 'lot_size': 500,  'strike_step': 20,  'sector': 'BANK'},
    {'symbol': 'BANDHANBNK', 'ticker': 'BANDHANBNK.NS', 'lot_size': 1800, 'strike_step': 5,   'sector': 'BANK'},
    {'symbol': 'PNB',        'ticker': 'PNB.NS',        'lot_size': 8000, 'strike_step': 2,   'sector': 'BANK'},
    {'symbol': 'CANBK',      'ticker': 'CANBK.NS',      'lot_size': 4500, 'strike_step': 2,   'sector': 'BANK'},
    {'symbol': 'BANKBARODA', 'ticker': 'BANKBARODA.NS', 'lot_size': 4350, 'strike_step': 2,   'sector': 'BANK'},
    {'symbol': 'TECHM',      'ticker': 'TECHM.NS',      'lot_size': 600,  'strike_step': 10,  'sector': 'IT'},
    {'symbol': 'MPHASIS',    'ticker': 'MPHASIS.NS',    'lot_size': 175,  'strike_step': 25,  'sector': 'IT'},
    {'symbol': 'LTIM',       'ticker': 'LTIM.NS',       'lot_size': 150,  'strike_step': 50,  'sector': 'IT'},
    {'symbol': 'PERSISTENT', 'ticker': 'PERSISTENT.NS', 'lot_size': 125,  'strike_step': 50,  'sector': 'IT'},
    {'symbol': 'HAL',        'ticker': 'HAL.NS',        'lot_size': 150,  'strike_step': 100, 'sector': 'INFRA'},
    {'symbol': 'BEL',        'ticker': 'BEL.NS',        'lot_size': 2900, 'strike_step': 5,   'sector': 'INFRA'},
    {'symbol': 'BHEL',       'ticker': 'BHEL.NS',       'lot_size': 4350, 'strike_step': 2,   'sector': 'INFRA'},
    {'symbol': 'SIEMENS',    'ticker': 'SIEMENS.NS',    'lot_size': 125,  'strike_step': 100, 'sector': 'INFRA'},
    {'symbol': 'ABB',        'ticker': 'ABB.NS',        'lot_size': 125,  'strike_step': 100, 'sector': 'INFRA'},
    {'symbol': 'POLYCAB',    'ticker': 'POLYCAB.NS',    'lot_size': 125,  'strike_step': 100, 'sector': 'INFRA'},
    {'symbol': 'MOTHERSON',  'ticker': 'MOTHERSON.NS',  'lot_size': 5000, 'strike_step': 2,   'sector': 'AUTO'},
    {'symbol': 'M&M',        'ticker': 'M&M.NS',        'lot_size': 350,  'strike_step': 20,  'sector': 'AUTO'},
    {'symbol': 'EICHERMOT',  'ticker': 'EICHERMOT.NS',  'lot_size': 175,  'strike_step': 50,  'sector': 'AUTO'},
    {'symbol': 'HEROMOTOCO', 'ticker': 'HEROMOTOCO.NS', 'lot_size': 150,  'strike_step': 50,  'sector': 'AUTO'},
    {'symbol': 'BOSCHLTD',   'ticker': 'BOSCHLTD.NS',   'lot_size': 15,   'strike_step': 500, 'sector': 'AUTO'},
    {'symbol': 'ZOMATO',     'ticker': 'ZOMATO.NS',     'lot_size': 3500, 'strike_step': 2,   'sector': 'FMCG'},
    {'symbol': 'PAYTM',      'ticker': 'PAYTM.NS',      'lot_size': 2000, 'strike_step': 5,   'sector': 'FINANCE'},
    {'symbol': 'NYKAA',      'ticker': 'NYKAA.NS',      'lot_size': 4000, 'strike_step': 2,   'sector': 'FMCG'},
    {'symbol': 'DELHIVERY',  'ticker': 'DELHIVERY.NS',  'lot_size': 2250, 'strike_step': 5,   'sector': 'INFRA'},
    {'symbol': 'VEDL',       'ticker': 'VEDL.NS',       'lot_size': 2800, 'strike_step': 5,   'sector': 'METAL'},
    {'symbol': 'SAIL',       'ticker': 'SAIL.NS',       'lot_size': 4500, 'strike_step': 2,   'sector': 'METAL'},
    {'symbol': 'NMDC',       'ticker': 'NMDC.NS',       'lot_size': 3750, 'strike_step': 2,   'sector': 'METAL'},
    {'symbol': 'RECLTD',     'ticker': 'RECLTD.NS',     'lot_size': 2200, 'strike_step': 5,   'sector': 'FINANCE'},
    {'symbol': 'PFC',        'ticker': 'PFC.NS',        'lot_size': 2700, 'strike_step': 5,   'sector': 'FINANCE'},
    {'symbol': 'IRFC',       'ticker': 'IRFC.NS',       'lot_size': 4350, 'strike_step': 2,   'sector': 'FINANCE'},
    {'symbol': 'IRCTC',      'ticker': 'IRCTC.NS',      'lot_size': 875,  'strike_step': 10,  'sector': 'FMCG'},
    {'symbol': 'CONCOR',     'ticker': 'CONCOR.NS',     'lot_size': 1000, 'strike_step': 10,  'sector': 'INFRA'},
    {'symbol': 'PIDILITIND',  'ticker': 'PIDILITIND.NS', 'lot_size': 350,  'strike_step': 20,  'sector': 'CHEMICAL'},
    {'symbol': 'BERGEPAINT', 'ticker': 'BERGEPAINT.NS', 'lot_size': 1100, 'strike_step': 5,   'sector': 'CHEMICAL'},
    {'symbol': 'KANSAINER',  'ticker': 'KANSAINER.NS',  'lot_size': 500,  'strike_step': 10,  'sector': 'CHEMICAL'},
    {'symbol': 'UPL',        'ticker': 'UPL.NS',        'lot_size': 1300, 'strike_step': 5,   'sector': 'CHEMICAL'},
    {'symbol': 'TRENT',      'ticker': 'TRENT.NS',      'lot_size': 350,  'strike_step': 25,  'sector': 'FMCG'},
    {'symbol': 'DMART',      'ticker': 'DMART.NS',      'lot_size': 175,  'strike_step': 50,  'sector': 'FMCG'},
    {'symbol': 'MUTHOOTFIN', 'ticker': 'MUTHOOTFIN.NS', 'lot_size': 400,  'strike_step': 20,  'sector': 'FINANCE'},
    {'symbol': 'CHOLAFIN',   'ticker': 'CHOLAFIN.NS',   'lot_size': 750,  'strike_step': 10,  'sector': 'FINANCE'},
    {'symbol': 'SBILIFE',    'ticker': 'SBILIFE.NS',    'lot_size': 750,  'strike_step': 10,  'sector': 'FINANCE'},
    {'symbol': 'HDFCLIFE',   'ticker': 'HDFCLIFE.NS',   'lot_size': 1100, 'strike_step': 5,   'sector': 'FINANCE'},
    {'symbol': 'ICICIGI',    'ticker': 'ICICIGI.NS',    'lot_size': 500,  'strike_step': 10,  'sector': 'FINANCE'},
    {'symbol': 'LICI',       'ticker': 'LICI.NS',       'lot_size': 700,  'strike_step': 10,  'sector': 'FINANCE'},
]

def _load_cache():
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        cached_at = datetime.fromisoformat(data.get('cached_at', '2000-01-01'))
        if datetime.utcnow() - cached_at < timedelta(hours=CACHE_TTL_HOURS):
            logger.info(f'[FO Universe Loader] Using cached universe ({len(data.get(\"stocks\", []))} stocks).')
            return data
    except Exception as e:
        logger.warning(f'[FO Universe Loader] Cache read failed: {e}')
    return {}

def _save_cache(universe):
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        universe['cached_at'] = datetime.utcnow().isoformat()
        with open(CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(universe, f, indent=2)
        logger.info(f'[FO Universe Loader] Cached {len(universe.get(\"stocks\", []))} stocks.')
    except Exception as e:
        logger.warning(f'[FO Universe Loader] Cache write failed: {e}')

def _fetch_nse_fo_lots():
    try:
        resp = requests.get(NSE_FO_LOTS_URL, headers=NSE_HEADERS, timeout=15)
        resp.raise_for_status()
        lines = resp.text.strip().splitlines()
        stocks = []
        for line in lines[1:]:
            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 3:
                continue
            symbol = parts[1].strip().upper() if len(parts) > 1 else ''
            if not symbol or symbol in ('SYMBOL', 'UNDERLYING', ''):
                continue
            try:
                lot_size = int(parts[2].replace(' ', '').replace(',', ''))
            except (ValueError, IndexError):
                lot_size = 500
            stocks.append({'symbol': symbol, 'ticker': f'{symbol}.NS', 'lot_size': lot_size,
                           'strike_step': _infer_strike_step(0), 'sector': 'DIVERSIFIED'})
        logger.info(f'[FO Universe Loader] NSE fetch returned {len(stocks)} F&O eligible stocks.')
        return stocks
    except Exception as e:
        logger.warning(f'[FO Universe Loader] NSE fetch failed ({e}). Using bootstrap fallback.')
        return []

def get_fo_universe():
    cached = _load_cache()
    if cached.get('stocks'):
        return {'indices': NSE_INDEX_DERIVATIVES, 'stocks': cached['stocks']}
    stocks = _fetch_nse_fo_lots()
    if len(stocks) < 50:
        logger.warning(f'[FO Universe Loader] NSE returned only {len(stocks)} stocks — merging with bootstrap.')
        nse_symbols = {s['symbol'] for s in stocks}
        for bs in BOOTSTRAP_FO_STOCKS:
            if bs['symbol'] not in nse_symbols:
                stocks.append(bs)
    universe = {'indices': NSE_INDEX_DERIVATIVES, 'stocks': stocks}
    _save_cache(universe)
    return universe
