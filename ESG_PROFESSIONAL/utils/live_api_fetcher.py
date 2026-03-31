"""
Live API Data Fetcher - Production Version
Pre-configured with Alpha Vantage API key
"""

import pandas as pd
import numpy as np
from datetime import datetime
import time
import warnings
warnings.filterwarnings('ignore')

# User's Alpha Vantage API key (pre-configured)
DEFAULT_API_KEY = "V1C9K6QDR0RWEXOK"

# 540+ company tickers across 5 sectors
COMPANY_TICKERS = {
    'Technology, Finance, Healthcare & Services': [
        'AAPL','MSFT','GOOGL','AMZN','META','NVDA','TSLA','INTC','AMD','CRM',
        'ORCL','CSCO','ADBE','AVGO','TXN','QCOM','IBM','NFLX','PYPL','NOW',
        'SHOP','UBER','ABNB','TWLO','ZOOM','DDOG','CRWD','ZS','OKTA','PANW',
        'SNOW','PLTR','COIN','RBLX','NET','DOCU','TEAM','WDAY','VEEV','SPLK',
        'FTNT','MDB','ZM','ESTC','GTLB','BILL','QLYS','COUP','SMCI','NTAP',
        'STX','WDC','HPQ','DELL','ACN','INFY','CTSH','IT','EPAM','LDOS',
        'BAH','CACI','SAIC','DXC','ATOS','CGI','WIT','CGNX','KEYS','ANSS',
        'CDNS','SNPS','ADSK','PTC','TYL','ROP','BR','FTV','ITW','ROK',
        'EMR','HON','JCI','CAR','GNRC','IR','XYL','AME','HUBB','AOS',
        'MIDD','TTC','BLDR','SSD','BLD','FAST','LECO','WSO','MLI','DCI',
        'UFPI','AAON','AIT','CR','FLS','GGG','ITGR','IEX','RBC','TRN',
        'GWW','MSM','DY','NFG','SWK','MATW','AIN','DNOW','DXPE','KAI',
        'CFX','BMI','EXPO','ALG','LAWS','TILE','HAYW','HASI','WIRE','CBT',
        'TISI','GVA','AROC','CLH','EEX','SLGN','HTLD','HLIO','MLR','UFPT',
        'PRIM','NPO','TWIN','HI','ESE','ATKR','SPXC','POWL','PLUG','FCEL',
    ],
    'Infrastructure, Real Estate & Construction': [
        'JPM','BAC','WFC','C','GS','MS','V','MA','AXP','BLK',
        'SCHW','USB','PNC','TFC','COF','BK','STT','NTRS','CFG','RF',
        'KEY','FITB','HBAN','MTB','ZION','CMA','PBCT','FRC','SIVB','SBNY',
        'WAL','EWBC','FCNCA','PACW','CUBI','BANF','WAFD','UBSI','HWC','ONB',
        'SFNC','FBP','BPOP','OZK','UMBF','FIBK','TCBI','WTFC','CASH','SBCF',
        'ICE','CME','CBOE','NDAQ','SPGI','MCO','MSCI','MKTX','TW','BGC',
        'VIRT','LPLA','IBKR','SF','HOOD','SOFI','UPST','AFRM','LC','ENVA',
        'PRU','MET','AIG','AFL','ALL','TRV','PGR','CB','HIG','PFG',
        'L','RGA','LNC','FNF','FAF','STWD','NLY','AGNC','TWO','CIM',
        'IVR','MFA','PMT','MITT','NRZ','RITM','GPMT','ACRE','ARI','BXMT',
        'RC','NYMT','DX','KREF','EARN','FBRT','TRTX','ORC','OXSQ','MAIN',
        'GAIN','GLAD','HTGC','FDUS','PSEC','NMFC','FSK','GBDC','PNNT','TSLX',
    ],
    'Agriculture & Food Systems': [
        'JNJ','UNH','PFE','ABBV','TMO','MRK','LLY','ABT','DHR','BMY',
        'MDT','AMGN','GILD','REGN','VRTX','BIIB','ISRG','BSX','EW','ZBH',
        'SYK','BAX','BDX','IQV','HCA','DGX','LH','CVS','CI','HUM',
        'CNC','MOH','ELV','CRL','A','TDOC','VEEV','DXCM','HOLX','ALGN',
        'IDXX','MTD','RMD','VAR','WST','TECH','COO','XRAY','PODD','TNDM',
        'NVST','OMCL','NEOG','IRTC','NVCR','ICUI','AMED','ENSG','ATRC','ATRI',
        'MRNA','BNTX','REGN','VRTX','ALXN','BMRN','IONS','RARE','SRPT','BLUE',
        'FOLD','EDIT','CRSP','NTLA','BEAM','VERV','ARCT','SANA','FATE','PRME',
        'VCYT','EXAS','GH','RVMD','SEER','ILMN','TMO','A','DHR','WAT',
        'PKI','BIO','TECH','MTD','IQV','CRL','MEDP','STE','HSIC','PDCO',
    ],
    'Manufacturing & Core Industries': [
        'XOM','CVX','COP','SLB','EOG','PSX','VLO','MPC','DVN','PXD',
        'FANG','OXY','HAL','BKR','WMB','OKE','KMI','EPD','MMP','TRGP',
        'HES','MRO','APA','NOG','SM','CIVI','RRC','AR','PR','MTDR',
        'OVV','CHRD','MUR','CNX','RNG','EQT','SWN','GPOR','PBF','DK',
        'HFC','ANDV','CVR','NOV','FTI','CHK','CRGY','SBOW','PDCE','NINE',
        'CPE','REPX','CRC','CLR','ESTE','MGY','VTLE','CRK','CTRA','REI',
        'ENLC','DCP','MPLX','PAA','AM','GEL','DKL','CEQP','USAC','NGL',
        'WTTR','NEXT','NBR','HP','LBRT','PUMP','RES','WTTR','PTEN','WTTR',
    ],
    'Consumer Goods, Retail & Lifestyle': [
        'WMT','HD','PG','COST','KO','PEP','MCD','NKE','SBUX','TGT',
        'LOW','DG','DLTR','YUM','CMG','RH','ROST','TJX','CL','GIS',
        'K','MKC','HSY','CHD','EL','COTY','NWL','HBI','BBY','TSCO',
        'ORLY','AZO','AAP','GME','KSS','M','JWN','DKS','ANF','AEO',
        'GPS','URBN','FL','SHOO','HIBB','SCVL','DLTH','EXPR','BGFV','ASO',
        'BIG','DBI','OLLI','FIVE','TCS','ULTA','LULU','GES','PLCE','ZUMZ',
        'VRA','BKE','BOOT','TPR','RL','PVH','VFC','HBI','LEE','OXM',
        'GIII','UNFI','SJM','CAG','CPB','HRL','MKC','BF.B','STZ','TAP',
        'SAM','MNST','KDP','FIZZ','CELH','COKE','DPS','MNST','CELH','PEP',
    ],
}

# Default ESG base scores per sector (used when live ESG data is missing)
_BASE_ESG = {
    'Technology, Finance, Healthcare & Services': 65,
    'Infrastructure, Real Estate & Construction': 55,
    'Agriculture & Food Systems':                 68,
    'Manufacturing & Core Industries':            35,
    'Consumer Goods, Retail & Lifestyle':         62,
}
_DEFAULT_ESG = 55  # safe fallback if sector is unknown / None


def fetch_from_yahoo(ticker, sector):
    """Fetch live data from Yahoo Finance."""
    try:
        import yfinance as yf

        stock = yf.Ticker(ticker)
        info  = stock.info

        if not info or len(info) < 5:
            return None

        result = {
            'ticker':        ticker,
            'company_name':  info.get('longName') or info.get('shortName') or f"{ticker} Corp",
            'sector':        sector,
            'market_cap':    info.get('marketCap', 0),
            'revenue':       info.get('totalRevenue') or info.get('revenue', 0),
            'profit_margin': (info.get('profitMargins', 0) * 100) if info.get('profitMargins') else 0,
            'debt_to_equity':info.get('debtToEquity', 0),
            'beta':          info.get('beta', 1.0),
            'pe_ratio':      info.get('trailingPE') or info.get('forwardPE', 0),
            'current_price': info.get('currentPrice') or info.get('regularMarketPrice', 0),
            'volume':        info.get('volume', 0),
            'data_source':   'yahoo_finance',
            'last_updated':  datetime.now().isoformat(),
        }

        esg_data = info.get('esgScores', {})
        if esg_data and isinstance(esg_data, dict):
            result['esg_score']           = esg_data.get('totalEsg', 0)
            result['environmental_score'] = esg_data.get('environmentScore', 0)
            result['social_score']        = esg_data.get('socialScore', 0)
            result['governance_score']    = esg_data.get('governanceScore', 0)
        else:
            result['esg_score'] = result['environmental_score'] = 0
            result['social_score'] = result['governance_score'] = 0

        if result['market_cap'] == 0 and result['revenue'] == 0 and result['current_price'] == 0:
            return None

        return result

    except Exception:
        return None


def fetch_from_alphavantage(ticker, sector, api_key):
    """Fetch from Alpha Vantage."""
    if not api_key:
        return None

    try:
        import requests

        url  = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}'
        r    = requests.get(url, timeout=5)
        data = r.json()

        if not data or 'Symbol' not in data:
            return None

        result = {
            'ticker':        ticker,
            'company_name':  data.get('Name', f"{ticker} Corp"),
            'sector':        sector,
            'market_cap':    int(float(data.get('MarketCapitalization', 0))),
            'revenue':       int(float(data.get('RevenueTTM', 0))),
            'profit_margin': float(data.get('ProfitMargin', 0)) * 100,
            'debt_to_equity':float(data.get('DebtToEquity', 0)),
            'beta':          float(data.get('Beta', 1.0)),
            'pe_ratio':      float(data.get('PERatio', 0)),
            'data_source':   'alpha_vantage',
            'last_updated':  datetime.now().isoformat(),
        }

        return result

    except Exception:
        return None


def create_fallback(ticker, sector):
    """Create realistic fallback data."""
    defaults = {
        'Technology, Finance, Healthcare & Services': {'esg': 65, 'mktcap': 50e9, 'pm': 15, 'beta': 1.2, 'dte': 40},
        'Infrastructure, Real Estate & Construction': {'esg': 55, 'mktcap': 30e9, 'pm': 22, 'beta': 1.1, 'dte': 350},
        'Agriculture & Food Systems':                 {'esg': 68, 'mktcap': 25e9, 'pm': 12, 'beta': 0.7, 'dte': 80},
        'Manufacturing & Core Industries':            {'esg': 35, 'mktcap': 20e9, 'pm': 8,  'beta': 1.0, 'dte': 60},
        'Consumer Goods, Retail & Lifestyle':         {'esg': 62, 'mktcap': 15e9, 'pm': 7,  'beta': 0.9, 'dte': 100},
    }

    # Safe .get() — never crashes on unknown sector
    d   = defaults.get(sector, defaults['Technology, Finance, Healthcare & Services'])
    rng = np.random.RandomState(hash(ticker) % 2**32)
    esg = d['esg'] + rng.uniform(-8, 8)

    return {
        'ticker':              ticker,
        'company_name':        f"{ticker} Corp",
        'sector':              sector,
        'market_cap':          int(d['mktcap'] * rng.uniform(0.5, 2.0)),
        'revenue':             int(d['mktcap'] * 0.3 * rng.uniform(0.5, 2.0)),
        'profit_margin':       round(d['pm']  + rng.uniform(-5, 5), 2),
        'debt_to_equity':      round(d['dte'] + rng.uniform(-20, 20), 2),
        'beta':                round(d['beta']+ rng.uniform(-0.2, 0.2), 3),
        'pe_ratio':            round(rng.uniform(10, 40), 2),
        'esg_score':           round(np.clip(esg, 10, 95), 2),
        'environmental_score': round(np.clip(esg + rng.uniform(-8, 8), 10, 95), 2),
        'social_score':        round(np.clip(esg + rng.uniform(-6, 6), 10, 95), 2),
        'governance_score':    round(np.clip(esg + rng.uniform(-5, 5), 10, 95), 2),
        'current_price':       round(rng.uniform(20, 500), 2),
        'volume':              int(rng.uniform(1e6, 50e6)),
        'data_source':         'fallback',
        'last_updated':        datetime.now().isoformat(),
    }


def fetch_live_dataset(api_keys=None, progress_callback=None, max_companies=550):
    """
    Fetch LIVE data with graceful fallbacks.

    Args:
        api_keys: Dict with 'alphavantage' key (defaults to pre-configured)
        progress_callback: Function(current, total, message)
        max_companies: Target number of companies

    Returns:
        DataFrame, live_count
    """

    if not api_keys:
        api_keys = {'alphavantage': DEFAULT_API_KEY}
    elif 'alphavantage' not in api_keys or not api_keys['alphavantage']:
        api_keys['alphavantage'] = DEFAULT_API_KEY

    all_data       = []
    live_count     = 0
    total_attempted = 0

    companies_per_sector = max_companies // len(COMPANY_TICKERS)

    for sector, tickers in COMPANY_TICKERS.items():
        tickers_to_fetch = tickers[:companies_per_sector]

        for ticker in tickers_to_fetch:
            total_attempted += 1

            if progress_callback:
                progress_callback(total_attempted, max_companies, f"Fetching {ticker}...")

            data = None

            # Try Yahoo Finance first
            data = fetch_from_yahoo(ticker, sector)

            # Try Alpha Vantage if Yahoo failed
            if not data and api_keys and api_keys.get('alphavantage'):
                data = fetch_from_alphavantage(ticker, sector, api_keys['alphavantage'])
                time.sleep(0.2)

            if data:
                live_count += 1
            else:
                data = create_fallback(ticker, sector)

            all_data.append(data)
            time.sleep(0.05)

            if len(all_data) >= max_companies:
                break

        if len(all_data) >= max_companies:
            break

    df = pd.DataFrame(all_data)

    # Clean numeric columns
    numeric_cols = ['market_cap','revenue','profit_margin','debt_to_equity','beta','pe_ratio',
                    'esg_score','environmental_score','social_score','governance_score',
                    'current_price','volume']

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Estimate missing ESG scores — FIXED: .get() with default, no KeyError possible
    mask = df['esg_score'] == 0
    if mask.sum() > 0:
        for idx in df[mask].index:
            sector  = df.loc[idx, 'sector']
            mktcap  = df.loc[idx, 'market_cap']
            pm      = df.loc[idx, 'profit_margin']

            # Safe lookup — returns _DEFAULT_ESG if sector is None/unknown
            base_esg = _BASE_ESG.get(str(sector) if sector else '', _DEFAULT_ESG)

            if mktcap > 500e9:  base_esg += 10
            elif mktcap > 100e9: base_esg += 5

            if pm > 20:  base_esg += 5
            elif pm < 0: base_esg -= 10

            base_esg = int(np.clip(base_esg, 10, 95))

            df.loc[idx, 'esg_score']           = base_esg
            df.loc[idx, 'environmental_score'] = np.clip(base_esg + np.random.uniform(-8, 8), 10, 95)
            df.loc[idx, 'social_score']        = np.clip(base_esg + np.random.uniform(-6, 6), 10, 95)
            df.loc[idx, 'governance_score']    = np.clip(base_esg + np.random.uniform(-5, 5), 10, 95)

    return df, live_count