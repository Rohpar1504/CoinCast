<<<<<<< HEAD
# CoinCast 📈💰

A cryptocurrency price forecasting dashboard built with FastAPI, React, and Machine Learning.

<img width="536" height="736" alt="Screenshot 2025-09-09 at 6 16 28 PM" src="https://github.com/user-attachments/assets/510f2471-c1a9-4bca-9bfa-8ecbeff525c7" />

## 🚀 Features

- Predict prices for 10+ popular cryptocurrencies (BTC, ETH, SOL, etc.).

- Interactive dashboard with clean UI (React + Bootstrap).

- Historical + forecast plots using Chart.js.

- Time-series forecasting with Holt’s Exponential Smoothing (statsmodels).

- REST API backend (FastAPI) serving predictions with confidence intervals.

- Live crypto market data pulled from the CoinGecko API.

## 🛠️ Tech Stack

### Frontend

- React (Vite)

- React-Bootstrap

- Chart.js + chartjs-adapter-date-fns

- Axios

### Backend

- Python 3.12

- FastAPI

- Statsmodels, Pandas, NumPy

- HTTPX (for CoinGecko API calls)

## ⚡ Quick Start

### 1. Clone the Repo
git clone https://github.com/<your-username>/CoinCast.git

cd CoinCast

### 2. Backend setup (FastAPI)
cd coincast

python3 -m venv .venv

source .venv/bin/activate   # Mac/Linux

#### # .venv\Scripts\activate    # Windows

pip install -r requirements.txt

uvicorn backend.main:app --reload

#### Backend runs at 👉 http://127.0.0.1:8000

#### Docs 👉 http://127.0.0.1:8000/docs

### 3. Frontend setup (React + Vite)
cd frontend/coincast-frontend

npm install

npm run dev

#### Frontend runs at 👉 http://localhost:5173

## 📊 Example API Call

curl "http://127.0.0.1:8000/api/predict?coin_id=bitcoin&horizon=7"

### Response:
{
  "coin_id": "bitcoin",
  "history": [
    {"t": 1694304000000, "price": 27234.5},
    ...
  ],
  "forecast": [
    {"t": 1696896000000, "yhat": 28000.1, "yhat_lower": 26800.5, "yhat_upper": 29200.7},
    ...
  ]
}

## 📌 Future Improvements

- Add ARIMA/Prophet model comparison.

- Backtesting metrics (MAPE, RMSE).

- Deploy backend (Render/Heroku) + frontend (Netlify/Vercel).

- Support for multiple coins on the same chart.

## ⚠️ Disclaimer

This project is for educational/demo purposes only. Forecasts are not investment advice.
=======
# CoinCast

A cryptocurrency price forecasting dashboard built with FastAPI, React, and Machine Learning.
>>>>>>> a71675d (feat: add ARIMA + ensemble forecasting and expose model info in API)
