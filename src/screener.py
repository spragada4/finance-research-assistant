# src/screener.py

import yfinance as yf
from datetime import datetime
from live_data import (
    get_stock_snapshot,
    calculate_technicals,
    calculate_composite_score,
    format_large_number,
)

# ── BATCH SCREENER ───────────────────────────────────────────

def screen_stocks(
    tickers:           list,
    top_n:             int = 5,
    min_price:         float = 1.0,
    geopolitical_context: dict = None,
) -> list:
    """
    Screen a list of tickers and return the top N scored stocks.
    Optionally boosts scores for sectors relevant to geopolitical themes.
    """
    print(f"  🔍 Screening {len(tickers)} stocks...")
    results = []

    for ticker in tickers:
        try:
            snap       = get_stock_snapshot(ticker)
            technicals = calculate_technicals(ticker)
            score_data = calculate_composite_score(snap, technicals)

            # Skip if data fetch failed
            if "error" in snap:
                continue

            # Skip penny stocks and very low liquidity
            price = snap.get("price", 0)
            try:
                if float(price) < min_price:
                    continue
            except:
                continue

            # Geopolitical relevance boost
            geo_boost = 0
            geo_sector = "N/A"
            if geopolitical_context:
                sector = snap.get("sector", "")
                sectors_scored = geopolitical_context.get("sectors", {})
                # Fuzzy match sector to our keys
                for geo_sec, relevance in sectors_scored.items():
                    if (geo_sec.lower() in sector.lower() or
                            sector.lower() in geo_sec.lower()):
                        geo_boost  = relevance * 0.15  # up to +15 points
                        geo_sector = geo_sec
                        break

            # Final score = composite + geo boost
            raw_score  = score_data["composite_score"]
            final_score = min(100, round(raw_score + geo_boost, 1))

            results.append({
                "ticker":      ticker,
                "name":        snap.get("name", ticker),
                "price":       price,
                "currency":    snap.get("currency", ""),
                "sector":      snap.get("sector", "N/A"),
                "industry":    snap.get("industry", "N/A"),
                "market_cap":  snap.get("market_cap", "N/A"),
                "pe_ratio":    snap.get("pe_ratio", "N/A"),
                "dividend":    snap.get("dividend_yield", "None"),
                "analyst":     snap.get("recommendation", "N/A"),
                "target":      snap.get("analyst_target", "N/A"),
                "week_52_high":snap.get("week_52_high", "N/A"),
                "week_52_low": snap.get("week_52_low", "N/A"),
                "rsi":         technicals.get("rsi", "N/A"),
                "rsi_signal":  technicals.get("rsi_signal", "N/A"),
                "ma_signal":   technicals.get("ma_signal", "N/A"),
                "macd_signal": technicals.get("macd_signal", "N/A"),
                "composite":   raw_score,
                "geo_boost":   round(geo_boost, 1),
                "geo_sector":  geo_sector,
                "final_score": final_score,
                "reasons":     score_data.get("reasons", []),
                "signal":      score_data.get("signal", ""),
            })

        except Exception as e:
            print(f"     ✗ {ticker}: {e}")
            continue

    # Sort by final score descending
    results = sorted(results, key=lambda x: x["final_score"], reverse=True)

    print(f"  ✓ Screened {len(results)} stocks successfully")
    return results[:top_n]


def format_screener_results(results: list, geo: dict = None) -> str:
    """Format screener results as context string for the LLM."""
    if not results:
        return "No stocks passed the screening criteria."

    lines = ["SCREENER RESULTS — TOP STOCKS BY COMPOSITE SCORE\n" + "━" * 55]

    for i, stock in enumerate(results, 1):
        geo_note = ""
        if stock.get("geo_boost", 0) > 0:
            geo_note = (
                f"\n  Geopolitical boost: +{stock['geo_boost']} pts "
                f"(sector '{stock['geo_sector']}' is currently relevant)"
            )

        lines.append(f"""
#{i}  {stock['ticker']} — {stock['name']}
  Final Score:     {stock['final_score']}/100 (base: {stock['composite']}, boost: +{stock['geo_boost']}){geo_note}
  Signal:          {stock['signal']}
  Price:           {stock['price']} {stock['currency']}
  Market Cap:      {stock['market_cap']}
  Sector:          {stock['sector']}
  P/E Ratio:       {stock['pe_ratio']}
  Dividend:        {stock['dividend']}
  52-Week Range:   {stock['week_52_low']} → {stock['week_52_high']}
  RSI:             {stock['rsi']} — {stock['rsi_signal']}
  MACD:            {stock['macd_signal']}
  Moving Avgs:     {stock['ma_signal']}
  Analyst View:    {stock['analyst']} (target: {stock['target']})
  Key reasons:
    {chr(10).join('    • ' + r for r in stock['reasons'][:3])}
""")

    return "\n".join(lines)


def is_insight_query(question: str) -> bool:
    """
    Detect if the user is asking for a market scan/insight
    rather than a single stock analysis.
    """
    question_lower = question.lower()
    insight_keywords = [
        "top stocks", "best stocks", "top shares", "best shares",
        "which stocks", "which shares", "what stocks", "what shares",
        "recommend stocks", "recommend shares",
        "geopolitical", "given the situation", "given the current",
        "market opportunity", "opportunities",
        "screener", "screen stocks", "scan the market",
        "potential to increase", "potential to rise",
        "worth looking at", "should i look at",
        "based on the news", "based on current events",
        "macro", "market outlook", "sector outlook",
        "what sectors", "which sectors",
        "top 5", "top 3", "top 10",
        "best performing", "outperform",
    ]
    return any(kw in question_lower for kw in insight_keywords)