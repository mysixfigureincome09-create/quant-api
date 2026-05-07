from flask import Flask, jsonify, request
import os
import random
import math
import datetime
import yfinance as yf

app = Flask(__name__)

# =========================
# INTERNAL CONFIG (HIDDEN ENGINE LAYER)
# =========================
UNIVERSE = [
    "AAPL", "MSFT", "NVDA", "TSLA", "AMZN",
    "GOOGL", "META", "AMD", "PLTR", "NFLX",
    "COIN", "SPY", "QQQ", "INTC", "BABA"
]

# =========================
# DATA LAYER (FUNDAMENTALS)
# =========================
def get_fundamentals(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        return {
            "price": info.get("currentPrice") or info.get("regularMarketPrice") or 0,
            "pe": info.get("trailingPE") or 0,
            "pb": info.get("priceToBook") or 0,
            "roe": info.get("returnOnEquity") or 0,
            "debt_to_equity": info.get("debtToEquity") or 0,
            "market_cap": info.get("marketCap") or 0,
            "profit_margin": info.get("profitMargins") or 0
        }
    except:
        return {
            "price": 0, "pe": 0, "pb": 0,
            "roe": 0, "debt_to_equity": 0,
            "market_cap": 0, "profit_margin": 0
        }

# =========================
# SENTIMENT MODEL (PLACEHOLDER FOR NEWS/REDDIT/LLM)
# =========================
def sentiment_score(symbol):
    return random.uniform(-0.6, 1.0)

# =========================
# GEO + MACRO RISK MODEL
# =========================
def macro_risk():
    # Simulated macro volatility index
    return random.uniform(0, 1)

# =========================
# FINANCIAL FORMULAS (CORE QUANT MODELS)
# =========================

# 1. ROE Efficiency Score
def roe_score(roe):
    return min(max(roe / 0.25, 0), 1)

# 2. Debt Penalty Function
def debt_penalty(dte):
    if dte == 0:
        return 0.9
    return max(0, 1 - (dte / 200))

# 3. Value Score (P/E + P/B combined)
def value_score(pe, pb):
    pe_score = 1 if 0 < pe < 20 else (0.6 if pe < 35 else 0.3)
    pb_score = 1 if 0 < pb < 5 else 0.5
    return (pe_score + pb_score) / 2

# 4. Profitability Score
def profit_score(pm):
    return min(max(pm * 5, 0), 1)

# 5. CAPM-style Expected Return proxy (simplified)
def expected_return(sentiment, fundamentals):
    rf = 0.02  # risk-free rate assumption
    beta_proxy = 1 + random.uniform(-0.2, 0.4)
    market_premium = 0.06

    return rf + beta_proxy * market_premium + sentiment * 0.03

# =========================
# RISK MODEL (VOLATILITY + MACRO)
# =========================
def risk_score():
    vol = random.uniform(0.1, 0.5)
    macro = macro_risk()
    return min(vol + macro, 1)

# =========================
# SHARPE-LIKE RATIO (CORE HEDGE FUND METRIC)
# =========================
def sharpe_like(expected_ret, risk):
    if risk == 0:
        return 0
    return expected_ret / risk

# =========================
# MASTER SCORING ENGINE (HEDGE FUND CORE)
# =========================
def score_stock(symbol):
    f = get_fundamentals(symbol)
    sentiment = sentiment_score(symbol)
    risk = risk_score()

    fundamentals_score = (
        roe_score(f["roe"]) * 0.25 +
        debt_penalty(f["debt_to_equity"]) * 0.2 +
        value_score(f["pe"], f["pb"]) * 0.25 +
        profit_score(f["profit_margin"]) * 0.3
    )

    expected_ret = expected_return(sentiment, f)

    sharpe = sharpe_like(expected_ret, risk)

    final_score = (
        fundamentals_score * 0.45 +
        sentiment * 0.2 +
        sharpe * 0.25 +
        (1 - risk) * 0.1
    )

    return {
        "symbol": symbol,
        "score": round(final_score, 4),
        "sharpe_like": round(sharpe, 4),
        "expected_return": round(expected_ret, 4),
        "risk": round(risk, 4),
        "fundamentals": f,
        "sentiment": round(sentiment, 4)
    }

# =========================
# PUBLIC API (HIDDEN ENGINE)
# =========================

@app.route("/")
def home():
    return jsonify({
        "status": "active",
        "engine": "Hedge Fund Engine v3",
        "note": "internal scoring system hidden"
    })

@app.route("/recommend", methods=["GET"])
def recommend():
    results = [score_stock(s) for s in UNIVERSE]
    results.sort(key=lambda x: x["score"], reverse=True)

    return jsonify({
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "top_picks": results[:8]
    })

@app.route("/analyze", methods=["GET"])
def analyze():
    symbol = request.args.get("symbol", "AAPL").upper()
    return jsonify(score_stock(symbol))

# =========================
# RENDER SAFE ENTRY POINT
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
