"""Funnel-plot control limits for fair institutional comparison (Spiegelhalter 2005)."""

from __future__ import annotations

import numpy as np
import pandas as pd

Z_95 = 1.959963985
Z_998 = 3.090232306


def pooled_mean(df: pd.DataFrame, p_col: str, n_col: str) -> float:
    """Volume-weighted pooled proportion."""
    return float(np.average(df[p_col], weights=df[n_col]))


def control_limit(p_bar: float, n: np.ndarray, z: float) -> np.ndarray:
    """Binomial control limit at volume n (widens as n shrinks)."""
    se = np.sqrt(p_bar * (1 - p_bar) / n)
    return np.clip(p_bar + z * se, 0, 1)


def flag_outliers(df: pd.DataFrame, p_col: str, n_col: str,
                  z: float = Z_998) -> tuple[float, pd.Series]:
    """Return (pooled mean, boolean Series flagging special-cause outliers)."""
    p_bar = pooled_mean(df, p_col, n_col)
    se = np.sqrt(p_bar * (1 - p_bar) / df[n_col])
    outlier = (df[p_col] > p_bar + z * se) | (df[p_col] < p_bar - z * se)
    return p_bar, outlier
