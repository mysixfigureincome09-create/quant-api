from flask import Flask, jsonify, request
import yfinance as yf
import pandas as pd
import numpy as np

app = Flask(__name__)

# =========================
# HOME ROUTE
# =========================
@app.route("/")
def home():
    return jsonify({
        "status": "running",
        "message": "Quant API is live"
    })

# =========================
# STOCK ANALYSIS ROUTE
# =========================
@app.route("/analyze", methods=["GET"])
def analyze():

    ticker = request.args.get("ticker", "").upper()

    if not ticker:
        return jsonify({
            "error": "Ticker required"
        }), 400

    try:
        stock = yf.Ticker(ticker)

        hist = stock.history(period="3mo")

        if hist.empty:
            return jsonify({
                "error": "Invalid ticker"
            }), 404

        close = hist["Close"]

        sma20 = close.rolling(20).mean().iloc[-1]
        sma50 = close.rolling(50).mean().iloc[-1]
        current = close.iloc[-1]

        change = ((current - close.iloc[-2]) / close.iloc[-2]) * 100

        signal = "HOLD"

        if current > sma20 > sma50:
            signal = "BUY"

        elif current < sma20 < sma50:
            signal = "SELL"

        return jsonify({
            "ticker": ticker,
            "current_price": round(float(current), 2),
            "daily_change_percent": round(float(change), 2),
            "sma20": round(float(sma20), 2),
            "sma50": round(float(sma50), 2),
            "signal": signal
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


# =========================
# RENDER START
# =========================
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
