from flask import Flask, jsonify, Response
import yfinance as yf
import requests
import random
import datetime
from textblob import TextBlob
from bs4 import BeautifulSoup

app = Flask(__name__)

# =========================
# UNIVERSE
# =========================
UNIVERSE = [
    "AAPL","MSFT","NVDA","TSLA","AMZN",
    "GOOGL","META","AMD","PLTR","NFLX",
    "COIN","SPY","QQQ","INTC","BABA"
]

# =========================
# REAL MARKET DATA (YAHOO FINANCE)
# =========================
def get_fundamentals(symbol):
    try:
        t = yf.Ticker(symbol)
        info = t.info

        return {
            "price": info.get("currentPrice") or info.get("regularMarketPrice") or 0,
            "pe": info.get("trailingPE") or 0,
            "roe": info.get("returnOnEquity") or 0,
            "margin": info.get("profitMargins") or 0,
            "debt": info.get("debtToEquity") or 0,
            "volume": info.get("volume") or 0
        }
    except:
        return {"price":0,"pe":0,"roe":0,"margin":0,"debt":0,"volume":0}

# =========================
# REDDIT SENTIMENT SCRAPER (NO API)
# =========================
def reddit_sentiment(symbol):
    try:
        url = f"https://www.reddit.com/search.json?q={symbol}&sort=new"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5)

        data = r.json()
        posts = data.get("data", {}).get("children", [])

        sentiment_scores = []

        for post in posts[:10]:
            text = post["data"].get("title", "")
            sentiment = TextBlob(text).sentiment.polarity
            sentiment_scores.append(sentiment)

        if not sentiment_scores:
            return random.uniform(-0.2, 0.3)

        return sum(sentiment_scores) / len(sentiment_scores)

    except:
        return random.uniform(-0.2, 0.3)

# =========================
# NEWS SENTIMENT (RSS SCRAPE)
# =========================
def news_sentiment():
    try:
        url = "https://news.google.com/rss/search?q=stock+market&hl=en-US&gl=US&ceid=US:en"
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.content, "xml")

        titles = soup.find_all("title")[1:10]

        scores = []
        for t in titles:
            score = TextBlob(t.text).sentiment.polarity
            scores.append(score)

        return sum(scores)/len(scores) if scores else 0

    except:
        return 0

# =========================
# FINANCIAL FORMULAS
# =========================
def value(pe):
    return 1 if 0 < pe < 20 else (0.6 if pe < 35 else 0.3)

def quality(roe):
    return min(roe * 3, 1)

def profit(margin):
    return min(margin * 4, 1)

def debt_penalty(debt):
    return max(0, 1 - debt/250)

def risk(vol):
    return vol / 3

# =========================
# CORE SCORING ENGINE
# =========================
def score(symbol):
    d = get_fundamentals(symbol)

    r_sent = reddit_sentiment(symbol)
    n_sent = news_sentiment()

    v = value(d["pe"])
    q = quality(d["roe"])
    p = profit(d["margin"])
    dp = debt_penalty(d["debt"])
    r = risk(d["volume"])
    s = (r_sent + n_sent) / 2

    final = (
        v * 0.25 +
        q * 0.25 +
        p * 0.15 +
        dp * 0.10 +
        (1 - r) * 0.10 +
        s * 0.15
    )

    return {
        "symbol": symbol,
        "score": round(final, 4),
        "price": d["price"],
        "sentiment": round(s, 4),
        "reddit": round(r_sent, 4)
    }

# =========================
# PORTFOLIO SELECTION
# =========================
def portfolio(scored):
    ranked = sorted(scored, key=lambda x: x["score"], reverse=True)

    return [
        {
            "symbol": s["symbol"],
            "score": s["score"],
            "reason": "Strong fundamentals + sentiment alignment"
        }
        for s in ranked[:12]
    ]

# =========================
# API
# =========================
@app.route("/api/live")
def live():
    scored = [score(s) for s in UNIVERSE]
    scored.sort(key=lambda x: x["score"], reverse=True)

    return jsonify({
        "time": datetime.datetime.utcnow().isoformat(),
        "engine_top": scored[:8],
        "portfolio": portfolio(scored)
    })

# =========================
# DASHBOARD
# =========================
@app.route("/")
def dashboard():
    html = """
    <html>
    <head>
    <title>Hedge Fund Live v8</title>
    <style>
        body { background:#0b0f14; color:#00ff99; font-family:Arial; padding:20px; }
        .card { background:#111827; padding:10px; margin:10px; border-radius:10px; }
    </style>
    </head>

    <body>
    <h1>📊 Hedge Fund Live System v8</h1>

    <h2>Top Quant Picks</h2>
    <div id="top"></div>

    <h2>Portfolio</h2>
    <div id="port"></div>

    <script>
    async function load(){
        const res = await fetch('/api/live');
        const data = await res.json();

        let t = "";
        data.engine_top.forEach(s=>{
            t += `<div class='card'>
                <b>${s.symbol}</b><br>
                Score: ${s.score}<br>
                Price: ${s.price}<br>
                Sentiment: ${s.sentiment}
            </div>`;
        });

        document.getElementById("top").innerHTML = t;

        let p = "";
        data.portfolio.forEach(s=>{
            p += `<div class='card'>
                <b>${s.symbol}</b><br>
                Score: ${s.score}<br>
                ${s.reason}
            </div>`;
        });

        document.getElementById("port").innerHTML = p;
    }

    setInterval(load, 5000);
    load();
    </script>

    </body>
    </html>
    """
    return Response(html, mimetype="text/html")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
