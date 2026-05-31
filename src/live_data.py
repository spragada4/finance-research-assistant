# src/live_data.py

import re
import numpy as np
import yfinance as yf
from datetime import datetime

# ── TICKER DETECTION ────────────────────────────────────────

TICKER_BLACKLIST = {
    "I", "A", "ME", "IT", "IS", "AT", "BE", "DO",
    "GO", "IF", "IN", "OF", "ON", "OR", "SO", "TO",
    "UP", "US", "UK", "AI", "CEO", "CFO", "COO",
    "GDP", "FCA", "ISA", "ETF", "IPO", "RSI", "EMA",
    "SMA", "PE", "EPS", "ROE", "MA",
}

COMPANY_NAME_MAP = {
    "apple":         "AAPL",
    "microsoft":     "MSFT",
    "google":        "GOOGL",
    "alphabet":      "GOOGL",
    "amazon":        "AMZN",
    "tesla":         "TSLA",
    "nvidia":        "NVDA",
    "meta":          "META",
    "facebook":      "META",
    "netflix":       "NFLX",
    "barclays":      "BARC.L",
    "lloyds":        "LLOY.L",
    "hsbc":          "HSBA.L",
    "bp":            "BP.L",
    "shell":         "SHEL.L",
    "vodafone":      "VOD.L",
    "astrazeneca":   "AZN.L",
    "tesco":         "TSCO.L",
    "rolls royce":   "RR.L",
    "natwest":       "NWG.L",
    "aviva":         "AV.L",
    "diageo":        "DGE.L",
    "unilever":      "ULVR.L",
    "gsk":           "GSK.L",
    "rio tinto":     "RIO.L",
    "bt":            "BT-A.L",
    "marks spencer": "MKS.L",
    "sainsbury":     "SBRY.L",
    "next":          "NXT.L",
    "standard chartered": "STAN.L",
}

def detect_tickers(question: str) -> list:
    """Detect stock tickers from a natural language question."""
    tickers = []

    # $TICKER format
    dollar_matches = re.findall(r'\$([A-Z]{1,5})', question)
    tickers.extend(dollar_matches)

    # ALL CAPS 2-5 char words not in blacklist
    upper_matches = re.findall(r'\b([A-Z]{2,5})\b', question)
    for m in upper_matches:
        if m not in TICKER_BLACKLIST and m not in tickers:
            tickers.append(m)

    # Company name → ticker
    question_lower = question.lower()
    for name, ticker in COMPANY_NAME_MAP.items():
        if name in question_lower and ticker not in tickers:
            tickers.append(ticker)

    return tickers[:2]  # max 2 stocks per query


# ── PRICE & FUNDAMENTALS ────────────────────────────────────

def format_large_number(n) -> str:
    if n is None:
        return "N/A"
    try:
        n = float(n)
        if n >= 1_000_000_000_000:
            return f"{n / 1_000_000_000_000:.2f}T"
        if n >= 1_000_000_000:
            return f"{n / 1_000_000_000:.2f}B"
        if n >= 1_000_000:
            return f"{n / 1_000_000:.2f}M"
        return f"{n:,.0f}"
    except:
        return str(n)


def get_stock_snapshot(ticker: str) -> dict:
    """Fetch current fundamentals and analyst data."""
    try:
        stock = yf.Ticker(ticker)
        info  = stock.info

        if not info or "currentPrice" not in info:
            fi = stock.fast_info
            return {
                "ticker":         ticker.upper(),
                "name":           ticker.upper(),
                "price":          round(fi.last_price, 2) if fi.last_price else "N/A",
                "currency":       getattr(fi, "currency", "N/A"),
                "market_cap":     format_large_number(getattr(fi, "market_cap", None)),
                "pe_ratio":       "N/A",
                "forward_pe":     "N/A",
                "eps":            "N/A",
                "week_52_high":   round(fi.fifty_two_week_high, 2) if fi.fifty_two_week_high else "N/A",
                "week_52_low":    round(fi.fifty_two_week_low,  2) if fi.fifty_two_week_low  else "N/A",
                "dividend_yield": "N/A",
                "sector":         "N/A",
                "industry":       "N/A",
                "analyst_target": "N/A",
                "recommendation": "N/A",
                "revenue":        "N/A",
                "profit_margin":  "N/A",
                "debt_to_equity": "N/A",
                "roe":            "N/A",
                "summary":        "No detailed info available.",
                "fetched_at":     datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
            }

        return {
            "ticker":         ticker.upper(),
            "name":           info.get("longName", ticker),
            "price":          info.get("currentPrice", info.get("regularMarketPrice", "N/A")),
            "currency":       info.get("currency", "N/A"),
            "market_cap":     format_large_number(info.get("marketCap")),
            "pe_ratio":       round(info.get("trailingPE", 0), 2) or "N/A",
            "forward_pe":     round(info.get("forwardPE", 0), 2) or "N/A",
            "eps":            info.get("trailingEps", "N/A"),
            "week_52_high":   info.get("fiftyTwoWeekHigh", "N/A"),
            "week_52_low":    info.get("fiftyTwoWeekLow",  "N/A"),
            "dividend_yield": f"{round(info.get('dividendYield', 0) * 100, 2)}%" if info.get("dividendYield") else "None",
            "sector":         info.get("sector", "N/A"),
            "industry":       info.get("industry", "N/A"),
            "analyst_target": info.get("targetMeanPrice", "N/A"),
            "recommendation": info.get("recommendationKey", "N/A").upper().replace("_", " "),
            "revenue":        format_large_number(info.get("totalRevenue")),
            "profit_margin":  f"{round(info.get('profitMargins', 0) * 100, 1)}%" if info.get("profitMargins") else "N/A",
            "debt_to_equity": info.get("debtToEquity", "N/A"),
            "roe":            f"{round(info.get('returnOnEquity', 0) * 100, 1)}%" if info.get("returnOnEquity") else "N/A",
            "summary":        (info.get("longBusinessSummary", "N/A") or "")[:400] + "...",
            "fetched_at":     datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
        }

    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_price_history(ticker: str, period: str = "6mo") -> str:
    """Plain-English summary of price movement."""
    try:
        hist = yf.Ticker(ticker).history(period=period)
        if hist.empty:
            return "No historical data available."

        start   = hist["Close"].iloc[0]
        end     = hist["Close"].iloc[-1]
        high    = hist["High"].max()
        low     = hist["Low"].min()
        chg     = ((end - start) / start) * 100
        avg_vol = hist["Volume"].mean()

        return (
            f"Over {period}: opened at {start:.2f}, now {end:.2f} "
            f"({chg:+.1f}%). Range: high {high:.2f}, low {low:.2f}. "
            f"Avg daily volume: {format_large_number(int(avg_vol))}."
        )
    except Exception as e:
        return f"Could not fetch history: {e}"


def get_recent_news(ticker: str) -> str:
    """Fetch recent news headlines."""
    try:
        news = yf.Ticker(ticker).news[:5] or []
        if not news:
            return "No recent news found."
        headlines = [f"• {item['title']}" for item in news if item.get("title")]
        return "\n".join(headlines) if headlines else "No headlines found."
    except Exception as e:
        return f"Could not fetch news: {e}"


# ── TECHNICAL INDICATORS ────────────────────────────────────

def calculate_technicals(ticker: str) -> dict:
    """
    Calculate RSI, MACD, Bollinger Bands, and Moving Averages.
    Returns signals and interpreted plain-English conclusions.
    """
    try:
        hist = yf.Ticker(ticker).history(period="6mo")

        if hist.empty or len(hist) < 26:
            return {"error": "Insufficient data for technical analysis"}

        close   = hist["Close"]
        current = close.iloc[-1]

        # ── Moving Averages ───────────────────────────────
        sma_20 = close.rolling(window=20).mean().iloc[-1]
        sma_50 = close.rolling(window=50).mean().iloc[-1] if len(close) >= 50 else None
        ema_12 = close.ewm(span=12, adjust=False).mean().iloc[-1]
        ema_26 = close.ewm(span=26, adjust=False).mean().iloc[-1]

        # ── RSI (14-period) ───────────────────────────────
        delta  = close.diff()
        gain   = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss   = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
        rs     = gain / loss
        rsi    = float((100 - (100 / (1 + rs))).iloc[-1])

        # ── MACD ─────────────────────────────────────────
        macd_line   = float(ema_12 - ema_26)
        signal_line = float(
            close.ewm(span=12, adjust=False).mean().ewm(span=26, adjust=False).mean()
            .ewm(span=9, adjust=False).mean().iloc[-1]
        )
        macd_hist = macd_line - signal_line

        # ── Bollinger Bands (20-day) ──────────────────────
        sma_series  = close.rolling(20).mean()
        std_series  = close.rolling(20).std()
        upper_band  = float((sma_series + 2 * std_series).iloc[-1])
        lower_band  = float((sma_series - 2 * std_series).iloc[-1])

        # ── Volume trend ──────────────────────────────────
        avg_vol_20  = hist["Volume"].rolling(20).mean().iloc[-1]
        latest_vol  = hist["Volume"].iloc[-1]
        vol_signal  = (
            "Above average — strong conviction in recent move"
            if latest_vol > avg_vol_20 * 1.2
            else "Below average — weak conviction in recent move"
            if latest_vol < avg_vol_20 * 0.8
            else "Average — no notable volume divergence"
        )

        # ── Interpret signals ─────────────────────────────
        rsi_signal = (
            "Oversold (below 30) — historically a potential mean-reversion zone"
            if rsi < 30 else
            "Overbought (above 70) — historically a potential pullback zone"
            if rsi > 70 else
            f"Neutral ({rsi:.1f}) — no extreme reading"
        )

        if sma_50:
            ma_signal = (
                "Bullish — price above both SMA20 and SMA50"
                if current > sma_20 > sma_50 else
                "Bearish — price below both SMA20 and SMA50"
                if current < sma_20 < sma_50 else
                "Mixed — price between the two moving averages"
            )
        else:
            ma_signal = (
                "Bullish — price above SMA20" if current > sma_20
                else "Bearish — price below SMA20"
            )

        bb_signal = (
            "Price near upper Bollinger Band — potentially overbought"
            if current >= upper_band * 0.98 else
            "Price near lower Bollinger Band — potentially oversold"
            if current <= lower_band * 1.02 else
            "Price within Bollinger Bands — neutral range"
        )

        macd_signal = (
            "Bullish — MACD line above signal line (positive momentum)"
            if macd_line > signal_line else
            "Bearish — MACD line below signal line (negative momentum)"
        )

        return {
            "current_price": round(float(current), 2),
            "sma_20":        round(float(sma_20), 2),
            "sma_50":        round(float(sma_50), 2) if sma_50 else "N/A",
            "ema_12":        round(float(ema_12), 2),
            "ema_26":        round(float(ema_26), 2),
            "rsi":           round(rsi, 1),
            "rsi_signal":    rsi_signal,
            "macd_line":     round(macd_line, 4),
            "signal_line":   round(signal_line, 4),
            "macd_hist":     round(macd_hist, 4),
            "macd_signal":   macd_signal,
            "upper_band":    round(upper_band, 2),
            "lower_band":    round(lower_band, 2),
            "bb_signal":     bb_signal,
            "ma_signal":     ma_signal,
            "volume_signal": vol_signal,
        }

    except Exception as e:
        return {"error": f"Technical analysis failed: {e}"}


# ── COMPOSITE SCORING ───────────────────────────────────────

def calculate_composite_score(snapshot: dict, technicals: dict) -> dict:
    """
    Score a stock 0-100 across 5 dimensions.
    Returns score, signal label, breakdown, and reasons.
    NOT a buy/sell recommendation — a structured research summary.
    """
    scores  = {}
    reasons = []

    # ── 1. Valuation (P/E ratio) ──────────────────────────
    try:
        pe = float(snapshot.get("pe_ratio", 0) or 0)
        if 0 < pe < 15:
            scores["valuation"] = 80
            reasons.append(f"Low P/E ({pe}) — potentially undervalued vs market average")
        elif pe < 25:
            scores["valuation"] = 60
            reasons.append(f"Moderate P/E ({pe}) — in the fairly valued range")
        elif pe < 40:
            scores["valuation"] = 35
            reasons.append(f"High P/E ({pe}) — priced for significant growth")
        elif pe >= 40:
            scores["valuation"] = 15
            reasons.append(f"Very high P/E ({pe}) — market expects exceptional growth")
        else:
            scores["valuation"] = 50
            reasons.append("P/E not available — valuation neutral")
    except:
        scores["valuation"] = 50
        reasons.append("P/E not available")

    # ── 2. Momentum (RSI) ─────────────────────────────────
    rsi = technicals.get("rsi", 50)
    if isinstance(rsi, (int, float)):
        if rsi < 30:
            scores["momentum"] = 80
            reasons.append(f"RSI oversold ({rsi}) — historically signals mean reversion")
        elif rsi < 45:
            scores["momentum"] = 65
            reasons.append(f"RSI in lower neutral zone ({rsi})")
        elif rsi < 60:
            scores["momentum"] = 50
            reasons.append(f"RSI in balanced neutral zone ({rsi})")
        elif rsi < 70:
            scores["momentum"] = 35
            reasons.append(f"RSI in upper neutral zone ({rsi})")
        else:
            scores["momentum"] = 15
            reasons.append(f"RSI overbought ({rsi}) — potential pullback zone")
    else:
        scores["momentum"] = 50

    # ── 3. Trend (Moving Averages) ────────────────────────
    ma_signal = technicals.get("ma_signal", "")
    if "Bullish" in str(ma_signal):
        scores["trend"] = 75
        reasons.append("Uptrend confirmed — price above both moving averages")
    elif "Bearish" in str(ma_signal):
        scores["trend"] = 25
        reasons.append("Downtrend signal — price below both moving averages")
    else:
        scores["trend"] = 50
        reasons.append("Mixed trend — no clear directional signal from MAs")

    # ── 4. Analyst Consensus ──────────────────────────────
    rec = str(snapshot.get("recommendation", "")).upper()
    rec_score_map = {
        "STRONG BUY": 90,
        "BUY":        75,
        "HOLD":       50,
        "UNDERPERFORM": 30,
        "SELL":       15,
    }
    scores["analyst"] = rec_score_map.get(rec, 50)
    reasons.append(
        f"Analyst consensus: {rec or 'Not available'} "
        f"(target: {snapshot.get('analyst_target', 'N/A')})"
    )

    # ── 5. Income / Dividend ──────────────────────────────
    div = str(snapshot.get("dividend_yield", "None"))
    if div not in ("None", "N/A", "0.0%", ""):
        scores["income"] = 70
        reasons.append(f"Pays dividend ({div}) — income component present")
    else:
        scores["income"] = 40
        reasons.append("No dividend — purely a growth/capital gain play")

    # ── Composite ─────────────────────────────────────────
    composite = round(sum(scores.values()) / len(scores), 1)

    if composite >= 70:
        signal = "Strong research interest — multiple positive signals"
    elif composite >= 55:
        signal = "Moderate research interest — mixed signals overall"
    elif composite >= 40:
        signal = "Cautious signals — more negative than positive indicators"
    else:
        signal = "Weak signals — most indicators pointing negatively"

    return {
        "composite_score": composite,
        "signal":          signal,
        "breakdown": {
            "Valuation":  scores["valuation"],
            "Momentum":   scores["momentum"],
            "Trend":      scores["trend"],
            "Analyst":    scores["analyst"],
            "Income":     scores["income"],
        },
        "reasons": reasons,
    }


# ── FULL CONTEXT BUILDER ────────────────────────────────────

def format_live_context(tickers: list) -> str:
    """Build complete formatted context for all detected tickers."""
    if not tickers:
        return "No specific stock ticker detected in this question."

    sections = []

    for ticker in tickers:
        snap        = get_stock_snapshot(ticker)
        history     = get_price_history(ticker)
        news        = get_recent_news(ticker)
        technicals  = calculate_technicals(ticker)
        score_data  = calculate_composite_score(snap, technicals)

        if "error" in snap:
            sections.append(f"[{ticker}] Could not fetch data: {snap['error']}")
            continue

        tech_section = ""
        if "error" not in technicals:
            tech_section = f"""
Technical Indicators:
  RSI (14):          {technicals.get('rsi')} — {technicals.get('rsi_signal')}
  MACD:              {technicals.get('macd_signal')}
  Moving Averages:   {technicals.get('ma_signal')}
  Bollinger Bands:   {technicals.get('bb_signal')}
  Volume:            {technicals.get('volume_signal')}
  SMA 20 / SMA 50:   {technicals.get('sma_20')} / {technicals.get('sma_50')}
  Upper / Lower BB:  {technicals.get('upper_band')} / {technicals.get('lower_band')}"""
        else:
            tech_section = f"\nTechnical Indicators: {technicals.get('error')}"

        score_section = f"""
Composite Research Score: {score_data['composite_score']}/100
Signal: {score_data['signal']}
Breakdown:
  Valuation score:  {score_data['breakdown']['Valuation']}/100
  Momentum score:   {score_data['breakdown']['Momentum']}/100
  Trend score:      {score_data['breakdown']['Trend']}/100
  Analyst score:    {score_data['breakdown']['Analyst']}/100
  Income score:     {score_data['breakdown']['Income']}/100
Key Reasons:
{chr(10).join('  • ' + r for r in score_data['reasons'])}"""

        section = f"""
{'━' * 55}
{snap['ticker']} — {snap['name']}
{'━' * 55}
Fundamentals:
  Price:            {snap['price']} {snap['currency']}
  Market Cap:       {snap['market_cap']}
  P/E (TTM):        {snap['pe_ratio']}  |  Forward P/E: {snap['forward_pe']}
  EPS:              {snap['eps']}
  52-Week Range:    {snap['week_52_low']} → {snap['week_52_high']}
  Dividend Yield:   {snap['dividend_yield']}
  Sector:           {snap['sector']} / {snap['industry']}
  Revenue:          {snap['revenue']}
  Profit Margin:    {snap['profit_margin']}
  Debt/Equity:      {snap['debt_to_equity']}
  ROE:              {snap['roe']}
  Analyst Target:   {snap['analyst_target']}
  Analyst View:     {snap['recommendation']}
Price History:      {history}
{tech_section}
{score_section}
Recent News:
{news}
Data fetched: {snap['fetched_at']}
"""
        sections.append(section)

    return "\n".join(sections)