"""
Elective surgery waitlist survival — Kaplan-Meier time-to-admission by urgency
category, with a log-rank test (SYNTHETIC).

Episodes still on the list at the extract date, or removed for non-surgical
reasons, are right-censored (is_admitted = 0). This is the correct way to handle
"not everyone has had their event yet" — a plain mean wait would be biased.
Run:  python analytics/06_waitlist_survival.py
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import matplotlib.pyplot as plt  # noqa: E402
from lifelines import KaplanMeierFitter  # noqa: E402
from lifelines.statistics import multivariate_logrank_test  # noqa: E402

from src import plotting as P  # noqa: E402
from src.data import load_elective  # noqa: E402

COLORS = {1: P.CORAL, 2: P.AMBER, 3: P.TEAL}


def main() -> None:
    df = load_elective()
    df = df[df["urgency_code"].isin([1, 2, 3])].copy()
    df["event"] = df["is_admitted"].astype(int)

    print("=== Kaplan-Meier: elective time-to-admission by urgency ===")
    P.style()
    fig, ax = plt.subplots(figsize=(9, 5.5))
    kmf = KaplanMeierFitter()
    for code in [1, 2, 3]:
        sub = df[df["urgency_code"] == code]
        rec = int(sub["recommended_max_wait_days"].iloc[0])
        kmf.fit(sub["wait_days"], event_observed=sub["event"], label=f"Category {code}")
        kmf.plot_survival_function(ax=ax, color=COLORS[code], ci_alpha=0.12)
        median = kmf.median_survival_time_
        median_txt = "not reached" if median != median or median == float("inf") else f"{median:.0f} days"
        censored = int((sub["event"] == 0).sum())
        print(f"  Cat {code}: median time-to-admission = {median_txt:<12} "
              f"(n={len(sub):,}, censored={censored}, recommended <= {rec}d)")

    res = multivariate_logrank_test(df["wait_days"], df["urgency_code"], df["event"])
    print(f"Log-rank test across categories: p = {res.p_value:.2e} "
          f"({'significant' if res.p_value < 0.05 else 'not significant'} difference in waits)")

    ax.set_xlabel("Days on waitlist")
    ax.set_ylabel("Probability still waiting")
    ax.set_title("Elective surgery time-to-admission by urgency (Kaplan-Meier, SYNTHETIC)")
    ax.legend(title="Urgency")
    print("saved:", P.save(fig, "06_waitlist_survival.png"))


if __name__ == "__main__":
    main()
