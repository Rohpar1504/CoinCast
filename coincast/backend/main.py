from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.data import fetch_history, COINS
from backend.modeling import forecast  # uses holt/arima/best/ensemble

app = FastAPI(title="CoinCast API", version="0.2.0")

# ---- CORS (dev-friendly; tighten for production) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*"  # allow all during local dev; remove in prod
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Schemas ----
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
    model_info: Dict[str, Any]

# ---- Routes ----
@app.get("/api/coins")
def list_coins() -> List[Dict[str, str]]:
    """List supported coins (id + human name) for the dropdown."""
    return [{"id": k, "name": v} for k, v in COINS.items()]

@app.get("/api/predict", response_model=ForecastResponse)
async def predict(
    coin_id: str,
    horizon: int = 7,
    days: int = 365,
    model: str = "best",  # "holt" | "arima" | "best" | "ensemble"
):
    if coin_id not in COINS:
        raise HTTPException(400, f"Unsupported coin_id: {coin_id}")
    if horizon not in (7, 14, 30, 60):
        raise HTTPException(400, "horizon must be 7, 14, 30, or 60")
    if model not in ("holt", "arima", "best", "ensemble"):
        raise HTTPException(400, "model must be one of: holt, arima, best, ensemble")

    # Fetch history (cached) and generate forecast
    series = await fetch_history(coin_id, days=days)
    fc_df, info = forecast(series, horizon=horizon, mode=model)

    # Send only recent history to client (e.g., last ~6 months)
    hist_tail = series.tail(180)

    # Convert pandas timestamps (ns) to milliseconds for Chart.js
    history = [
        {"t": int(idx.value // 1_000_000), "price": float(val)}
        for idx, val in hist_tail.items()
    ]
    forecast_points = [
        {
            "t": int(idx.value // 1_000_000),
            "yhat": float(row.yhat),
            "yhat_lower": float(row.yhat_lower),
            "yhat_upper": float(row.yhat_upper),
        }
        for idx, row in fc_df.iterrows()
    ]

    return {
        "coin_id": coin_id,
        "history": history,
        "forecast": forecast_points,
        "model_info": info,
    }

# (optional) simple health check
@app.get("/api/health")
def health():
    return {"status": "ok"}
