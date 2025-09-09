import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def forecast_series(series: pd.Series, horizon: int = 7) -> pd.DataFrame:
    """
    Holt's Exponential Smoothing (additive trend, no seasonality)
    Returns DataFrame indexed by future dates with columns: yhat, yhat_lower, yhat_upper
    """
    # Ensure numeric dtype
    y = series.astype(float)

    model = ExponentialSmoothing(
        y, trend="add", seasonal=None, initialization_method="estimated"
    )
    fit = model.fit(optimized=True)
    preds = fit.forecast(horizon)

    # Residual-based 95% intervals (naive but effective for MVP)
    fitted = fit.fittedvalues.reindex(y.index)
    resid = y - fitted
    sigma = float(np.nanstd(resid))

    idx_future = pd.date_range(y.index[-1] + pd.Timedelta(days=1), periods=horizon, freq="D")
    out = pd.DataFrame({"yhat": preds.values}, index=idx_future)
    out["yhat_lower"] = out["yhat"] - 1.96 * sigma
    out["yhat_upper"] = out["yhat"] + 1.96 * sigma
    return out
