# src/watchlist.py

import json
import os
from datetime import datetime
from live_data import get_stock_snapshot

WATCHLIST_FILE = "./data/watchlist.json"


def load_watchlist() -> dict:
    """Load watchlist from disk."""
    if not os.path.exists(WATCHLIST_FILE):
        return {}
    try:
        with open(WATCHLIST_FILE) as f:
            return json.load(f)
    except:
        return {}


def save_watchlist(watchlist: dict):
    """Save watchlist to disk."""
    os.makedirs("./data", exist_ok=True)
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(watchlist, f, indent=2)


def add_to_watchlist(
    ticker: str,
    alert_below: float = None,
    alert_above: float = None,
) -> str:
    """Add a ticker to the watchlist with optional price alerts."""
    wl = load_watchlist()
    wl[ticker.upper()] = {
        "alert_below": alert_below,
        "alert_above": alert_above,
        "added":       str(datetime.today().date()),
    }
    save_watchlist(wl)
    return f"✅ {ticker.upper()} added to watchlist."


def remove_from_watchlist(ticker: str) -> str:
    """Remove a ticker from the watchlist."""
    wl = load_watchlist()
    if ticker.upper() in wl:
        del wl[ticker.upper()]
        save_watchlist(wl)
        return f"🗑️ {ticker.upper()} removed."
    return f"{ticker.upper()} not found in watchlist."


def check_alerts() -> list:
    """
    Check all watchlist tickers against their alert thresholds.
    Returns list of triggered alert messages.
    """
    wl     = load_watchlist()
    alerts = []

    for ticker, config in wl.items():
        snap  = get_stock_snapshot(ticker)
        price = snap.get("price")

        if not isinstance(price, (int, float)):
            continue

        if config.get("alert_below") and price < config["alert_below"]:
            alerts.append({
                "type":    "below",
                "ticker":  ticker,
                "message": f"🔴 {ticker} dropped below {config['alert_below']} — now at {price}",
                "price":   price,
            })

        if config.get("alert_above") and price > config["alert_above"]:
            alerts.append({
                "type":    "above",
                "ticker":  ticker,
                "message": f"🟢 {ticker} rose above {config['alert_above']} — now at {price}",
                "price":   price,
            })

    return alerts


def get_watchlist_snapshot() -> list:
    """
    Return current price and status for all watchlist tickers.
    Used to render the watchlist table in the UI.
    """
    wl   = load_watchlist()
    rows = []

    for ticker, config in wl.items():
        snap = get_stock_snapshot(ticker)
        rows.append({
            "ticker":       ticker,
            "name":         snap.get("name", ticker),
            "price":        snap.get("price", "N/A"),
            "currency":     snap.get("currency", ""),
            "alert_below":  config.get("alert_below"),
            "alert_above":  config.get("alert_above"),
            "added":        config.get("added", ""),
            "recommendation": snap.get("recommendation", "N/A"),
        })

    return rows