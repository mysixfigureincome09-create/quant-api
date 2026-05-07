from flask import Flask, jsonify
from flask_cors import CORS
import requests
import pandas as pd
import os

# =========================================
# APP SETUP
# =========================================
app = Flask(__name__)
CORS(app)

# =========================================
# API CONFIG
# =========================================
API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

# =========================================
# HOME ROUTE
# =========================================
@app.route("/")
def home():
    return jsonify({
        "message": "Quant API is live",
        "status": "running"
    })

# =========================================
# STATUS ROUTE
# =========================================
@app.route("/status")
def status():
    return jsonify({
        "status": "ok",
        "server": "running"
    })

# =========================================
# DASHBOARD
# =========================================
@app.route("/dashboard")
def dashboard():

    return """
    <html>

    <head>
        <title>Quant Dashboard</title>

        <style>

            body {
                background-color: #0f1117;
                color: white;
                font-family: Arial;
                padding: 40px;
            }

            .card {
                background: #1c1f26;
                padding: 25px;
                border-radius: 12px;
                margin-bottom: 20px;
            }

            h1 {
                color: #00ff99;
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

        <h1>Quant Dashboard</h1>

        <div class="card">
            <h2>API Status</h2>
            <p>ONLINE</p>
        </div>

        <div class="card">
            <h2>Stock Endpoints</h2>

            <ul>
                <li><a href="/price/AAPL">AAPL Live Price</a></li>
                <li><a href="/analyze/AAPL">Analyze AAPL</a></li>

                <li><a href="/price/TSLA">TSLA Live Price</a></li>
                <li><a href="/analyze/TSLA">Analyze TSLA</a></li>

                <li><a href="/price/NVDA">NVDA Live Price</a></li>
                <li><a href="/analyze/NVDA">Analyze NVDA</a></li>
            </ul>

        </div>

    </body>

    </html>
    """

# =========================================
# LIVE STOCK PRICE
# =========================================
@app.route("/price/<symbol>")
def price(symbol):

    symbol = symbol.upper()

    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": API_KEY
    }

    try:

        response = requests.get(BASE_URL, params=params)
        data = response.json()

        print(data)

        if "Global Quote" not in data:
            return jsonify({
                "error": "Stock data unavailable",
                "details": data
            }), 500

        quote = data["Global Quote"]

        return jsonify({
            "symbol": quote.get("01. symbol"),
            "price": quote.get("05. price"),
            "change": quote.get("09. change"),
            "percent_change": quote.get("10. change percent")
        })

    except Exception as e:

        return jsonify({
            "error": "data fetch failed",
            "details": str(e)
        }), 500

# =========================================
# STOCK ANALYSIS
# =========================================
@app.route("/analyze/<symbol>")
def analyze(symbol):

    symbol = symbol.upper()

    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": API_KEY
    }

    try:

        response = requests.get(BASE_URL, params=params)
        data = response.json()

        print(data)

        if "Time Series (Daily)" not in data:
            return jsonify({
                "error": "Analysis unavailable",
                "details": data
            }), 500

        ts = data["Time Series (Daily)"]

        df = pd.DataFrame.from_dict(ts, orient="index")

        df = df.astype(float)

        df = df.sort_index()

        # Moving averages
        df["SMA5"] = df["4. close"].rolling(5).mean()
        df["SMA20"] = df["4. close"].rolling(20).mean()

        latest = df.iloc[-1]

        signal = "HOLD"

        if latest["SMA5"] > latest["SMA20"]:
            signal = "BUY"

        elif latest["SMA5"] < latest["SMA20"]:
            signal = "SELL"

        return jsonify({
            "symbol": symbol,
            "current_price": round(latest["4. close"], 2),
            "sma5": round(latest["SMA5"], 2),
            "sma20": round(latest["SMA20"], 2),
            "signal": signal
        })

    except Exception as e:

        return jsonify({
            "error": "analysis failed",
            "details": str(e)
        }), 500

# =========================================
# LOCAL RUN
# =========================================
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
