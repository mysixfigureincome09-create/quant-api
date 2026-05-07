from flask import Flask, jsonify
import requests
import os
import pandas as pd
import numpy as np
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
@app.route("/")

@app.route("/")
def home():
    return jsonify({"message": "Quant API is live", "status": "running"})


# 👇 ADD IT RIGHT HERE (same level as other routes)
@app.route("/dashboard")
def dashboard():
    return """
    <html>
        <h1>Quant Dashboard</h1>
        <p>API Running</p>
        <ul>
            <li>/price/AAPL</li>
            <li>/analyze/AAPL</li>
        </ul>
    </html>
    """
# =========================
# CONFIG
# =========================
API_KEY = "JXJUT1ZYW2ES67X1"
BASE_URL = "https://www.alphavantage.co/query"

# simple in-memory cache
cache = {}

# =========================
# HEALTH CHECK
# =========================
@app.route("/")
def home():
    return jsonify({"message": "Quant API is live", "status": "running"})


@app.route("/status")
def status():
    return jsonify({
        "status": "ok",
        "cache_size": len(cache)
    })

# =========================
# LIVE PRICE
# =========================
@app.route("/price/<symbol>")
def price(symbol):
    symbol = symbol.upper()

    if symbol in cache:
        return jsonify(cache[symbol])

    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": "5min",
        "apikey": API_KEY
    }

    r = requests.get(BASE_URL, params=params)
    data = r.json()

    try:
        timeseries = data["Time Series (5min)"]
        latest_time = list(timeseries.keys())[0]
        price = float(timeseries[latest_time]["4. close"])

        result = {
            "symbol": symbol,
            "price": price,
            "time": latest_time
        }

        cache[symbol] = result
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": "data fetch failed", "details": str(e)}), 500


# =========================
# SIMPLE TRADING SIGNAL
# =========================
@app.route("/analyze/<symbol>")
def analyze(symbol):
    symbol = symbol.upper()

    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": API_KEY
    }

    r = requests.get(BASE_URL, params=params)
    data = r.json()

    try:
        ts = data["Time Series (Daily)"]

        df = pd.DataFrame.from_dict(ts, orient="index")
        df = df.astype(float)
        df = df.sort_index()

        df["SMA_5"] = df["4. close"].rolling(5).mean()
        df["SMA_20"] = df["4. close"].rolling(20).mean()

        latest = df.iloc[-1]

        signal = "HOLD"

        if latest["SMA_5"] > latest["SMA_20"]:
            signal = "BUY"
        elif latest["SMA_5"] < latest["SMA_20"]:
            signal = "SELL"

        return jsonify({
            "symbol": symbol,
            "price": latest["4. close"],
            "signal": signal
        })

    except Exception as e:
        return jsonify({"error": "analysis failed", "details": str(e)}), 500


# =========================
# RUN (LOCAL ONLY)
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
