# src/geopolitical.py

import feedparser
import requests
import warnings
warnings.filterwarnings("ignore")

from datetime import datetime, timedelta
from sentiment import vader_score, vader_label

# ── NEWS SOURCES ────────────────────────────────────────────
# All free RSS feeds — no API keys required

RSS_FEEDS = {
    "Reuters World":    "https://feeds.reuters.com/reuters/worldNews",
    "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
    "BBC World":        "http://feeds.bbci.co.uk/news/world/rss.xml",
    "BBC Business":     "http://feeds.bbci.co.uk/news/business/rss.xml",
    "AP Top News":      "https://feeds.apnews.com/rss/apf-topnews",
    "FT Markets":       "https://www.ft.com/rss/home",
}

# ── GEOPOLITICAL THEME → SECTOR MAPPING ─────────────────────
THEME_SECTOR_MAP = {
    # Conflict & defence
    "war":          ["Defense", "Energy", "Cybersecurity"],
    "conflict":     ["Defense", "Energy", "Cybersecurity"],
    "military":     ["Defense", "Aerospace"],
    "nato":         ["Defense", "Aerospace"],
    "sanctions":    ["Energy", "Financials", "Commodities"],
    "russia":       ["Energy", "Defense", "Commodities"],
    "ukraine":      ["Energy", "Defense", "Agriculture"],

    # US-China / trade
    "china":        ["Semiconductors", "Technology", "Rare Earths"],
    "taiwan":       ["Semiconductors", "Technology", "Defense"],
    "tariff":       ["Manufacturing", "Agriculture", "Retail"],
    "trade war":    ["Semiconductors", "Agriculture", "Manufacturing"],

    # Energy
    "oil":          ["Energy", "Airlines", "Transportation"],
    "opec":         ["Energy", "Transportation"],
    "gas":          ["Energy", "Utilities"],
    "energy":       ["Energy", "Renewables", "Utilities"],
    "pipeline":     ["Energy", "Utilities"],

    # Economic policy
    "interest rate":["Financials", "Real Estate", "Utilities"],
    "inflation":    ["Commodities", "Consumer Staples", "Gold"],
    "recession":    ["Consumer Staples", "Healthcare", "Utilities"],
    "fed":          ["Financials", "Real Estate", "Technology"],
    "rate cut":     ["Real Estate", "Technology", "Financials"],

    # Safe havens
    "uncertainty":  ["Gold", "Consumer Staples", "Utilities"],
    "crisis":       ["Gold", "Defense", "Healthcare"],
    "safe haven":   ["Gold", "Consumer Staples", "Utilities"],

    # Tech & AI
    "ai":           ["Technology", "Semiconductors", "Cloud"],
    "semiconductor":["Semiconductors", "Technology"],
    "chip":         ["Semiconductors", "Technology"],

    # Climate & environment
    "climate":      ["Renewables", "Energy", "Agriculture"],
    "green":        ["Renewables", "Utilities"],
    "election":     ["Defense", "Financials", "Energy"],
    "election":     ["Energy", "Financials", "Healthcare"],
}

# ── SECTOR → STOCK UNIVERSE MAPPING ─────────────────────────
SECTOR_STOCKS = {
    "Defense": [
        "LMT",   # Lockheed Martin
        "RTX",   # Raytheon
        "NOC",   # Northrop Grumman
        "GD",    # General Dynamics
        "BA",    # Boeing
        "RR.L",  # Rolls-Royce (UK)
        "BAE.L", # BAE Systems (UK)
        "QQ.L",  # iShares Defence ETF (UK)
    ],
    "Energy": [
        "XOM",    # Exxon Mobil
        "CVX",    # Chevron
        "BP.L",   # BP (UK)
        "SHEL.L", # Shell (UK)
        "TTE",    # TotalEnergies
        "COP",    # ConocoPhillips
        "SLB",    # Schlumberger
        "PSX",    # Phillips 66
    ],
    "Semiconductors": [
        "NVDA",  # Nvidia
        "AMD",   # AMD
        "INTC",  # Intel
        "QCOM",  # Qualcomm
        "ASML",  # ASML
        "TSM",   # TSMC
        "AMAT",  # Applied Materials
        "MU",    # Micron
    ],
    "Technology": [
        "MSFT",  # Microsoft
        "AAPL",  # Apple
        "GOOGL", # Alphabet
        "META",  # Meta
        "CRM",   # Salesforce
        "ORCL",  # Oracle
        "IBM",   # IBM
        "SAP",   # SAP
    ],
    "Renewables": [
        "NEE",   # NextEra Energy
        "ENPH",  # Enphase
        "FSLR",  # First Solar
        "SEDG",  # SolarEdge
        "ORSTED.CO", # Ørsted
        "RNW",   # ReNew Energy
        "SSE.L", # SSE (UK)
        "IBE.MC",# Iberdrola
    ],
    "Gold": [
        "GLD",   # SPDR Gold ETF
        "NEM",   # Newmont
        "GOLD",  # Barrick Gold
        "AEM",   # Agnico Eagle
        "WPM",   # Wheaton Precious Metals
        "ABX",   # Barrick (TSX)
        "AU",    # AngloGold Ashanti
    ],
    "Financials": [
        "JPM",    # JPMorgan
        "BAC",    # Bank of America
        "HSBA.L", # HSBC (UK)
        "BARC.L", # Barclays (UK)
        "LLOY.L", # Lloyds (UK)
        "GS",     # Goldman Sachs
        "MS",     # Morgan Stanley
        "BLK",    # BlackRock
    ],
    "Healthcare": [
        "JNJ",   # Johnson & Johnson
        "UNH",   # UnitedHealth
        "PFE",   # Pfizer
        "MRK",   # Merck
        "AZN.L", # AstraZeneca (UK)
        "GSK.L", # GSK (UK)
        "ABBV",  # AbbVie
        "LLY",   # Eli Lilly
    ],
    "Consumer Staples": [
        "PG",     # Procter & Gamble
        "KO",     # Coca-Cola
        "PEP",    # PepsiCo
        "WMT",    # Walmart
        "ULVR.L", # Unilever (UK)
        "TSCO.L", # Tesco (UK)
        "NESN.SW",# Nestlé
        "MCD",    # McDonald's
    ],
    "Utilities": [
        "NEE",   # NextEra
        "DUK",   # Duke Energy
        "SO",    # Southern Company
        "D",     # Dominion Energy
        "SSE.L", # SSE (UK)
        "NG.L",  # National Grid (UK)
        "AWK",   # American Water Works
    ],
    "Agriculture": [
        "DE",    # John Deere
        "ADM",   # Archer-Daniels-Midland
        "BG",    # Bunge
        "MOS",   # Mosaic (fertilizers)
        "NTR",   # Nutrien
        "CF",    # CF Industries
        "FMC",   # FMC Corp
    ],
    "Aerospace": [
        "BA",   # Boeing
        "AIR.PA",# Airbus
        "LMT",  # Lockheed Martin
        "GE",   # GE Aerospace
        "HEI",  # HEICO
        "TDG",  # TransDigm
        "SPR",  # Spirit AeroSystems
    ],
    "Commodities": [
        "FCX",  # Freeport-McMoRan (copper)
        "RIO",  # Rio Tinto
        "BHP",  # BHP Group
        "VALE", # Vale (iron ore)
        "AA",   # Alcoa (aluminium)
        "NEM",  # Newmont
        "MP",   # MP Materials (rare earths)
    ],
    "Cybersecurity": [
        "CRWD", # CrowdStrike
        "PANW", # Palo Alto Networks
        "ZS",   # Zscaler
        "FTNT", # Fortinet
        "S",    # SentinelOne
        "OKTA", # Okta
        "CYBR", # CyberArk
    ],
}


# ── NEWS FETCHING ────────────────────────────────────────────

def fetch_geopolitical_news(max_articles: int = 50) -> list:
    """
    Fetch headlines from multiple RSS feeds.
    Returns list of article dicts with title, summary, source, score.
    """
    articles = []
    cutoff   = datetime.now() - timedelta(days=3)

    for source_name, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
                title   = entry.get("title", "")
                summary = entry.get("summary", "")
                text    = f"{title} {summary}"
                score   = vader_score(text)

                articles.append({
                    "source":  source_name,
                    "title":   title[:200],
                    "summary": summary[:300],
                    "score":   score,
                    "label":   vader_label(score),
                    "text":    text.lower(),
                })

                if len(articles) >= max_articles:
                    break

        except Exception as e:
            print(f"  ⚠️  Could not fetch {source_name}: {e}")
            continue

    print(f"  ✓ Fetched {len(articles)} news articles")
    return articles


# ── THEME EXTRACTION ─────────────────────────────────────────

def extract_themes(articles: list) -> dict:
    """
    Scan headlines for geopolitical keywords.
    Returns theme → mention_count + sector recommendations.
    """
    theme_counts = {}
    theme_scores = {}

    for article in articles:
        text = article["text"]
        for keyword, sectors in THEME_SECTOR_MAP.items():
            if keyword in text:
                if keyword not in theme_counts:
                    theme_counts[keyword] = 0
                    theme_scores[keyword] = []
                theme_counts[keyword] += 1
                theme_scores[keyword].append(article["score"])

    # Build theme summary
    themes = {}
    for keyword, count in theme_counts.items():
        if count >= 2:  # Only themes with 2+ mentions
            avg_sentiment = sum(theme_scores[keyword]) / len(theme_scores[keyword])
            themes[keyword] = {
                "mentions":      count,
                "avg_sentiment": round(avg_sentiment, 3),
                "sentiment_label": vader_label(avg_sentiment),
                "sectors":       THEME_SECTOR_MAP[keyword],
            }

    # Sort by mentions
    themes = dict(sorted(themes.items(), key=lambda x: x[1]["mentions"], reverse=True))
    return themes


# ── SECTOR RELEVANCE SCORING ─────────────────────────────────

def score_sectors(themes: dict) -> dict:
    """
    Score each sector by how many active themes point to it.
    Returns sector → relevance score.
    """
    sector_scores = {}

    for theme, data in themes.items():
        weight = data["mentions"]
        for sector in data["sectors"]:
            if sector not in sector_scores:
                sector_scores[sector] = 0
            sector_scores[sector] += weight

    # Normalize to 0-100
    if sector_scores:
        max_score = max(sector_scores.values())
        sector_scores = {
            k: round((v / max_score) * 100)
            for k, v in sector_scores.items()
        }

    return dict(sorted(sector_scores.items(), key=lambda x: x[1], reverse=True))


# ── TOP HEADLINES ─────────────────────────────────────────────

def get_top_headlines(articles: list, n: int = 10) -> list:
    """Return top N headlines sorted by absolute sentiment strength."""
    sorted_articles = sorted(
        articles,
        key=lambda x: abs(x["score"]),
        reverse=True,
    )
    return sorted_articles[:n]


# ── MAIN ENTRY POINT ─────────────────────────────────────────

def get_geopolitical_context() -> dict:
    """
    Full geopolitical intelligence pipeline.
    Returns context dict for screener and LLM.
    """
    print("  🌍 Fetching geopolitical news...")

    articles  = fetch_geopolitical_news()
    themes    = extract_themes(articles)
    sectors   = score_sectors(themes)
    headlines = get_top_headlines(articles)

    # Top 3 sectors by relevance
    top_sectors = list(sectors.keys())[:3]

    # Collect relevant tickers for top sectors
    relevant_tickers = []
    for sector in top_sectors:
        tickers = SECTOR_STOCKS.get(sector, [])
        relevant_tickers.extend(tickers)

    # Deduplicate while preserving order
    seen = set()
    unique_tickers = []
    for t in relevant_tickers:
        if t not in seen:
            seen.add(t)
            unique_tickers.append(t)

    return {
        "articles":         articles,
        "themes":           themes,
        "sectors":          sectors,
        "top_sectors":      top_sectors,
        "relevant_tickers": unique_tickers[:25],  # cap at 25
        "headlines":        headlines,
        "fetched_at":       datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
    }


def format_geopolitical_context(geo: dict) -> str:
    """Format geopolitical data as readable context for the LLM."""
    themes  = geo.get("themes", {})
    sectors = geo.get("sectors", {})
    headlines = geo.get("headlines", [])

    top_themes = list(themes.items())[:8]
    top_sectors = list(sectors.items())[:6]
    top_headlines = headlines[:8]

    theme_lines = "\n".join(
        f"  • {k}: {v['mentions']} mentions — "
        f"{v['sentiment_label']} (sentiment: {v['avg_sentiment']}) → "
        f"sectors: {', '.join(v['sectors'][:3])}"
        for k, v in top_themes
    )

    sector_lines = "\n".join(
        f"  • {k}: relevance score {v}/100"
        for k, v in top_sectors
    )

    headline_lines = "\n".join(
        f"  [{a['label']}] {a['source']}: {a['title']}"
        for a in top_headlines
    )

    return f"""
{'━' * 55}
GEOPOLITICAL CONTEXT (live news analysis)
{'━' * 55}
Active Themes (by news volume):
{theme_lines}

Most Relevant Sectors Right Now:
{sector_lines}

Key Headlines:
{headline_lines}

Data fetched: {geo.get('fetched_at', '')}
"""