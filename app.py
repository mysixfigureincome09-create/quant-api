from flask import Flask, jsonify
from flask_cors import CORS
import requests
import pandas as pd
import numpy as np
import os
from datetime import datetime

# =====================================================
# APP SETUP
# =====================================================
app = Flask(__name__)
CORS(app)

# =====================================================
# API CONFIG
# =====================================================
ALPHA_API_KEY = "JXJUT1ZYW2ES67X1"
BASE_URL = "https://www.alphavantage.co/query"

# =====================================================
# STOCK UNIVERSE
# =====================================================
WATCHLIST = [
    "AAPL",
    "MSFT",
    "NVDA",
    "META",
    "GOOGL",
    "AMZN",
    "AMD",
    "TSLA",
    "JPM",
    "XOM",
    "LLY",
    "AVGO"
]

# =====================================================
# HOME
# =====================================================
@app.route("/")
def home():
    return jsonify({
        "message": "Quant AI API Live",
        "status": "running"
    })

# =====================================================
# DASHBOARD
# =====================================================
@app.route("/dashboard")
def dashboard():

    html = """
    <html>

    <head>
        <title>Quant AI Dashboard</title>

        <style>

            body {
                background-color: #0f1117;
                color: white;
                font-family: Arial;
                padding: 30px;
            }

            .card {
                background: #1c1f26;
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 20px;
            }

            h1 {
                color: #00ff99;
            }

            h2 {
                color: #00ffaa;
            }

            a {
                color: #00ff99;
                text-decoration: none;
                font-size: 18px;
            }

            li {
                margin-bottom: 10px;
            }

        </style>

    </head>

    <body>

        <h1>Quant AI Dashboard</h1>

        <div class="card">
            <h2>System</h2>
            <p>Portfolio Intelligence Engine Online</p>
        </div>

        <div class="card">
            <h2>Endpoints</h2>

            <ul>

                <li><a href="/top_picks">AI Top Picks</a></li>

                <li><a href="/portfolio/swing">Swing Portfolio</a></li>

                <li><a href="/portfolio/quarterly">Quarterly Portfolio</a></li>

                <li><a href="/portfolio/yearly">Yearly Portfolio</a></li>

                <li><a href="/market_sentiment">Market Sentiment</a></li>

            </ul>

        </div>

    </body>

    </html>
    """

    return html

# =====================================================
# GET GLOBAL QUOTE
# =====================================================
def get_quote(symbol):

    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": ALPHA_API_KEY
    }

    try:

        response = requests.get(BASE_URL, params=params)
        data = response.json()

        if "Global Quote" not in data:
            return None

        quote = data["Global Quote"]

        return {
            "symbol": symbol,
            "price": float(quote["05. price"]),
            "change_percent": float(
                quote["10. change percent"].replace("%", "")
            )
        }

    except:
        return None

# =====================================================
# GET DAILY DATA
# =====================================================
def get_daily_data(symbol):

    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": ALPHA_API_KEY
    }

    try:

        response = requests.get(BASE_URL, params=params)
        data = response.json()

        if "Time Series (Daily)" not in data:
            return None

        ts = data["Time Series (Daily)"]

        df = pd.DataFrame.from_dict(ts, orient="index")

        df = df.astype(float)

        df = df.sort_index()

        return df

    except:
        return None

# =====================================================
# MARKET SENTIMENT ENGINE
# =====================================================
@app.route("/market_sentiment")
def market_sentiment():

    # basic mock sentiment model
    # phase 2 can connect real news APIs

    sentiment = {
        "market_regime": "risk_on",
        "geopolitical_risk": "moderate",
        "fed_policy": "neutral",
        "ai_sector_strength": "strong",
        "generated_at": str(datetime.utcnow())
    }

    return jsonify(sentiment)

# =====================================================
# STOCK SCORING MODEL
# =====================================================
def score_stock(symbol):

    quote = get_quote(symbol)

    df = get_daily_data(symbol)

    if quote is None or df is None:
        return None

    try:

        latest_price = df["4. close"].iloc[-1]

        sma5 = df["4. close"].rolling(5).mean().iloc[-1]

        sma20 = df["4. close"].rolling(20).mean().iloc[-1]

        momentum = (
            (latest_price - sma20) / sma20
        ) * 100

        volatility = (
            df["4. close"].pct_change().std()
        ) * 100

        sentiment_bonus = 10

        score = (
            momentum * 2
            - volatility
            + sentiment_bonus
        )

        return {
            "ticker": symbol,
            "price": round(latest_price, 2),
            "momentum": round(momentum, 2),
            "volatility": round(volatility, 2),
            "score": round(score, 2),
            "daily_change": quote["change_percent"]
        }

    except:
        return None

# =====================================================
# TOP PICKS
# =====================================================
@app.route("/top_picks")
def top_picks():

    results = []

    for symbol in WATCHLIST:

        stock = score_stock(symbol)

        if stock:
            results.append(stock)

    results = sorted(
        results,
        key=lambda x: x["score"],
        reverse=True
    )

    top = results[:8]

    return jsonify({
        "generated_at": str(datetime.utcnow()),
        "market_mode": "growth",
        "top_picks": top
    })

# =====================================================
# PORTFOLIO GENERATOR
# =====================================================
def generate_portfolio(strategy):

    results = []

    for symbol in WATCHLIST:

        stock = score_stock(symbol)

        if stock:
            results.append(stock)

    results = sorted(
        results,
        key=lambda x: x["score"],
        reverse=True
    )

    if strategy == "swing":
        selected = results[:6]

    elif strategy == "quarterly":
        selected = results[:8]

    else:
        selected = results[:10]

    total_score = sum(
        max(stock["score"], 1)
        for stock in selected
    )

    portfolio = []

    for stock in selected:

        allocation = (
            max(stock["score"], 1)
            / total_score
        ) * 100

        portfolio.append({
            "ticker": stock["ticker"],
            "allocation_percent": round(allocation, 2),
            "score": stock["score"],
            "price": stock["price"]
        })

    return portfolio

# =====================================================
# SWING PORTFOLIO
# =====================================================
@app.route("/portfolio/swing")
def swing_portfolio():

    portfolio = generate_portfolio("swing")

    return jsonify({
        "strategy": "swing_trading",
        "rebalance": "weekly",
        "generated_at": str(datetime.utcnow()),
        "portfolio": portfolio
    })

# =====================================================
# QUARTERLY PORTFOLIO
# =====================================================
@app.route("/portfolio/quarterly")
def quarterly_portfolio():

    portfolio = generate_portfolio("quarterly")

    return jsonify({
        "strategy": "quarterly_growth",
        "rebalance": "quarterly",
        "generated_at": str(datetime.utcnow()),
        "portfolio": portfolio
    })

# =====================================================
# YEARLY PORTFOLIO
# =====================================================
@app.route("/portfolio/yearly")
def yearly_portfolio():

    portfolio = generate_portfolio("yearly")

    return jsonify({
        "strategy": "long_term_compounding",
        "rebalance": "yearly",
        "generated_at": str(datetime.utcnow()),
        "portfolio": portfolio
    })

# =====================================================
# LOCAL RUN
# =====================================================
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
