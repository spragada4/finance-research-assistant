# src/app.py

import re
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import yfinance as yf
from qa import load_qa_chain, ask
from watchlist import (
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

# ── LOAD QA CHAIN ────────────────────────────────────────────
@st.cache_resource
def get_chain():
    with st.spinner("Loading models and knowledge base..."):
        return load_qa_chain()

retriever_llm = get_chain()


# ── CHART FUNCTIONS ──────────────────────────────────────────

def render_candlestick(ticker: str):
    try:
        hist  = yf.Ticker(ticker).history(period="6mo")
        if hist.empty:
            st.caption("Chart unavailable.")
            return
        close  = hist["Close"]
        sma_20 = close.rolling(20).mean()
        sma_50 = close.rolling(50).mean()

        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist["Open"], high=hist["High"],
            low=hist["Low"],   close=hist["Close"],
            name=ticker,
            increasing_line_color="#02C39A",
            decreasing_line_color="#EF4444",
        ))
        fig.add_trace(go.Scatter(
            x=hist.index, y=sma_20, mode="lines", name="SMA 20",
            line=dict(color="#F59E0B", width=1.5, dash="dot"),
        ))
        fig.add_trace(go.Scatter(
            x=hist.index, y=sma_50, mode="lines", name="SMA 50",
            line=dict(color="#818CF8", width=1.5, dash="dash"),
        ))
        fig.update_layout(
            title=f"{ticker} — 6 Month Price",
            height=360,
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            legend=dict(orientation="h", yanchor="bottom", y=1.0),
            margin=dict(l=40, r=20, t=60, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.caption(f"Chart unavailable: {e}")


def render_rsi(ticker: str):
    try:
        hist  = yf.Ticker(ticker).history(period="6mo")
        close = hist["Close"]
        delta = close.diff()
        gain  = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss  = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
        rsi   = 100 - (100 / (1 + gain / loss))

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist.index, y=rsi, mode="lines",
            name="RSI", line=dict(color="#02C39A", width=2),
        ))
        fig.add_hline(y=70, line_dash="dash", line_color="#EF4444",
                      annotation_text="Overbought (70)")
        fig.add_hline(y=30, line_dash="dash", line_color="#22C55E",
                      annotation_text="Oversold (30)")
        fig.add_hline(y=50, line_dash="dot",  line_color="#94A3B8")
        fig.update_layout(
            title=f"{ticker} — RSI (14)",
            yaxis=dict(range=[0, 100]),
            height=220,
            template="plotly_dark",
            margin=dict(l=40, r=20, t=50, b=30),
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.caption(f"RSI unavailable: {e}")


def render_gauge(score: float, title: str):
    color = (
        "#22C55E" if score >= 65 else
        "#84CC16" if score >= 55 else
        "#F59E0B" if score >= 45 else
        "#F97316" if score >= 35 else
        "#EF4444"
    )
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": title, "font": {"size": 13}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar":  {"color": color},
            "steps": [
                {"range": [0,  30],  "color": "#450a0a"},
                {"range": [30, 45],  "color": "#431407"},
                {"range": [45, 55],  "color": "#1c1917"},
                {"range": [55, 70],  "color": "#052e16"},
                {"range": [70, 100], "color": "#064e3b"},
            ],
        },
        number={"suffix": "/100", "font": {"size": 24}},
    ))
    fig.update_layout(
        height=200,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=40, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_bull_bear_bar(bullish_pct: float, bearish_pct: float, ticker: str):
    neutral_pct = max(0.0, 100.0 - bullish_pct - bearish_pct)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Bullish", y=["StockTwits"], x=[bullish_pct],
        orientation="h", marker_color="#22C55E",
        text=[f"{bullish_pct}%"], textposition="inside",
    ))
    fig.add_trace(go.Bar(
        name="Neutral", y=["StockTwits"], x=[neutral_pct],
        orientation="h", marker_color="#64748B",
        text=[f"{neutral_pct:.0f}%"], textposition="inside",
    ))
    fig.add_trace(go.Bar(
        name="Bearish", y=["StockTwits"], x=[bearish_pct],
        orientation="h", marker_color="#EF4444",
        text=[f"{bearish_pct}%"], textposition="inside",
    ))
    fig.update_layout(
        barmode="stack",
        title=f"{ticker} — StockTwits Bull/Bear Ratio",
        height=150,
        template="plotly_dark",
        showlegend=True,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(range=[0, 100]),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_sentiment_section(sentiment_data: dict, ticker: str):
    if not sentiment_data or ticker not in sentiment_data:
        st.caption("Sentiment data not available for this query.")
        return

    sent   = sentiment_data[ticker]
    comp   = sent.get("composite", {})
    st_d   = sent.get("stocktwits", {})
    fg     = sent.get("fear_greed", {})
    trends = sent.get("trends", {})
    poly   = sent.get("polymarket", {})

    st.markdown(f"#### 🧠 Public Sentiment — {ticker}")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_gauge(comp.get("composite", 50), "Overall Sentiment")
    with c2:
        render_gauge(comp.get("breakdown", {}).get("stocktwits", 50), "StockTwits (40%)")
    with c3:
        render_gauge(comp.get("breakdown", {}).get("fear_greed", 50), "Fear & Greed (35%)")
    with c4:
        render_gauge(comp.get("breakdown", {}).get("trends", 50), "Google Trends (25%)")

    st.markdown(
        f"**Overall Signal:** {comp.get('label', 'N/A')}  "
        f"— Score: **{comp.get('composite', 'N/A')}/100**"
    )
    st.caption(
        "⚠️ High bullish sentiment can signal a crowded trade. "
        "Always use alongside fundamentals and technicals."
    )
    st.divider()

    st.markdown("**📊 StockTwits**")
    if st_d.get("available") and st_d.get("bullish_pct") is not None:
        render_bull_bear_bar(st_d["bullish_pct"], st_d["bearish_pct"], ticker)
        c1, c2, c3 = st.columns(3)
        c1.metric("Bullish",  f"{st_d['bullish_pct']}%")
        c2.metric("Bearish",  f"{st_d['bearish_pct']}%")
        c3.metric("Messages", st_d["total_msgs"])
        st.caption(f"Signal: **{st_d['signal']}**")
    else:
        st.caption(f"StockTwits: {st_d.get('note', 'Unavailable')}")

    st.divider()
    st.markdown("**😨 Fear & Greed Index**")
    if fg.get("available"):
        c1, c2, c3 = st.columns(3)
        c1.metric("Score", f"{fg['score']}/100")
        c2.metric("Label", fg["label"])
        c3.metric("vs Last Week", f"{fg['prev_week']}")
        st.info(fg.get("context", ""))

    st.divider()
    st.markdown("**🔍 Google Trends**")
    if trends.get("available"):
        c1, c2, c3 = st.columns(3)
        c1.metric("Current Interest", f"{trends['current']}/100")
        c2.metric("4-Week Avg", f"{trends['avg_4w']}")
        c3.metric("12-Week Avg", f"{trends['avg_12w']}")
        st.caption(trends["trend"])

    st.divider()
    st.markdown("**🎯 Polymarket Prediction Markets**")
    if poly.get("found") and poly.get("markets"):
        for market in poly["markets"][:3]:
            st.markdown(f"**{market['question']}**")
            for outcome, prob in market.get("outcomes", []):
                color = "green" if prob > 60 else "red" if prob < 40 else "orange"
                st.markdown(f"  :{color}[{outcome}: {prob}%]")
            if market.get("url"):
                st.caption(f"[View on Polymarket]({market['url']})")
    else:
        st.caption("No active prediction markets found.")


# ── INSIGHT RENDERING ─────────────────────────────────────────

def render_geo_themes(geo: dict):
    """Render geopolitical themes as a bar chart."""
    themes  = geo.get("themes", {})
    sectors = geo.get("sectors", {})

    if themes:
        st.markdown("**📰 Active Geopolitical Themes**")
        theme_df = pd.DataFrame([
            {"Theme": k, "Mentions": v["mentions"], "Sentiment": v["sentiment_label"]}
            for k, v in list(themes.items())[:8]
        ])
        fig = px.bar(
            theme_df, x="Mentions", y="Theme",
            orientation="h",
            color="Mentions",
            color_continuous_scale="Blues",
            template="plotly_dark",
            height=300,
        )
        fig.update_layout(
            title="News mention volume by theme",
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    if sectors:
        st.markdown("**🏭 Sector Relevance Scores**")
        sector_df = pd.DataFrame([
            {"Sector": k, "Relevance": v}
            for k, v in list(sectors.items())[:8]
        ])
        fig = px.bar(
            sector_df, x="Relevance", y="Sector",
            orientation="h",
            color="Relevance",
            color_continuous_scale="Teal",
            template="plotly_dark",
            height=300,
        )
        fig.update_layout(
            title="Sector relevance (0-100, driven by active themes)",
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False,
            xaxis=dict(range=[0, 100]),
        )
        st.plotly_chart(fig, use_container_width=True)


def render_screener_results(results: list):
    """Render screener results as a comparison table and score chart."""
    if not results:
        st.caption("No screener results to display.")
        return

    st.markdown("**🏆 Top Screened Stocks**")

    # Score comparison chart
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Base Score",
        x=[r["ticker"] for r in results],
        y=[r["composite"] for r in results],
        marker_color="#065A82",
    ))
    fig.add_trace(go.Bar(
        name="Geo Boost",
        x=[r["ticker"] for r in results],
        y=[r["geo_boost"] for r in results],
        marker_color="#02C39A",
    ))
    fig.update_layout(
        barmode="stack",
        title="Composite Score by Stock (base + geopolitical boost)",
        template="plotly_dark",
        height=300,
        margin=dict(l=20, r=20, t=50, b=30),
        yaxis=dict(range=[0, 100]),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Summary table
    table_data = []
    for r in results:
        table_data.append({
            "Rank":       results.index(r) + 1,
            "Ticker":     r["ticker"],
            "Name":       r["name"][:28],
            "Score":      f"{r['final_score']}/100",
            "Price":      f"{r['price']} {r['currency']}",
            "P/E":        r["pe_ratio"],
            "RSI":        r["rsi"],
            "Analyst":    r["analyst"],
            "Sector":     r["sector"],
        })

    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Per-stock charts
    st.markdown("**📊 Individual Stock Charts**")
    cols = st.columns(min(len(results), 3))
    for i, result in enumerate(results[:3]):
        with cols[i]:
            st.caption(f"**{result['ticker']}** — {result['final_score']}/100")
            render_candlestick(result["ticker"])


# ── SIDEBAR ──────────────────────────────────────────────────
with st.sidebar:
    st.title("📈 Finance Research")
    st.caption("Llama 3.1 + yfinance — fully local")
    st.divider()

    st.markdown("### ⚠️ Disclaimer")
    st.warning(
        "**Research tool only.** Nothing here is financial advice. "
        "Always consult an FCA-authorised advisor before investing."
    )
    st.divider()

    st.markdown("### ⚙️ Settings")
    include_sentiment = st.toggle(
        "🧠 Include Sentiment Analysis",
        value=True,
        help="Adds ~10s. Includes StockTwits, Fear & Greed, Google Trends, Polymarket",
    )
    st.divider()

    st.markdown("### 👀 Watchlist")
    alerts = check_alerts()
    if alerts:
        for alert in alerts:
            if alert["type"] == "above":
                st.success(alert["message"])
            else:
                st.error(alert["message"])

    wl_data = get_watchlist_snapshot()
    if wl_data:
        for row in wl_data:
            c1, c2 = st.columns([3, 1])
            c1.markdown(
                f"**{row['ticker']}** — {row['price']} {row['currency']}\n\n"
                f"*{row['recommendation']}*"
            )
            if c2.button("🗑️", key=f"rm_{row['ticker']}"):
                remove_from_watchlist(row["ticker"])
                st.rerun()
    else:
        st.caption("No stocks in watchlist yet.")

    with st.expander("➕ Add to Watchlist"):
        new_ticker  = st.text_input("Ticker (e.g. AAPL, LLOY.L)")
        c1, c2      = st.columns(2)
        alert_below = c1.number_input("Alert below", value=0.0, min_value=0.0)
        alert_above = c2.number_input("Alert above", value=0.0, min_value=0.0)
        if st.button("Add", use_container_width=True) and new_ticker:
            msg = add_to_watchlist(
                new_ticker.strip().upper(),
                float(alert_below) if alert_below > 0 else None,
                float(alert_above) if alert_above > 0 else None,
            )
            st.success(msg)
            st.rerun()

    st.divider()
    st.markdown("### 💡 Try These")
    examples = [
        # Insight queries
        "What 5 stocks have the best potential given geopolitics?",
        "Top sectors based on current global situation",
        "Which stocks benefit from current tensions?",
        "Best opportunities given the macro environment",
        # Single stock queries
        "Analyse Apple for me",
        "What is NVIDIA's current position?",
        "Is HSBC overbought or oversold?",
        "Compare Tesla and Ford",
        "Explain what RSI means",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True, key=f"ex_{ex}"):
            st.session_state.pending_question = ex


# ── MAIN AREA ─────────────────────────────────────────────────
st.title("📈 Finance Research Assistant")
st.caption(
    "Single stock analysis, or ask for market insights — "
    "live data and geopolitical context fetched per query."
)
st.info(
    "🔒 Fully local — your questions never leave your machine. "
    "Live data fetched from public APIs per query.",
    icon="🔒",
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# ── RENDER HISTORY ─────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg.get("is_insight") and msg.get("geo_context"):
            with st.expander("🌍 Geopolitical Intelligence"):
                tab1, tab2 = st.tabs(["📊 Themes & Sectors", "📰 Headlines"])
                with tab1:
                    render_geo_themes(msg["geo_context"])
                with tab2:
                    for h in msg["geo_context"].get("headlines", [])[:10]:
                        emoji = "🟢" if h["score"] > 0.1 else "🔴" if h["score"] < -0.1 else "⚪"
                        st.markdown(f"{emoji} **{h['source']}** — {h['title']}")

            if msg.get("screener_results"):
                with st.expander("🏆 Screener Results", expanded=True):
                    render_screener_results(msg["screener_results"])

        elif msg.get("tickers"):
            st.caption(f"📊 Data fetched for: {', '.join(msg['tickers'])}")
            for ticker in msg["tickers"]:
                with st.expander(f"📊 Analysis — {ticker}"):
                    tab1, tab2, tab3 = st.tabs(["📈 Price", "🧠 Sentiment", "📡 Raw"])
                    with tab1:
                        render_candlestick(ticker)
                        render_rsi(ticker)
                    with tab2:
                        render_sentiment_section(msg.get("sentiment_data", {}), ticker)
                    with tab3:
                        st.code(msg.get("live_data", ""))

        if msg.get("sources"):
            with st.expander("📚 Sources"):
                for src in msg["sources"]:
                    st.markdown(f"- {src}")

# ── HANDLE SIDEBAR BUTTONS ─────────────────────────────────────
pending = st.session_state.pop("pending_question", None)

# ── CHAT INPUT ──────────────────────────────────────────────────
question = (
    st.chat_input(
        "e.g. 'What 5 stocks suit the current geopolitical situation?' "
        "or 'Analyse Apple for me'"
    )
    or pending
)

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Fetching news, screening stocks, generating report..."):
            result = ask(retriever_llm, question, include_sentiment=include_sentiment)

        st.markdown(result["answer"])

        # Insight result rendering
        if result.get("is_insight"):
            if result.get("geo_context"):
                with st.expander("🌍 Geopolitical Intelligence", expanded=True):
                    tab1, tab2 = st.tabs(["📊 Themes & Sectors", "📰 Headlines"])
                    with tab1:
                        render_geo_themes(result["geo_context"])
                    with tab2:
                        for h in result["geo_context"].get("headlines", [])[:10]:
                            emoji = "🟢" if h["score"] > 0.1 else "🔴" if h["score"] < -0.1 else "⚪"
                            st.markdown(f"{emoji} **{h['source']}** — {h['title']}")

            if result.get("screener_results"):
                with st.expander("🏆 Screener Results", expanded=True):
                    render_screener_results(result["screener_results"])

        # Standard single stock rendering
        elif result.get("tickers"):
            st.caption(f"📊 Data fetched for: {', '.join(result['tickers'])}")
            for ticker in result["tickers"]:
                with st.expander(f"📊 Full Analysis — {ticker}", expanded=True):
                    tab1, tab2, tab3 = st.tabs(["📈 Price", "🧠 Sentiment", "📡 Raw"])
                    with tab1:
                        c1, c2 = st.columns([2, 1])
                        with c1:
                            render_candlestick(ticker)
                        with c2:
                            score_match = re.search(
                                r"Composite Research Score: (\d+\.?\d*)/100",
                                result.get("live_data", "")
                            )
                            if score_match:
                                render_gauge(float(score_match.group(1)), f"{ticker} Score")
                        render_rsi(ticker)
                    with tab2:
                        render_sentiment_section(result.get("sentiment_data", {}), ticker)
                    with tab3:
                        st.code(result.get("live_data", ""))

        if result.get("sources"):
            with st.expander("📚 Sources"):
                for src in result["sources"]:
                    st.markdown(f"- {src}")

    st.session_state.messages.append({
        "role":             "assistant",
        "content":          result["answer"],
        "sources":          result.get("sources", []),
        "tickers":          result.get("tickers", []),
        "live_data":        result.get("live_data", ""),
        "sentiment_data":   result.get("sentiment_data", {}),
        "screener_results": result.get("screener_results", []),
        "geo_context":      result.get("geo_context"),
        "is_insight":       result.get("is_insight", False),
    })