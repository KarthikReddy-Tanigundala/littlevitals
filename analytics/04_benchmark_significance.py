"""
Benchmark significance — is each hospital's Cat 2 on-time rate significantly
different from the Victorian pooled rate? Two-sided proportion z-test with 95%
CIs, plus a funnel plot flagging special-cause outliers (the fair alternative to
a league table). Uses the real Gold fact.

Run:  python analytics/04_benchmark_significance.py
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from src import plotting as P  # noqa: E402
from src.data import load_fact  # noqa: E402
from src.funnel import Z_95, Z_998, control_limit, flag_outliers, pooled_mean  # noqa: E402
from src.stats_tests import one_sample_proportion_test  # noqa: E402


def main() -> None:
    fact = load_fact()
    fy = fact["financial_year"].max()
    cat2 = fact[(fact["state_code"] == "VIC") & (fact["triage_code"] == 2)
                & (fact["financial_year"] == fy)].copy()
    cat2 = cat2.rename(columns={"total_presentations": "n", "pct_seen_on_time": "p"})

    p_bar = pooled_mean(cat2, "p", "n")
    print(f"FY {fy} | VIC pooled Cat 2 on-time = {p_bar:.1%}\n")
    print(f"{'Hospital':<34}{'on-time':>8}{'n':>8}{'95% CI':>16}{'p-value':>9}  verdict")
    print("-" * 84)
    for _, r in cat2.sort_values("p", ascending=False).iterrows():
        t = one_sample_proportion_test(float(r["p"]), int(r["n"]), p_bar)
        print(f"{r['hospital_name']:<34}{r['p']:>7.1%}{int(r['n']):>8,}"
              f"{f'[{t.ci_low:.0%}, {t.ci_high:.0%}]':>16}{t.p_value:>9.3f}  {t.verdict}")

    # ---- Funnel plot ----
    _, outlier = flag_outliers(cat2, "p", "n")
    n_grid = np.linspace(cat2["n"].min() * 0.7, cat2["n"].max() * 1.1, 200)
    P.style()
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for z, ls, lbl in [(Z_95, ":", "95% limit"), (Z_998, "--", "99.8% limit")]:
        ax.plot(n_grid, control_limit(p_bar, n_grid, z), color=P.GREY, ls=ls, lw=1, label=lbl)
        ax.plot(n_grid, control_limit(p_bar, n_grid, -z), color=P.GREY, ls=ls, lw=1)
    ax.axhline(p_bar, color=P.TEAL, lw=2, label=f"Pooled mean ({p_bar:.0%})")
    ax.scatter(cat2["n"], cat2["p"], s=90,
               color=np.where(outlier, P.CORAL, P.TEAL), edgecolor="white", zorder=3)
    for _, r in cat2[outlier].iterrows():
        ax.annotate(r["hospital_name"], (r["n"], r["p"]), fontsize=8,
                    xytext=(4, 4), textcoords="offset points")
    ax.set_title(f"Funnel plot — Cat 2 ED on-time, VIC {fy}")
    ax.set_xlabel("ED presentations (Cat 2) — volume")
    ax.set_ylabel("Seen on time")
    ax.legend(fontsize=8)
    print("\nspecial-cause outliers:", cat2.loc[outlier, "hospital_name"].tolist() or "none")
    print("saved:", P.save(fig, "04_benchmark_funnel.png"))


if __name__ == "__main__":
    main()
