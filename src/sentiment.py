# src/sentiment.py

import os
import re
import requests
import warnings
warnings.filterwarnings("ignore")

from datetime import datetime

# ── VADER ───────────────────────────────────────────────────
try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    _vader = SentimentIntensityAnalyzer()
    VADER_AVAILABLE = True
except Exception:
    VADER_AVAILABLE = False


def vader_score(text: str) -> float:
    """Score text from -1 (very negative) to +1 (very positive)."""
    if not VADER_AVAILABLE or not text:
        return 0.0
    return _vader.polarity_scores(str(text))["compound"]


def vader_label(score: float) -> str:
    if score >=  0.5: return "Very Bullish"
    if score >=  0.1: return "Bullish"
    if score >= -0.1: return "Neutral"
    if score >= -0.5: return "Bearish"
    return "Very Bearish"


# ── STOCKTWITS ──────────────────────────────────────────────

def get_stocktwits_sentiment(ticker: str) -> dict:
    """
    Fetch StockTwits stream for a ticker.
    No API key required for basic access.
    """
    clean_ticker = ticker.replace(".L", "").replace("-", ".")
    try:
        url      = f"https://api.stocktwits.com/api/2/streams/symbol/{clean_ticker}.json"
        headers  = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data     = response.json()
            messages = data.get("messages", [])

            bullish    = 0
            bearish    = 0
            neutral    = 0
            sentiments = []

            for msg in messages:
                entities  = msg.get("entities", {})
                sentiment = entities.get("sentiment", {})
                basic     = sentiment.get("basic") if sentiment else None

                if basic == "Bullish":
                    bullish += 1
                elif basic == "Bearish":
                    bearish += 1
                else:
                    neutral += 1

                body  = msg.get("body", "")
                score = vader_score(body)
                sentiments.append(score)

            total       = bullish + bearish + neutral or 1
            avg_vader   = sum(sentiments) / len(sentiments) if sentiments else 0.0
            bullish_pct = round((bullish / total) * 100, 1)
            bearish_pct = round((bearish / total) * 100, 1)

            signal = (
                "Strongly Bullish" if bullish_pct > 65 else
                "Bullish"          if bullish_pct > 55 else
                "Strongly Bearish" if bearish_pct > 65 else
                "Bearish"          if bearish_pct > 55 else
                "Mixed / Neutral"
            )

            return {
                "source":      "StockTwits",
                "ticker":      clean_ticker,
                "total_msgs":  total,
                "bullish":     bullish,
                "bearish":     bearish,
                "neutral":     neutral,
                "bullish_pct": bullish_pct,
                "bearish_pct": bearish_pct,
                "vader_avg":   round(avg_vader, 3),
                "signal":      signal,
                "available":   True,
            }

        elif response.status_code == 404:
            return {
                "source":    "StockTwits",
                "ticker":    clean_ticker,
                "available": False,
                "note":      "Ticker not found on StockTwits",
            }
        else:
            return {
                "source":    "StockTwits",
                "available": False,
                "note":      f"API returned {response.status_code}",
            }

    except Exception as e:
        return {"source": "StockTwits", "available": False, "note": str(e)}


# ── FEAR & GREED INDEX ──────────────────────────────────────

def get_fear_greed_index() -> dict:
    """Fetch CNN Fear & Greed Index. 0=Extreme Fear, 100=Extreme Greed."""
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer":    "https://www.cnn.com/markets/fear-and-greed",
        }
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code == 200:
            data       = resp.json()
            score      = data.get("fear_and_greed", {}).get("score", 50)
            rating     = data.get("fear_and_greed", {}).get("rating", "Neutral")
            prev       = data.get("fear_and_greed_historical", {})
            prev_week  = prev.get("previous_1_week",  {}).get("score", score)
            prev_month = prev.get("previous_1_month", {}).get("score", score)

            direction = (
                "Rising — market becoming greedier"
                if float(score) > float(prev_week) else
                "Falling — market becoming more fearful"
            )

            label = (
                "Extreme Fear"  if float(score) < 25 else
                "Fear"          if float(score) < 45 else
                "Neutral"       if float(score) < 55 else
                "Greed"         if float(score) < 75 else
                "Extreme Greed"
            )

            context = (
                "Extreme Fear — historically a contrarian buy signal for long-term investors"
                if float(score) < 25 else
                "Fear present — investors cautious, potentially presenting value opportunities"
                if float(score) < 45 else
                "Balanced sentiment — neither euphoric nor panicked"
                if float(score) < 55 else
                "Greed present — markets running warm, valuations may be stretched"
                if float(score) < 75 else
                "Extreme Greed — historically a warning signal, markets may be overextended"
            )

            return {
                "source":     "CNN Fear & Greed",
                "available":  True,
                "score":      round(float(score), 1),
                "label":      label,
                "rating":     rating,
                "prev_week":  round(float(prev_week), 1),
                "prev_month": round(float(prev_month), 1),
                "direction":  direction,
                "context":    context,
            }

        return {
            "source":    "CNN Fear & Greed",
            "available": False,
            "note":      f"API returned {resp.status_code}",
        }

    except Exception as e:
        return {"source": "CNN Fear & Greed", "available": False, "note": str(e)}


# ── GOOGLE TRENDS ───────────────────────────────────────────

def get_google_trends(ticker: str, company_name: str = "") -> dict:
    """
    Fetch Google Trends data.
    Rising search interest = increasing retail attention.
    """
    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl="en-GB", tz=0, timeout=(10, 25))
        keyword  = company_name if company_name else ticker

        pytrends.build_payload(
            [keyword],
            cat=7,
            timeframe="today 3-m",
            geo="",
        )

        data = pytrends.interest_over_time()

        if data.empty:
            return {
                "source":    "Google Trends",
                "available": False,
                "note":      "No trend data found",
            }

        values  = data[keyword].tolist()
        current = values[-1]
        avg_4w  = sum(values[-4:]) / 4
        avg_12w = sum(values) / len(values)

        trend = (
            "Surging — search interest well above recent average"
            if current > avg_4w * 1.5 else
            "Rising — search interest above recent average"
            if current > avg_4w * 1.1 else
            "Declining — search interest below recent average"
            if current < avg_4w * 0.8 else
            "Stable — search interest in line with recent average"
        )

        return {
            "source":    "Google Trends",
            "available": True,
            "keyword":   keyword,
            "current":   current,
            "avg_4w":    round(avg_4w, 1),
            "avg_12w":   round(avg_12w, 1),
            "trend":     trend,
            "note":      "100 = peak search interest. Relative scale.",
        }

    except Exception as e:
        return {"source": "Google Trends", "available": False, "note": str(e)}


# ── POLYMARKET ──────────────────────────────────────────────

def get_polymarket_sentiment(company_name: str, ticker: str = "") -> dict:
    """
    Search Polymarket Gamma API for prediction markets
    related to a company or ticker.
    """
    try:
        search_term = company_name or ticker
        url     = "https://gamma-api.polymarket.com/markets"
        params  = {
            "search": search_term,
            "active": "true",
            "closed": "false",
            "limit":  5,
        }
        headers  = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code != 200:
            return {
                "source":    "Polymarket",
                "available": False,
                "note":      f"API returned {response.status_code}",
            }

        markets = response.json()

        if not markets:
            return {
                "source":    "Polymarket",
                "available": True,
                "found":     False,
                "note":      f"No active prediction markets found for {search_term}",
            }

        processed = []
        for m in markets[:5]:
            outcomes       = m.get("outcomePrices", [])
            outcome_labels = m.get("outcomes", [])
            try:
                probs = [round(float(p) * 100, 1) for p in outcomes]
            except:
                probs = []

            processed.append({
                "question": m.get("question", ""),
                "volume":   m.get("volume", 0),
                "end_date": m.get("endDate", ""),
                "outcomes": list(zip(outcome_labels, probs)) if outcome_labels and probs else [],
                "url":      f"https://polymarket.com/event/{m.get('slug', '')}",
            })

        return {
            "source":    "Polymarket",
            "available": True,
            "found":     True,
            "markets":   processed,
            "note":      "Prediction market probabilities reflect crowd consensus",
        }

    except Exception as e:
        return {"source": "Polymarket", "available": False, "note": str(e)}


# ── COMPOSITE SENTIMENT SCORE ───────────────────────────────

def calculate_sentiment_composite(
    stocktwits: dict,
    fear_greed: dict,
    trends:     dict,
) -> dict:
    """
    Combine sentiment sources into a single 0-100 score.
    Weights: StockTwits 40%, Fear & Greed 35%, Google Trends 25%
    """
    scores  = {}
    sources = []

    # StockTwits (40%)
    if stocktwits.get("available") and stocktwits.get("bullish_pct") is not None:
        scores["stocktwits"] = stocktwits["bullish_pct"]
        sources.append(
            f"StockTwits: {stocktwits['bullish_pct']}% bullish "
            f"({stocktwits['total_msgs']} messages) — {stocktwits['signal']}"
        )
    else:
        scores["stocktwits"] = 50
        sources.append(f"StockTwits: unavailable — {stocktwits.get('note', '')}")

    # Fear & Greed (35%)
    if fear_greed.get("available"):
        scores["fear_greed"] = float(fear_greed["score"])
        sources.append(
            f"Fear & Greed: {fear_greed['score']}/100 "
            f"({fear_greed['label']}) — {fear_greed['direction']}"
        )
    else:
        scores["fear_greed"] = 50
        sources.append("Fear & Greed: unavailable")

    # Google Trends (25%)
    if trends.get("available"):
        current  = trends.get("current", 50)
        avg_12w  = trends.get("avg_12w", 50)
        interest = min((current / max(avg_12w, 1)) * 50, 100)
        scores["trends"] = round(interest, 1)
        sources.append(
            f"Google Trends: {current}/100 — {trends['trend']}"
        )
    else:
        scores["trends"] = 50
        sources.append("Google Trends: unavailable")

    weights = {
        "stocktwits": 0.40,
        "fear_greed": 0.35,
        "trends":     0.25,
    }

    composite = round(sum(scores[k] * weights[k] for k in scores), 1)

    label = (
        "Very Bullish Sentiment" if composite >= 70 else
        "Bullish Sentiment"      if composite >= 58 else
        "Neutral / Mixed"        if composite >= 42 else
        "Bearish Sentiment"      if composite >= 30 else
        "Very Bearish Sentiment"
    )

    return {
        "composite": composite,
        "label":     label,
        "breakdown": scores,
        "sources":   sources,
    }


# ── MAIN ENTRY POINT ────────────────────────────────────────

def get_full_sentiment(ticker: str, company_name: str = "") -> dict:
    """
    Run all sentiment sources for a ticker.
    Returns unified sentiment package for LLM and UI.
    """
    print(f"  📡 Fetching sentiment for {ticker}...")

    stocktwits = get_stocktwits_sentiment(ticker)
    fear_greed = get_fear_greed_index()
    trends     = get_google_trends(ticker, company_name)
    polymarket = get_polymarket_sentiment(company_name or ticker, ticker)
    composite  = calculate_sentiment_composite(stocktwits, fear_greed, trends)

    return {
        "ticker":     ticker,
        "stocktwits": stocktwits,
        "fear_greed": fear_greed,
        "trends":     trends,
        "polymarket": polymarket,
        "composite":  composite,
        "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
    }


def format_sentiment_context(sentiment: dict) -> str:
    """Format sentiment data as readable context string for the LLM."""
    if not sentiment:
        return "Sentiment data unavailable."

    comp   = sentiment.get("composite", {})
    st     = sentiment.get("stocktwits", {})
    fg     = sentiment.get("fear_greed", {})
    trends = sentiment.get("trends", {})
    poly   = sentiment.get("polymarket", {})

    poly_section = ""
    if poly.get("found") and poly.get("markets"):
        poly_section = "\nPolymarket Prediction Markets:\n"
        for m in poly["markets"][:3]:
            poly_section += f"  • {m['question']}\n"
            for outcome, prob in m.get("outcomes", []):
                poly_section += f"    {outcome}: {prob}%\n"
    elif poly.get("available"):
        poly_section = f"\nPolymarket: {poly.get('note', 'No markets found')}"

    return f"""
{'━' * 55}
PUBLIC SENTIMENT — {sentiment.get('ticker', '')}
{'━' * 55}
Composite Sentiment Score: {comp.get('composite', 'N/A')}/100
Overall Signal: {comp.get('label', 'N/A')}

Breakdown:
  StockTwits score:    {comp.get('breakdown', {}).get('stocktwits', 'N/A')}/100 (weight: 40%)
  Fear & Greed score:  {comp.get('breakdown', {}).get('fear_greed', 'N/A')}/100 (weight: 35%)
  Google Trends score: {comp.get('breakdown', {}).get('trends',     'N/A')}/100 (weight: 25%)

StockTwits ({st.get('total_msgs', 0)} messages):
  {st.get('bullish_pct', 'N/A')}% Bullish / {st.get('bearish_pct', 'N/A')}% Bearish
  Signal: {st.get('signal', 'N/A')}
  VADER avg: {st.get('vader_avg', 'N/A')}

CNN Fear & Greed: {fg.get('score', 'N/A')}/100 ({fg.get('label', 'N/A')})
  {fg.get('context', '')}
  vs last week: {fg.get('prev_week', 'N/A')} | vs last month: {fg.get('prev_month', 'N/A')}
  Direction: {fg.get('direction', 'N/A')}

Google Trends — {trends.get('keyword', '')}:
  Current: {trends.get('current', 'N/A')}/100
  {trends.get('trend', 'N/A')}

⚠️ Note: High bullish sentiment can signal a crowded trade
just as much as genuine strength. Always use alongside
fundamentals and technicals — never in isolation.
{poly_section}
Fetched: {sentiment.get('fetched_at', '')}
"""