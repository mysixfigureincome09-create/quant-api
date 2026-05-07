from flask import Flask, jsonify, Response
import requests
import random
import datetime
from textblob import TextBlob
from bs4 import BeautifulSoup

app = Flask(__name__)

# =========================
# UNIVERSE
# =========================
STOCKS = [
    "AAPL","MSFT","NVDA","TSLA","AMZN",
    "GOOGL","META","AMD","PLTR","NFLX",
    "COIN","SPY","QQQ"
]

CRYPTO = [
    "bitcoin","ethereum","solana","ripple",
    "cardano","dogecoin","chainlink"
]

# =========================
# AI SCRAPING: REDDIT SENTIMENT
# =========================
def reddit_sentiment(query):
    try:
        url = f"https://www.reddit.com/search.json?q={query}&sort=new"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5)
        data = r.json()

        posts = data.get("data", {}).get("children", [])
        scores = []

        for p in posts[:10]:
            text = p["data"].get("title", "")
            scores.append(TextBlob(text).sentiment.polarity)

        return sum(scores)/len(scores) if scores else random.uniform(-0.2,0.3)

    except:
        return random.uniform(-0.2,0.3)

# =========================
# AI SCRAPING: NEWS SENTIMENT
# =========================
def news_sentiment():
    try:
        url = "https://news.google.com/rss/search?q=stocks&hl=en-US&gl=US&ceid=US:en"
        r = requests.get(url, timeout=5)

        soup = BeautifulSoup(r.content, "xml")
        titles = soup.find_all("title")[1:10]

        scores = [TextBlob(t.text).sentiment.polarity for t in titles]

        return sum(scores)/len(scores) if scores else 0

    except:
        return 0

# =========================
# MARKET SIMULATION (still needed for structure)
# =========================
def market_data(symbol):
    return {
        "price": round(random.uniform(50,600),2),
        "momentum": random.uniform(-1,1),
        "volatility": random.uniform(0.1,0.7)
    }

# =========================
# CRYPTO DATA (real API)
# =========================
def crypto_data(cid):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={cid}&vs_currencies=usd&include_24hr_change=true"
        r = requests.get(url, timeout=5)
        d = r.json().get(cid, {})

        return {
            "price": d.get("usd",0),
            "momentum": (d.get("usd_24h_change",0))/10,
            "volatility": abs(d.get("usd_24h_change",0))/10
        }
    except:
        return {"price":0,"momentum":0,"volatility":0.5}

# =========================
# SCORING ENGINE (AI + MARKET FUSION)
# =========================
def score_asset(symbol, asset_type="stock"):

    if asset_type == "stock":
        m = market_data(symbol)
        sentiment = (reddit_sentiment(symbol) + news_sentiment()) / 2
    else:
        m = crypto_data(symbol)
        sentiment = reddit_sentiment(symbol)

    score = (
        m["momentum"] * 0.4 +
        sentiment * 0.4 +
        (1 - m["volatility"]) * 0.2
    )

    if score > 0.35:
        signal = "BUY 🚀"
    elif score < -0.2:
        signal = "SELL 🔻"
    else:
        signal = "HOLD ⚖️"

    return {
        "symbol": symbol,
        "score": round(score,4),
        "price": m["price"],
        "sentiment": round(sentiment,4),
        "signal": signal,
        "type": asset_type
    }

# =========================
# PORTFOLIO BUILDER
# =========================
def build_portfolio(all_assets):
    return sorted(all_assets, key=lambda x: x["score"], reverse=True)[:12]

# =========================
# API
# =========================
@app.route("/api/live")
def live():

    stocks = [score_asset(s,"stock") for s in STOCKS]
    cryptos = [score_asset(c,"crypto") for c in CRYPTO]

    combined = stocks + cryptos

    return jsonify({
        "time": datetime.datetime.utcnow().isoformat(),
        "top_stocks": sorted(stocks, key=lambda x:x["score"], reverse=True)[:6],
        "top_crypto": sorted(cryptos, key=lambda x:x["score"], reverse=True)[:6],
        "portfolio": build_portfolio(combined)
    })

# =========================
# DASHBOARD
# =========================
@app.route("/")
def dashboard():
    html = """
    <html>
    <head>
        <title>Hedge Fund AI Scraper v10</title>
        <style>
            body { background:#0b0f14; color:#00ff99; font-family:Arial; padding:20px; }
            .card { background:#111827; padding:10px; margin:10px; border-radius:10px; }
        </style>
    </head>

    <body>
        <h1>🧠 Hedge Fund AI Scraper v10</h1>

        <h2>📈 Stocks</h2>
        <div id="stocks"></div>

        <h2>🪙 Crypto</h2>
        <div id="crypto"></div>

        <h2>📌 Portfolio</h2>
        <div id="portfolio"></div>

        <script>
        async function load(){
            const res = await fetch('/api/live');
            const d = await res.json();

            let s="";
            d.top_stocks.forEach(x=>{
                s += `<div class='card'>
                    <b>${x.symbol}</b><br>
                    Score: ${x.score}<br>
                    Sentiment: ${x.sentiment}<br>
                    Signal: ${x.signal}
                </div>`;
            });

            let c="";
            d.top_crypto.forEach(x=>{
                c += `<div class='card'>
                    <b>${x.symbol}</b><br>
                    Score: ${x.score}<br>
                    Sentiment: ${x.sentiment}<br>
                    Signal: ${x.signal}
                </div>`;
            });

            let p="";
            d.portfolio.forEach(x=>{
                p += `<div class='card'>
                    <b>${x.symbol}</b> (${x.type})<br>
                    Score: ${x.score}<br>
                    Signal: ${x.signal}
                </div>`;
            });

            document.getElementById("stocks").innerHTML=s;
            document.getElementById("crypto").innerHTML=c;
            document.getElementById("portfolio").innerHTML=p;
        }

        setInterval(load,5000);
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
