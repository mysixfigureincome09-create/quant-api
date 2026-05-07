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
API_KEY = "JXJUT1ZYW2ES67X1"
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
                background-color: #111;
                color: #00ff99;
                font-family: Arial;
                padding: 40px;
            }

            h1 {
                color: white;
            }

            a {
                color: #00ff99;
                text-decoration: none;
                font-size: 20px;
            }

            .box {
                background: #1c1c1c;
                padding: 20px;
                border-radius: 10px;
                margin-top: 20px;
            }
        </style>
    </head>

    <body>
        <h1>Quant Dashboard</h1>

        <div class="box">
            <p>API Status: ONLINE</p>

            <p>Test Endpoints:</p>

            <ul>
                <li><a href="/price/AAPL">AAPL Price</a></li>
                <li><a href="/analyze/AAPL">Analyze AAPL</a></li>
                <li><a href="/price/TSLA">TSLA Price</a></li>
                <li><a href="/analyze/TSLA">Analyze TSLA</a></li>
            </ul>
        </div>
    </body>
    </html>
    """

# =========================================
# LIVE PRICE ROUTE
# =========================================
@app.route("/price/<symbol>")
def price(symbol):

    symbol = symbol.upper()

    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": "5min",
        "apikey": API_KEY
    }

    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()

        # Debug logging
        print(data)

        if "Time Series (5min)" not in data:
            return jsonify({
                "error": "Stock data unavailable",
                "details": data
            }), 500

        ts = data["Time Series (5min)"]

        latest_time = list(ts.keys())[0]

        latest_price = ts[latest_time]["4. close"]

        return jsonify({
            "symbol": symbol,
            "price": latest_price,
            "time": latest_time
        })

    except Exception as e:
        return jsonify({
            "error": "data fetch failed",
            "details": str(e)
        }), 500

# =========================================
# ANALYSIS ROUTE
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
                "error": "Analysis data unavailable",
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
    app.run(host="0.0.0.0", port=port)
