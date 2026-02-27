# Stock-Market-Sentiment-Agentic-Trader
# AI-Driven Stock Market Sentiment & Technical Agentic Trader

## Project Abstract
The objective of this project is to build an automated, intelligent trading agent that bridges the gap between fundamental market sentiment and strict technical execution. By transforming unstructured text data (financial news) into actionable logic, the LLM-powered agent independently assesses market narratives. However, to prevent poor entries, the system routes this sentiment into a Python-based **Technical Decision Engine**. This engine acts as a strict gatekeeper, analyzing market structure, trend direction, and pullbacks to output precise Go/No-Go decisions and draft exact Long/Short limit orders.

## Core Technology Stack
* **Python (Pandas & NumPy):** The core mathematical engine driving the backend logic, calculating market structure, trends, and exact pullback entry zones.
* **BeautifulSoup & Requests:** The data ingestion pipeline to scrape real-time financial headlines and articles.
* **LLM API (Large Language Model):** The "Fundamental Analyst," utilizing NLP to perform entity recognition (identifying specific assets) and contextual sentiment scoring.
* **Streamlit:** A lightweight framework used to build the frontend dashboard, providing a clean user interface to monitor the agent's actions, portfolio health, and the math behind its trade decisions.

## Key Features
* **Automated Data Ingestion:** Continuously scrapes targeted financial news sources without manual intervention.
* **Contextual Sentiment Scoring:** The LLM analyzes the context of news to generate a precise sentiment score (e.g., 85% Bullish, 20% Bearish) and a confidence metric.
* **The Confluence Decision Engine:** The system never enters a trade blindly on news. It cross-references the LLM's sentiment score with live price action to issue a strict Go/No-Go execution command.
* **Directional Alignment (Long/Short):** The algorithm forces alignment between the news and the chart. It only looks for LONG entries if Sentiment is Bullish AND the chart is in a mathematical Uptrend (Higher Highs/Higher Lows). It looks for SHORT entries if Sentiment is Bearish AND the chart is in a Downtrend.
* **Pullback Entry Calculations:** Instead of executing market orders at the top or bottom of a move, the Python engine calculates structural pullbacks (e.g., 50% to 61.8% Fibonacci retracement zones). It drafts precise Limit Orders only when the price "discounts" into these zones.
* **Live Portfolio Dashboard:** A visual UI that tracks the drafted decisions, including the asset, sentiment, trend status, pullback status, and the final exact entry price.



## System Accuracy & Realities
* **Separation of Concerns:** To prevent AI mathematical hallucinations, the system strictly separates duties: The LLM *only* handles language and sentiment, while Python *only* handles the hard math, trend identification, and entry calculation.
* **Market Realities:** The system is probabilistic. While it perfectly calculates pullbacks and accurately gauges sentiment, markets can still behave unpredictably due to sudden macroeconomic shifts. Strict risk management and stop-loss logic are hardcoded to protect against "priced-in" news or failed breakouts.



## Future Scaling Capability (The Ultimate Vision)
This system is built with a modular, decoupled architecture, designed to scale into a comprehensive quantitative trading suite. Future phases will include:
* **Smart Money Concepts (SMC):** Adding deeper technical definitions to identify Fair Value Gaps (FVGs), order blocks, and liquidity sweeps for institutional-grade entries.
* **Live Broker Execution:** Upgrading from a Streamlit mock-dashboard to a live broker API (like Alpaca, Binance, or Interactive Brokers) via TradingView webhooks for real-time paper trading and live capital execution.

---
*Built as a foundational module for an advanced algorithmic trading suite.*
