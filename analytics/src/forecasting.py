"""SARIMA forecasting with an honest backtest (CLAUDE.md §18.3)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

Order = tuple[int, int, int]
SeasonalOrder = tuple[int, int, int, int]


def _fit(series: pd.Series, order: Order, seasonal_order: SeasonalOrder):
    return SARIMAX(
        series, order=order, seasonal_order=seasonal_order,
        enforce_stationarity=False, enforce_invertibility=False,
    ).fit(disp=False)


def backtest(series: pd.Series, order: Order, seasonal_order: SeasonalOrder,
             horizon: int = 12) -> dict:
    """Hold out the last `horizon` points, fit on the rest, score the forecast."""
    train, test = series.iloc[:-horizon], series.iloc[-horizon:]
    forecast = _fit(train, order, seasonal_order).forecast(horizon)
    err = test.values - forecast.values
    return {
        "mape": float(np.mean(np.abs(err / test.values)) * 100),
        "mae": float(np.mean(np.abs(err))),
        "test": test,
        "forecast": pd.Series(forecast.values, index=test.index),
    }


def fit_forecast(series: pd.Series, order: Order, seasonal_order: SeasonalOrder,
                 horizon: int = 12, alpha: float = 0.05) -> dict:
    """Fit on the full series and forecast `horizon` ahead with a (1-alpha) PI."""
    res = _fit(series, order, seasonal_order).get_forecast(horizon)
    ci = res.conf_int(alpha=alpha)
    return {"mean": res.predicted_mean, "ci": ci}
