# src/config.py

import os
from dotenv import load_dotenv
load_dotenv()

os.environ["USER_AGENT"] = "finance-qa-tool/1.0"

# ── MODEL SETTINGS ─────────────────────────────────────────
OLLAMA_MODEL    = "llama3.1"
EMBEDDING_MODEL = "nomic-embed-text"

# ── PATHS ──────────────────────────────────────────────────
CHROMA_DB_PATH = "./data/db"
RAW_DATA_PATH  = "./data/raw"

# ── CHUNKING ───────────────────────────────────────────────
CHUNK_SIZE    = 512
CHUNK_OVERLAP = 64

# ── RETRIEVAL ──────────────────────────────────────────────
TOP_K_RESULTS = 5

# ── OPTIONAL: NEWS API KEY ─────────────────────────────────
# Free key from https://newsapi.org — 100 calls/day
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# ── FINANCE KNOWLEDGE BASE URLS ────────────────────────────
FINANCE_URLS = [

    # ── Investing Fundamentals ─────────────────────────────
    "https://www.investopedia.com/terms/p/price-earningsratio.asp",
    "https://www.investopedia.com/terms/e/eps.asp",
    "https://www.investopedia.com/terms/m/marketcap.asp",
    "https://www.investopedia.com/terms/d/dividend.asp",
    "https://www.investopedia.com/terms/v/volatility.asp",
    "https://www.investopedia.com/terms/b/beta.asp",
    "https://www.investopedia.com/terms/r/returnoninvestment.asp",
    "https://www.investopedia.com/terms/e/ebitda.asp",
    "https://www.investopedia.com/terms/f/freecashflow.asp",
    "https://www.investopedia.com/terms/b/bookvalue.asp",
    "https://www.investopedia.com/terms/d/debtequityratio.asp",
    "https://www.investopedia.com/terms/p/price-to-book-ratio.asp",
    "https://www.investopedia.com/terms/r/revenue.asp",
    "https://www.investopedia.com/terms/g/grossprofit.asp",
    "https://www.investopedia.com/terms/n/netincome.asp",
    "https://www.investopedia.com/terms/p/profitmargin.asp",

    # ── Trading Concepts ───────────────────────────────────
    "https://www.investopedia.com/terms/s/shortselling.asp",
    "https://www.investopedia.com/terms/s/stoploss.asp",
    "https://www.investopedia.com/terms/l/limitorder.asp",
    "https://www.investopedia.com/terms/m/marketorder.asp",
    "https://www.investopedia.com/terms/s/spreadbetting.asp",
    "https://www.investopedia.com/terms/o/options.asp",
    "https://www.investopedia.com/terms/l/leverage.asp",
    "https://www.investopedia.com/terms/m/margin.asp",
    "https://www.investopedia.com/terms/p/portfolio.asp",
    "https://www.investopedia.com/terms/d/diversification.asp",

    # ── Technical Analysis ─────────────────────────────────
    "https://www.investopedia.com/terms/r/rsi.asp",
    "https://www.investopedia.com/terms/b/bollingerbands.asp",
    "https://www.investopedia.com/terms/m/macd.asp",
    "https://www.investopedia.com/terms/m/movingaverage.asp",
    "https://www.investopedia.com/terms/s/sma.asp",
    "https://www.investopedia.com/terms/e/ema.asp",
    "https://www.investopedia.com/terms/s/supportlevel.asp",
    "https://www.investopedia.com/terms/r/resistance.asp",
    "https://www.investopedia.com/terms/c/candlestick.asp",
    "https://www.investopedia.com/terms/v/volume.asp",

    # ── Investing Strategies ───────────────────────────────
    "https://www.investopedia.com/terms/v/valueinvesting.asp",
    "https://www.investopedia.com/terms/g/growthinvesting.asp",
    "https://www.investopedia.com/terms/i/indexinvesting.asp",
    "https://www.investopedia.com/terms/d/dollarcostaveraging.asp",
    "https://www.investopedia.com/terms/b/buyandhold.asp",
    "https://www.investopedia.com/terms/c/contrarian.asp",

    # ── Market Structure ───────────────────────────────────
    "https://www.investopedia.com/terms/b/bullmarket.asp",
    "https://www.investopedia.com/terms/b/bearmarket.asp",
    "https://www.investopedia.com/terms/m/marketcorrection.asp",
    "https://www.investopedia.com/terms/s/stockmarket.asp",
    "https://www.investopedia.com/terms/i/ipo.asp",
    "https://www.investopedia.com/terms/m/mutualfund.asp",
    "https://www.investopedia.com/terms/e/etf.asp",
    "https://www.investopedia.com/terms/i/index.asp",

    # ── UK / London Stock Exchange Specific ────────────────
    "https://www.investopedia.com/terms/f/ftse.asp",
    "https://www.investopedia.com/terms/i/isa.asp",
    "https://www.investopedia.com/terms/s/sipp.asp",

    # ── Risk Management ────────────────────────────────────
    "https://www.investopedia.com/terms/r/riskmanagement.asp",
    "https://www.investopedia.com/terms/s/systematicrisk.asp",
    "https://www.investopedia.com/terms/u/unsystematicrisk.asp",
    "https://www.investopedia.com/terms/h/hedge.asp",
    "https://www.investopedia.com/terms/a/assetallocation.asp",

    # ── Financial Statements ───────────────────────────────
    "https://www.investopedia.com/terms/i/incomestatement.asp",
    "https://www.investopedia.com/terms/b/balancesheet.asp",
    "https://www.investopedia.com/terms/c/cashflowstatement.asp",
    "https://www.investopedia.com/terms/a/annualreport.asp",
    "https://www.investopedia.com/terms/e/earnings.asp",
    "https://www.investopedia.com/terms/e/earningspershare.asp",
    "https://www.investopedia.com/terms/q/quarterlyearnings.asp",
]