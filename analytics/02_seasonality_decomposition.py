"""
Seasonality decomposition — STL on the synthetic monthly paediatric ED series.

Quantifies the seasonal strength and the winter (Jun–Aug) uplift, and saves the
trend / seasonal / residual decomposition.

SYNTHETIC data (seed=42).
Run:  python analytics/02_seasonality_decomposition.py
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from statsmodels.tsa.seasonal import STL  # noqa: E402

from src import plotting as P  # noqa: E402
from src.data import load_monthly_paediatric  # noqa: E402


def main() -> None:
    series = load_monthly_paediatric()
    stl = STL(series, period=12, robust=True).fit()

    # Seasonal strength (Wang–Smith–Hyndman): 1 - Var(resid) / Var(seasonal+resid).
    seasonal_strength = max(0.0, 1 - stl.resid.var() / (stl.seasonal + stl.resid).var())
    by_month = stl.seasonal.groupby(series.index.month).mean()
    winter_uplift = by_month.loc[[6, 7, 8]].mean()
    baseline = series.mean()
    print(f"Seasonal strength: {seasonal_strength:.2f} (0 = none, 1 = fully seasonal)")
    print(f"Winter (Jun-Aug) seasonal uplift: {winter_uplift:+,.0f} presentations/month "
          f"(~{winter_uplift / baseline:+.1%} vs mean).")
    print(f"Peak seasonal month: {by_month.idxmax()} | trough: {by_month.idxmin()}")

    P.style()
    fig = stl.plot()
    fig.set_size_inches(10, 7)
    fig.suptitle("STL decomposition — paediatric ED (SYNTHETIC)", y=1.01, fontweight="bold")
    print("saved:", P.save(fig, "02_seasonality_decomposition.png"))


if __name__ == "__main__":
    main()
