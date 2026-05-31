# src/app.py

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import pandas as pd
from qa import load_qa_chain, ask
from watchlist import (
    load_watchlist,
    add_to_watchlist,
    remove_from_watchlist,
    check_alerts,
    get_watchlist_snapshot,
)

# ── PAGE CONFIG ─────────────────────────────────────────────
st.set_page_config(
    page_title="Finance Research Assistant",
    page_icon="📈",
    layout="wide",
)

# ── LOAD CHAIN ──────────────────────────────────────────────
@st.cache_resource
def get_chain():
    with st.spinner("Loading models and knowledge base..."):
        return load_qa_chain()

retriever_llm = get_chain()


# ── CHART HELPERS ────────────────────────────────────────────

def render_candlestick_chart(ticker: str):
    """Render a 6-month candlestick chart with SMA overlays."""
    try:
        hist = yf.Ticker(ticker).history(period="6mo")
        if hist.empty:
            st.caption("Chart data unavailable.")
            return

        close  = hist["Close"]
        sma_20 = close.rolling(20).mean()
        sma_50 = close.rolling(50).mean()

        fig = go.Figure()

        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist["Open"],
            high=hist["High"],
            low=hist["Low"],
            close=hist["Close"],
            name=ticker,
            increasing_line_color="#02C39A",
            decreasing_line_color="#EF4444",
        ))

        fig.add_trace(go.Scatter(
            x=hist.index, y=sma_20,
            mode="lines", name="SMA 20",
            line=dict(color="#F59E0B", width=1.5, dash="dot"),
        ))

        fig.add_trace(go.Scatter(
            x=hist.index, y=sma_50,
            mode="lines", name="SMA 50",
            line=dict(color="#818CF8", width=1.5, dash="dash"),
        ))

        fig.update_layout(
            title=f"{ticker} — 6 Month Price Chart",
            xaxis_title="Date",
            yaxis_title="Price",
            height=380,
            xaxis_rangeslider_visible=False,
            template="plotly_dark",
            legend=dict(orientation="h", yanchor="bottom", y=1.0),
            margin=dict(l=40, r=20, t=60, b=40),
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.caption(f"Chart unavailable: {e}")


def render_rsi_chart(ticker: str):
    """Render RSI chart with overbought/oversold zones."""
    try:
        hist  = yf.Ticker(ticker).history(period="6mo")
        close = hist["Close"]

        delta = close.diff()
        gain  = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss  = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
        rs    = gain / loss
        rsi   = 100 - (100 / (1 + rs))

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=hist.index, y=rsi,
            mode="lines", name="RSI (14)",
            line=dict(color="#02C39A", width=2),
        ))

        # Overbought / oversold zones
        fig.add_hline(y=70, line_dash="dash",
                      line_color="#EF4444", annotation_text="Overbought (70)")
        fig.add_hline(y=30, line_dash="dash",
                      line_color="#22C55E", annotation_text="Oversold (30)")
        fig.add_hline(y=50, line_dash="dot",
                      line_color="#94A3B8", annotation_text="Midline")

        fig.update_layout(
            title=f"{ticker} — RSI (14)",
            yaxis=dict(range=[0, 100]),
            height=220,
            template="plotly_dark",
            margin=dict(l=40, r=20, t=50, b=30),
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.caption(f"RSI chart unavailable: {e}")


def render_score_gauge(score: float, label: str):
    """Render a gauge chart for the composite score."""
    color = (
        "#22C55E" if score >= 70 else
        "#F59E0B" if score >= 50 else
        "#EF4444"
    )

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": label, "font": {"size": 14}},
        gauge={
            "axis":  {"range": [0, 100]},
            "bar":   {"color": color},
            "steps": [
                {"range": [0,  40],  "color": "#1E293B"},
                {"range": [40, 60],  "color": "#1E3A5F"},
                {"range": [60, 100], "color": "#164E3B"},
            ],
            "threshold": {
                "line":  {"color": "white", "width": 2},
                "thickness": 0.75,
                "value": score,
            },
        },
        number={"suffix": "/100", "font": {"size": 28}},
    ))

    fig.update_layout(
        height=220,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=40, b=20),
    )

    st.plotly_chart(fig, use_container_width=True)


# ── SIDEBAR ─────────────────────────────────────────────────
with st.sidebar:
    st.title("📈 Finance Research")
    st.caption("Llama 3.1 + yfinance — fully local")

    st.divider()

    # Disclaimer
    st.markdown("### ⚠️ Disclaimer")
    st.warning(
        "**Research tool only.** Nothing here is financial advice. "
        "Consult an FCA-authorised advisor before investing."
    )

    st.divider()

    # Watchlist management
    st.markdown("### 👀 Watchlist")

    # Check alerts
    alerts = check_alerts()
    if alerts:
        st.markdown("**🔔 Active Alerts**")
        for alert in alerts:
            if alert["type"] == "above":
                st.success(alert["message"])
            else:
                st.error(alert["message"])

    # Watchlist table
    wl_data = get_watchlist_snapshot()
    if wl_data:
        for row in wl_data:
            col1, col2 = st.columns([3, 1])
            col1.markdown(
                f"**{row['ticker']}** — {row['price']} {row['currency']}"
                f"\n\n*{row['recommendation']}*"
            )
            if col2.button("🗑️", key=f"rm_{row['ticker']}"):
                remove_from_watchlist(row["ticker"])
                st.rerun()
    else:
        st.caption("No stocks in watchlist yet.")

    # Add to watchlist
    with st.expander("➕ Add to Watchlist"):
        new_ticker = st.text_input("Ticker (e.g. AAPL, LLOY.L)")
        col1, col2 = st.columns(2)
        alert_below = col1.number_input("Alert below", value=0.0, min_value=0.0)
        alert_above = col2.number_input("Alert above", value=0.0, min_value=0.0)
        if st.button("Add", use_container_width=True) and new_ticker:
            msg = add_to_watchlist(
                new_ticker.strip().upper(),
                float(alert_below) if alert_below > 0 else None,
                float(alert_above) if alert_above > 0 else None,
            )
            st.success(msg)
            st.rerun()

    st.divider()

    # Example questions
    st.markdown("### 💡 Try These")
    examples = [
        "What is Apple's current P/E ratio?",
        "Analyse NVIDIA for me",
        "Compare Tesla and Ford",
        "What is Lloyds Bank current price?",
        "Explain what RSI means",
        "What is dollar cost averaging?",
        "What do analysts think about Microsoft?",
        "Is HSBC overbought or oversold?",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True, key=f"ex_{ex}"):
            st.session_state.pending_question = ex


# ── MAIN AREA ────────────────────────────────────────────────
st.title("📈 Finance Research Assistant")
st.caption(
    "Ask questions about stocks, markets, ratios, and strategies. "
    "Live data fetched from Yahoo Finance per query."
)
st.info(
    "🔒 Fully local — your questions never leave your machine. "
    "Live prices fetched from public Yahoo Finance API.",
    icon="🔒",
)

# ── SESSION STATE ────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# ── RENDER HISTORY ───────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Show charts for historical ticker messages
        if msg.get("tickers"):
            st.caption(f"📊 Data fetched for: {', '.join(msg['tickers'])}")
            for ticker in msg["tickers"]:
                with st.expander(f"📉 Charts — {ticker}"):
                    render_candlestick_chart(ticker)
                    render_rsi_chart(ticker)

        if msg.get("sources"):
            with st.expander("📚 Knowledge Base Sources"):
                for src in msg["sources"]:
                    st.markdown(f"- {src}")

        if (msg.get("live_data") and
                msg["live_data"] != "No specific stock ticker detected in this question."):
            with st.expander("📡 Raw Market Data"):
                st.code(msg["live_data"])

# ── HANDLE SIDEBAR BUTTONS ───────────────────────────────────
pending = st.session_state.pop("pending_question", None)

# ── CHAT INPUT ───────────────────────────────────────────────
question = (
    st.chat_input("e.g. Analyse Apple for me, or what is a P/E ratio?")
    or pending
)

if question:
    # User message
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Assistant response
    with st.chat_message("assistant"):
        with st.spinner("Fetching live data, calculating signals, generating research..."):
            result = ask(retriever_llm, question)

        st.markdown(result["answer"])

        # Charts if tickers detected
        if result.get("tickers"):
            st.caption(f"📊 Live data fetched for: {', '.join(result['tickers'])}")
            for ticker in result["tickers"]:
                with st.expander(f"📉 Charts — {ticker}"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        render_candlestick_chart(ticker)
                    with col2:
                        # Extract composite score from live_data if available
                        import re
                        score_match = re.search(
                            r"Composite Research Score: (\d+\.?\d*)/100",
                            result.get("live_data", "")
                        )
                        if score_match:
                            render_score_gauge(
                                float(score_match.group(1)),
                                f"{ticker} Research Score"
                            )
                    render_rsi_chart(ticker)

        # Sources
        if result.get("sources"):
            with st.expander("📚 Knowledge Base Sources"):
                for src in result["sources"]:
                    st.markdown(f"- {src}")

        # Raw data
        if (result.get("live_data") and
                result["live_data"] != "No specific stock ticker detected in this question."):
            with st.expander("📡 Raw Market Data"):
                st.code(result["live_data"])

    # Save to history
    st.session_state.messages.append({
        "role":      "assistant",
        "content":   result["answer"],
        "sources":   result.get("sources", []),
        "tickers":   result.get("tickers", []),
        "live_data": result.get("live_data", ""),
    })