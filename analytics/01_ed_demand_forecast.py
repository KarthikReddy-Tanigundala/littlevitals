"""
ED demand forecasting — SARIMA on the synthetic monthly paediatric ED series.

Reports a backtested error (MAPE/MAE on a 12-month holdout) BEFORE forecasting,
then forecasts 12 months ahead with a 95% prediction interval. The winter surge
is the dominant seasonal signal.

SYNTHETIC data (seed=42) — see data/sample/generate_monthly_encounters.py.
Run:  python analytics/01_ed_demand_forecast.py
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import matplotlib.pyplot as plt  # noqa: E402

from src import plotting as P  # noqa: E402
from src.data import load_monthly_paediatric  # noqa: E402
from src.forecasting import backtest, fit_forecast  # noqa: E402

ORDER = (1, 1, 1)
SEASONAL = (1, 1, 0, 12)
HORIZON = 12


def main() -> None:
    series = load_monthly_paediatric()

    bt = backtest(series, ORDER, SEASONAL, horizon=HORIZON)
    print(f"Backtest (last {HORIZON} months held out): "
          f"MAPE = {bt['mape']:.2f}%   MAE = {bt['mae']:.0f} presentations/month")

    ff = fit_forecast(series, ORDER, SEASONAL, horizon=HORIZON)
    peak = ff["mean"].idxmax()
    print(f"Next 12 months: forecast peak {ff['mean'].max():,.0f} in "
          f"{peak.strftime('%b %Y')} (winter surge).")

    P.style()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(series.index, series.values, color=P.TEAL, lw=1.8, label="History (synthetic)")
    ax.plot(bt["forecast"].index, bt["forecast"].values, color=P.AMBER, lw=1.5,
            ls="--", label="Backtest forecast")
    ax.plot(ff["mean"].index, ff["mean"].values, color=P.CORAL, lw=2, label="12-month forecast")
    ci = ff["ci"]
    ax.fill_between(ci.index, ci.iloc[:, 0], ci.iloc[:, 1], color=P.CORAL,
                    alpha=0.15, label="95% prediction interval")
    ax.set_title("Paediatric ED demand — SARIMA 12-month forecast  (SYNTHETIC)")
    ax.set_ylabel("ED presentations / month")
    ax.legend(loc="upper left", fontsize=8)
    print("saved:", P.save(fig, "01_ed_demand_forecast.png"))


if __name__ == "__main__":
    main()
