from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
from typing import Optional

app = FastAPI()

# CORS para permitir frontend externo si lo necesitas
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/signals")
def get_signals(ticker: str = Query(..., description="Ticker de la acción")):
    df = yf.download(ticker, period="6mo", interval="1d")

    if df.empty:
        return {"error": "Ticker inválido o sin datos"}

    # Cálculo de RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    last_rsi = rsi.dropna().iloc[-1]

    # MACD
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal

    # EMAs
    ema_50 = df['Close'].ewm(span=50, adjust=False).mean()
    ema_200 = df['Close'].ewm(span=200, adjust=False).mean()

    golden_cross = ema_50.iloc[-1] > ema_200.iloc[-1] and ema_50.iloc[-2] <= ema_200.iloc[-2]

    return {
        "ticker": ticker.upper(),
        "RSI": round(last_rsi, 2),
        "MACD": {
            "macd": round(macd.iloc[-1], 2),
            "signal": round(signal.iloc[-1], 2),
            "histogram": round(histogram.iloc[-1], 2)
        },
        "EMA": {
            "EMA_50": round(ema_50.iloc[-1], 2),
            "EMA_200": round(ema_200.iloc[-1], 2),
            "golden_cross": golden_cross
        }
    }
