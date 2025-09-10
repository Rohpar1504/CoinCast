import numpy as np
import pandas as pd
from typing import Literal, Tuple, Dict

from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA

# ---------- Base forecasts ----------

def holt_forecast(series: pd.Series, horizon: int) -> pd.DataFrame:
    y = series.astype(float)
    model = ExponentialSmoothing(y, trend="add", seasonal=None, initialization_method="estimated")
    fit = model.fit(optimized=True)
    preds = fit.forecast(horizon)

    # residual-based 95% interval
    fitted = fit.fittedvalues.reindex(y.index)
    resid = y - fitted
    sigma = float(np.nanstd(resid))
    idx = pd.date_range(y.index[-1] + pd.Timedelta(days=1), periods=horizon, freq="D")
    out = pd.DataFrame({"yhat": preds.values}, index=idx)
    out["yhat_lower"] = out["yhat"] - 1.96 * sigma
    out["yhat_upper"] = out["yhat"] + 1.96 * sigma
    return out

def arima_logprice_forecast(series: pd.Series, horizon: int, order=(1,1,1)) -> pd.DataFrame:
    # model log price to stabilize variance
    y = series.astype(float)
    logp = np.log(y)
    model = ARIMA(logp, order=order)
    fit = model.fit()
    fc = fit.get_forecast(steps=horizon)
    log_mean = fc.predicted_mean
    ci = fc.conf_int(alpha=0.05)

    mean = np.exp(log_mean)
    lower = np.exp(ci.iloc[:, 0])
    upper = np.exp(ci.iloc[:, 1])

    idx = pd.date_range(y.index[-1] + pd.Timedelta(days=1), periods=horizon, freq="D")
    out = pd.DataFrame({"yhat": mean.values, "yhat_lower": lower.values, "yhat_upper": upper.values}, index=idx)
    return out

# ---------- Rolling backtest & selection ----------

def _mae(a, b):
    return float(np.mean(np.abs(np.asarray(a) - np.asarray(b))))

def rolling_backtest(series: pd.Series, model_name: Literal["holt","arima"],
                     horizon: int = 7, start_days: int = 300, step: int = 7) -> float:
    """Return average MAE over rolling splits; lower is better."""
    errs = []
    for cut in range(start_days, len(series) - horizon, step):
        train = series.iloc[:cut]
        test = series.iloc[cut:cut + horizon]

        if model_name == "holt":
            pred = holt_forecast(train, horizon)
        else:
            pred = arima_logprice_forecast(train, horizon)

        yhat = pred["yhat"].reindex(test.index)
        errs.append(_mae(test.values, yhat.values))
    return float(np.mean(errs)) if errs else np.inf

def best_model(series: pd.Series, horizon: int) -> Tuple[str, Dict[str, float]]:
    """Pick the better model by recent backtest MAE."""
    # limit training window to recent ~720d to reduce regime drift
    s = series.tail(720)
    mae_holt = rolling_backtest(s, "holt", horizon=horizon, start_days=min(300, max(120, len(s)//2)))
    mae_arima = rolling_backtest(s, "arima", horizon=horizon, start_days=min(300, max(120, len(s)//2)))
    if mae_arima < mae_holt:
        return "arima", {"holt": mae_holt, "arima": mae_arima}
    return "holt", {"holt": mae_holt, "arima": mae_arima}

def ensemble_forecast(series: pd.Series, horizon: int) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """Error-weighted ensemble of Holt + ARIMA based on recent MAE."""
    s = series.tail(720)
    # backtest MAE
    mae_holt = rolling_backtest(s, "holt", horizon=horizon, start_days=min(300, max(120, len(s)//2)))
    mae_arima = rolling_backtest(s, "arima", horizon=horizon, start_days=min(300, max(120, len(s)//2)))

    # forecasts
    f_h = holt_forecast(s, horizon)
    f_a = arima_logprice_forecast(s, horizon)

    # weights inversely proportional to MAE (add eps to avoid div/0)
    eps = 1e-6
    w_h = 1.0 / (mae_holt + eps)
    w_a = 1.0 / (mae_arima + eps)
    w_sum = w_h + w_a
    w_h /= w_sum; w_a /= w_sum

    yhat = w_h * f_h["yhat"].values + w_a * f_a["yhat"].values
    # conservative interval: union of bands
    lower = np.minimum(f_h["yhat_lower"].values, f_a["yhat_lower"].values)
    upper = np.maximum(f_h["yhat_upper"].values, f_a["yhat_upper"].values)

    out = pd.DataFrame({"yhat": yhat, "yhat_lower": lower, "yhat_upper": upper}, index=f_h.index)
    weights = {"holt": float(w_h), "arima": float(w_a), "mae_holt": float(mae_holt), "mae_arima": float(mae_arima)}
    return out, weights

# ---------- Public entry point ----------

def forecast(series: pd.Series, horizon: int, mode: Literal["holt","arima","best","ensemble"]="best"):
    """
    mode:
      - 'holt'      : Holt only
      - 'arima'     : ARIMA(log-price) only
      - 'best'      : pick better by recent MAE
      - 'ensemble'  : error-weighted average
    """
    s = series.tail(720)  # recent training window
    if mode == "holt":
        fc = holt_forecast(s, horizon)
        info = {"model": "holt"}
    elif mode == "arima":
        fc = arima_logprice_forecast(s, horizon)
        info = {"model": "arima"}
    elif mode == "ensemble":
        fc, w = ensemble_forecast(s, horizon)
        info = {"model": "ensemble", **w}
    else:  # best
        m, maes = best_model(s, horizon)
        fc = holt_forecast(s, horizon) if m == "holt" else arima_logprice_forecast(s, horizon)
        info = {"model": m, **maes}
    return fc, info
