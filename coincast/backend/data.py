import time
import asyncio
import pandas as pd
import httpx

# Public list of supported coins (id -> nice name)
COINS = {
    "bitcoin": "Bitcoin",
    "ethereum": "Ethereum",
    "binancecoin": "BNB",
    "ripple": "XRP",
    "cardano": "Cardano",
    "solana": "Solana",
    "dogecoin": "Dogecoin",
    "polkadot": "Polkadot",
    "litecoin": "Litecoin",
    "chainlink": "Chainlink",
}

# --- Simple in-memory cache to avoid CoinGecko rate limits ---
_CACHE: dict[tuple[str, int], tuple[float, pd.Series]] = {}
TTL_SECONDS = 300  # 5 minutes


async def _sleep(s: float):
    await asyncio.sleep(s)


async def _fetch_history_nocache(coin_id: str, days: int = 365) -> pd.Series:
    """Fetch historical daily prices for a coin from CoinGecko."""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days}

    # Exponential backoff for 429/5xx
    backoff = 0.5
    for _ in range(4):
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, params=params)
        if r.status_code == 429 or 500 <= r.status_code < 600:
            await _sleep(backoff)
            backoff *= 2
            continue

        r.raise_for_status()
        prices = r.json()["prices"]  # [[ms, price], ...]
        df = pd.DataFrame(prices, columns=["ts", "price"])
        df["ts"] = pd.to_datetime(df["ts"], unit="ms")
        # Daily frequency + light interpolation for small gaps
        df = df.set_index("ts").asfreq("D").interpolate(limit_direction="both")
        return df["price"]

    # If we got here, still failing—raise the last response error
    r.raise_for_status()


async def fetch_history(coin_id: str, days: int = 365) -> pd.Series:
    """Cached fetch wrapper."""
    key = (coin_id, days)
    now = time.time()

    if key in _CACHE:
        ts, series = _CACHE[key]
        if now - ts < TTL_SECONDS:
            return series

    series = await _fetch_history_nocache(coin_id, days)
    _CACHE[key] = (now, series)
    return series
