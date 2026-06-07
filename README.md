# 📈 Finance Research Assistant

A fully local, AI-powered financial research tool that combines live market data, technical analysis, public sentiment, geopolitical intelligence, and a stock screener — all running on your own machine with no data sent to external AI providers.

---

## What It Does

Ask questions in plain English and receive structured, data-backed research reports:

- **Single stock analysis** — fundamentals, technical indicators, sentiment, analyst view, composite score
- **Market insights** — scan 100+ stocks based on live geopolitical news and surface the highest-scoring opportunities
- **Watchlist with alerts** — track stocks and get notified when prices cross your thresholds
- **Live price charts** — candlestick, SMA overlays, RSI with overbought/oversold zones
- **Public sentiment** — StockTwits bull/bear ratio, CNN Fear & Greed Index, Google Trends, Polymarket prediction markets

Everything runs locally. Your questions, the AI model, and the analysis never leave your machine.

---

## How It Works

```
User asks a question
        ↓
Query router detects intent
   ↙               ↘
Single stock      Market insight
pipeline          pipeline
   ↓                   ↓
Live data          Geopolitical news
Technicals         Theme extraction
Sentiment          Sector scoring
Composite          Stock screener
score              Top N results
   ↓                   ↓
LLM synthesis (llama3.1 via Ollama)
             ↓
   Structured research report
             ↓
      Streamlit chat UI
```

---

## Features

### Stock Research
- Live price, market cap, P/E, EPS, 52-week range, dividend, revenue, profit margin, debt/equity, ROE
- RSI (14), MACD, SMA20, SMA50, Bollinger Bands, volume trend
- Composite research score (0–100) across valuation, momentum, trend, analyst consensus, income
- Structured report format: always balanced — positives and caution factors equally weighted

### Public Sentiment
- **StockTwits** — bullish/bearish message ratio with VADER NLP scoring
- **CNN Fear & Greed Index** — market-wide mood (0=Extreme Fear, 100=Extreme Greed)
- **Google Trends** — retail search interest as attention proxy
- **Polymarket** — crowd prediction markets where available
- Composite sentiment score (0–100) weighted across all sources

### Market Intelligence (Insight Mode)
- Scrapes live RSS feeds from Reuters, BBC, AP
- Extracts active geopolitical themes (conflict, sanctions, oil, rates, trade war, AI...)
- Maps themes to relevant sectors and scores sector relevance
- Screens 100+ stocks across those sectors
- Applies geopolitical boost to composite scores
- Returns top 5 stocks with full reasoning

### Watchlist
- Track any stock with optional price alerts (above/below thresholds)
- Alerts shown in sidebar on every session load
- Persistent JSON storage — survives restarts

### Knowledge Base (RAG)
- Indexed financial documentation: Investopedia terms, trading concepts, technical analysis, financial statements, UK-specific content (ISA, FTSE, FCA)
- Answers concept questions from indexed documentation with source citations
- Add your own PDFs to `data/raw/` to extend the knowledge base

---

## Prerequisites

| Requirement | Minimum | Recommended |
|---|---|---|
| Python | 3.10+ | 3.11 |
| RAM | 16 GB | 32 GB |
| Disk space | 15 GB free | 20 GB free |
| GPU | Not required | 8 GB VRAM |
| OS | macOS / Linux / Windows | macOS / Linux |

> Without a GPU, responses take 15–30 seconds. With a GPU, 1–3 seconds.

---

## Installation

### Step 1: Install Ollama

**macOS:** Download from https://ollama.com/download/mac

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:** Download from https://ollama.com/download/windows

Verify:
```bash
ollama --version
```

---

### Step 2: Pull the Required Models

```bash
# LLM (~4.7 GB)
ollama pull llama3.1

# Embedding model (~274 MB)
ollama pull nomic-embed-text
```

---

### Step 3: Clone the Repository

```bash
git clone https://github.com/yourusername/finance-research-tool.git
cd finance-research-tool
```

---

### Step 4: Create a Virtual Environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

---

### Step 5: Fix SSL Certificates (macOS only)

```bash
open /Applications/Python\ 3.11/Install\ Certificates.command
```

---

### Step 6: Install Dependencies

```bash
pip install -r requirements.txt
python -c "import nltk; nltk.download('vader_lexicon')"
```

---

### Step 7: Configure Environment

Create a `.env` file in the project root:

```bash
# .env
# No credentials required for the core tool.
# All data sources (StockTwits, Fear & Greed, Google Trends, Polymarket) work without API keys.
```

> `.env` is already in `.gitignore` — never commit it.

---

### Step 8: Run Document Ingestion

This indexes financial documentation into the local vector database. Run once, or again whenever you add new PDFs.

```bash
cd src
python ingest.py
```

Expected output:
```
=====================================================
  FINANCE QA — DOCUMENT INGESTION
=====================================================

📥 Loading 55 URLs...
  → https://www.investopedia.com/terms/p/price-earningsratio.asp
     ✓ 12,847 chars loaded
  ...

✂️  Chunking 55 documents...
   ✓ 4,231 chunks created

🔢 Embedding into ChromaDB...
   ✓ Saved to ./data/db

✅ Ingestion complete!
```

> Takes approximately 10–20 minutes depending on your connection.

---

### Step 9: Launch the App

```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501**

> Make sure the Ollama menu bar app is running before launching.

---

## Project Structure

```
finance-research-tool/
├── src/
│   ├── config.py          # Models, paths, URLs, settings
│   ├── ingest.py          # Document ingestion pipeline
│   ├── live_data.py       # yfinance data + technicals + scoring
│   ├── sentiment.py       # StockTwits, Fear & Greed, Trends, Polymarket
│   ├── geopolitical.py    # RSS news scraping, theme extraction, sector mapping
│   ├── screener.py        # Stock screener + insight query detection
│   ├── watchlist.py       # Watchlist persistence and alert checking
│   ├── qa.py              # RAG pipeline, LLM prompts, query routing
│   └── app.py             # Streamlit chat UI
├── data/
│   ├── raw/               # Drop your own PDFs here for ingestion
│   ├── db/                # ChromaDB vector store (auto-generated)
│   └── watchlist.json     # Watchlist storage (auto-generated)
├── .env                   # Environment variables (never commit)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Usage

### Single Stock Analysis

```
Analyse Apple for me
What is NVIDIA's current position?
Is HSBC overbought or oversold?
Compare Tesla and Ford fundamentals
What do analysts think about Microsoft?
What is Lloyds Bank current price?
```

### Market Intelligence (Insight Mode)

Triggered automatically when your question implies a market scan:

```
What 5 stocks have the best potential given the geopolitical situation?
Top sectors based on current global events
Which stocks benefit from current tensions?
Best opportunities in the current macro environment
Screen the market for me
What shares should I research given today's news?
```

### Concept Questions

```
What is a P/E ratio and how do I use it?
Explain the difference between EMA and SMA
What is dollar cost averaging?
What is a stop-loss order?
Explain the Fear and Greed Index
What does RSI tell me?
```

### Watchlist

Use the sidebar to add any stock with optional price alerts:
- Enter a ticker (e.g. `AAPL`, `LLOY.L`)
- Set optional alert below / above thresholds
- Alerts appear in the sidebar on every session load

---

## Configuration

All settings live in `src/config.py`:

```python
OLLAMA_MODEL    = "llama3.1"          # or "mistral", "llama3.1:70b"
EMBEDDING_MODEL = "nomic-embed-text"  # or "mxbai-embed-large"
CHUNK_SIZE      = 512
CHUNK_OVERLAP   = 64
TOP_K_RESULTS   = 5
```

### Adding More Knowledge Base URLs

Open `src/config.py` and add URLs to `FINANCE_URLS`. Then rebuild:

```bash
rm -rf data/db/
python ingest.py
```

### Adding Internal Documents

Drop PDFs into `data/raw/` then rebuild:

```bash
cp your-document.pdf data/raw/
rm -rf data/db/
python ingest.py
```

### Adding More Stocks to the Screener

Open `src/geopolitical.py` and add tickers to the relevant sector in `SECTOR_STOCKS`:

```python
SECTOR_STOCKS = {
    "Defense": [
        "LMT", "RTX", "NOC",
        "YOUR_TICKER_HERE",  # add here
    ],
}
```

### Adding UK / LSE Stocks

Use the `.L` suffix for London Stock Exchange tickers and add to `COMPANY_NAME_MAP` in `live_data.py`:

```python
COMPANY_NAME_MAP = {
    "admiral":   "ADM.L",
    "prudential":"PRU.L",
}
```

---

## Data Sources

| Source | What It Provides | API Key Required | Notes |
|---|---|---|---|
| yfinance | Price, fundamentals, analyst data, news | No | Unofficial Yahoo Finance API |
| StockTwits | Bull/bear sentiment ratio | No | Basic access, no auth |
| CNN Fear & Greed | Market-wide mood index (0–100) | No | Public data endpoint |
| Google Trends | Retail search interest | No | Via pytrends |
| Polymarket | Prediction market probabilities | No | Public Gamma API |
| Reuters RSS | Financial and world news | No | Public RSS feed |
| BBC RSS | World and business news | No | Public RSS feed |
| AP RSS | Top news headlines | No | Public RSS feed |
| Investopedia | Financial concepts | No | Scraped for knowledge base |

---

## Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| LLM | Llama 3.1 8B via Ollama | Answer generation |
| Embeddings | nomic-embed-text via Ollama | Document vectorisation |
| Vector store | ChromaDB (local) | Knowledge base storage |
| RAG framework | LangChain | Retrieval and chain orchestration |
| UI | Streamlit | Chat interface |
| Market data | yfinance | Live prices and fundamentals |
| NLP | NLTK VADER | Sentiment scoring |
| Charts | Plotly | Price, RSI, gauge, bar charts |
| News | feedparser | RSS feed ingestion |

---

## Shortcuts

Add to `~/.zshrc`:

```bash
alias financeingest="cd ~/Desktop/finance-research-tool && source venv/bin/activate && rm -rf data/db/ && cd src && python ingest.py"
alias financestart="cd ~/Desktop/finance-research-tool && source venv/bin/activate && cd src && streamlit run app.py"
```

Reload:
```bash
source ~/.zshrc
```

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `ollama: command not found` | Ollama not in PATH | Restart terminal after install |
| `ConnectionError: Failed to connect to Ollama` | Ollama not running | Open Ollama.app from Applications |
| `ModuleNotFoundError` | Package missing | `pip install -r requirements.txt` |
| SSL error during pip install | macOS cert issue | Run `Install Certificates.command` |
| Slow responses | CPU only, no GPU | Normal — or switch to `mistral` |
| ChromaDB error | Stale vector store | `rm -rf data/db/` then reingest |
| URL fails during ingestion | Site blocks scrapers | Download page as PDF → `data/raw/` |
| Ticker not detected | Not in name map | Add to `COMPANY_NAME_MAP` in `live_data.py` |
| No data for ticker | Wrong ticker format | Add `.L` suffix for LSE (e.g. `LLOY.L`) |
| Google Trends unavailable | Rate limited | Reduce frequency or disable sentiment toggle |

---

## Security

| Component | Data stays local? | Notes |
|---|---|---|
| Ollama + Llama 3.1 | ✅ Yes | Fully local — no telemetry |
| ChromaDB | ✅ Yes | Files on local disk only |
| LangChain | ✅ Yes | Python library, not a cloud service |
| Streamlit | ✅ Yes | Local web server |
| yfinance | 🟡 Ticker sent | Ticker symbol only — no personal data |
| StockTwits | 🟡 Ticker sent | Ticker symbol only — no personal data |
| CNN Fear & Greed | 🟡 HTTP request | Anonymous — no personal data |
| Google Trends | 🟡 Keyword sent | Anonymous — no personal data |
| Polymarket | 🟡 Search term | Anonymous — no personal data |
| RSS feeds | 🟡 HTTP request | Standard anonymous web request |

The only data leaving your machine are ticker symbols and keywords sent to public financial APIs — identical to typing a ticker into Google Finance.

---

## Legal Disclaimer

> This tool is for **research and educational purposes only**. Nothing it produces constitutes financial advice, a personal recommendation, or a solicitation to buy or sell any security.
>
> The tool is not authorised by the Financial Conduct Authority (FCA). Its output must not be relied upon as the basis for any investment decision.
>
> Past performance does not guarantee future results. Markets can move against any position. Always consult a qualified, FCA-authorised financial adviser before making any investment decision.

---

## Roadmap

| Phase | Enhancement |
|---|---|
| Now | Add more stocks to `SECTOR_STOCKS` and `COMPANY_NAME_MAP` |
| Month 1 | Upgrade embeddings to `mxbai-embed-large` |
| Month 1 | Hybrid search (semantic + BM25 keyword) |
| Month 2 | Conversation memory for follow-up questions |
| Month 2 | Feedback logging per answer |
| Month 3 | Sentiment history tracking week-over-week |
| Month 3 | Docker deployment for internal team access |
| 6 months | Fine-tune model on team feedback data |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-improvement`
3. Commit: `git commit -m "add: your improvement"`
4. Push: `git push origin feature/your-improvement`
5. Open a Pull Request

---

## Licence

MIT Licence — free to use, modify, and distribute for internal and personal use.

The LLM model (Llama 3.1) is subject to Meta's Community Licence — free for organisations with under 700 million monthly active users.

---

*Built as an internal financial research tool. Not affiliated with any financial institution or data provider.*