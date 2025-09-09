from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

from backend.data import fetch_history, COINS
from backend.modeling import forecast_series

app = FastAPI(title="CoinCast API", version="0.1.0")

# ---- CORS (dev friendly; tighten for prod) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Response models ----
class HistoryPoint(BaseModel):
    t: int
    price: float

class ForecastPoint(BaseModel):
    t: int
    yhat: float
    yhat_lower: float
    yhat_upper: float

class ForecastResponse(BaseModel):
    coin_id: str
    history: List[HistoryPoint]
    forecast: List[ForecastPoint]


@app.get("/api/coins")
def list_coins() -> List[Dict[str, str]]:
    return [{"id": k, "name": v} for k, v in COINS.items()]


@app.get("/api/predict", response_model=ForecastResponse)
async def predict(coin_id: str, horizon: int = 7, days: int = 365):
    if coin_id not in COINS:
        raise HTTPException(400, f"Unsupported coin_id: {coin_id}")
    if horizon not in (7, 14, 30):
        raise HTTPException(400, "horizon must be 7, 14, or 30")

    # Fetch history (cached) + forecast
    series = await fetch_history(coin_id, days=days)
    fc = forecast_series(series, horizon=horizon)

    # Only send last ~6 months of history to the client
    hist_tail = series.tail(180)

    # Convert pandas indices to ms timestamps (Chart.js uses ms)
    history = [{"t": int(idx.value // 1_000_000), "price": float(val)} for idx, val in hist_tail.items()]
    forecast = [
        {
            "t": int(idx.value // 1_000_000),
            "yhat": float(row.yhat),
            "yhat_lower": float(row.yhat_lower),
            "yhat_upper": float(row.yhat_upper),
        }
        for idx, row in fc.iterrows()
    ]

    return {"coin_id": coin_id, "history": history, "forecast": forecast}
