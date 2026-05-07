from flask import Flask, jsonify, render_template
from flask_cors import CORS
import os
import random
import datetime
import yfinance as yf
from openai import OpenAI

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

UNIVERSE = [
    "AAPL","MSFT","NVDA","TSLA","AMZN",
    "GOOGL","META","AMD","PLTR","NFLX",
    "COIN","SPY","QQQ","INTC","BABA"
]

# -------------------------
# MARKET DATA LAYER
# -------------------------
def get_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info or {}

        return {
            "price": info.get("currentPrice") or info.get("regularMarketPrice") or 0,
            "pe": info.get("trailingPE") or 0,
            "roe": info.get("returnOnEquity") or 0,
            "margin": info.get("profitMargins") or 0,
            "market_cap": info.get("marketCap") or 0
        }
    except:
        return {"price":0,"pe":0,"roe":0,"margin":0,"market_cap":0}

# -------------------------
# QUANT SCORE ENGINE
# -------------------------
def score(symbol):
    d = get_data(symbol)

    value = 1 if 0 < d["pe"] < 25 else 0.5
    quality = min(d["roe"] * 3, 1)
    profit = min(d["margin"] * 5, 1)
    momentum = random.uniform(0, 1)
    sentiment = random.uniform(-0.3, 1)

    final = (
        value * 0.3 +
        quality * 0.25 +
        profit * 0.2 +
        momentum * 0.15 +
        sentiment * 0.1
    )

    return {
        "symbol": symbol,
        "score": round(final, 4),
        "price": d["price"],
        "sentiment": sentiment
    }

# -------------------------
# OPENAI PORTFOLIO ENGINE
# -------------------------
def ai_portfolio(scored):
    try:
        payload = [
            {
                "symbol": s["symbol"],
                "score": s["score"],
                "sentiment": s["sentiment"],
                "price": s["price"]
            }
            for s in scored
        ]

        prompt = f"""
You are a hedge fund portfolio manager.

Select 6–12 stocks from this dataset.

Rules:
- maximize risk-adjusted returns
- prefer high score + strong sentiment
- diversify sectors
Return JSON ONLY:
{{
  "portfolio": [
    {{"symbol": "...", "reason": "..."}}
  ]
}}

DATA:
{payload}
"""

        res = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a hedge fund quant PM."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        return res.choices[0].message.content

    except Exception as e:
        return str(e)

# -------------------------
# LIVE API ENDPOINT
# -------------------------
@app.route("/api/live")
def live():
    scored = [score(s) for s in UNIVERSE]
    scored.sort(key=lambda x: x["score"], reverse=True)

    ai = ai_portfolio(scored)

    return jsonify({
        "time": datetime.datetime.utcnow().isoformat(),
        "engine_top": scored[:8],
        "ai_portfolio": ai
    })

# -------------------------
# DASHBOARD PAGE
# -------------------------
@app.route("/")
def dashboard():
    return render_template("index.html")

# -------------------------
# RENDER ENTRY
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
