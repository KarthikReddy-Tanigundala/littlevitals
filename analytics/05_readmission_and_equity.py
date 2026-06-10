"""
30-day readmission risk + socio-economic equity (SYNTHETIC / Synthea).

(a) Readmission model: logistic regression predicting whether an index encounter
    is followed by a readmission within 30 days, from age, length of stay,
    encounter class and SEIFA quintile. Reports a held-out ROC-AUC and the
    standardised coefficients (interpretability).
(b) Equity: 30-day readmission rate by SEIFA-IRSD quintile, with a linear trend
    test (is disadvantage associated with higher readmission?).

SYNTHETIC data: the generator encodes plausible risk relationships to demonstrate
the methodology — not real Victorian epidemiology. No causal claims.
Run:  python analytics/05_readmission_and_equity.py
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from scipy import stats  # noqa: E402
from sklearn.compose import ColumnTransformer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import roc_auc_score, roc_curve  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import OneHotEncoder, StandardScaler  # noqa: E402

from src import plotting as P  # noqa: E402
from src.data import load_encounters  # noqa: E402

NUMERIC = ["age_years", "los_hours", "seifa_irsd_quintile"]
CATEGORICAL = ["encounter_class"]
TARGET = "had_readmission_30d"


def readmission_model(df) -> None:
    X = df[NUMERIC + CATEGORICAL]
    y = df[TARGET].astype(int)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y)

    pre = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
    ])
    model = Pipeline([
        ("pre", pre),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ]).fit(X_tr, y_tr)

    proba = model.predict_proba(X_te)[:, 1]
    auc = roc_auc_score(y_te, proba)
    print("=== Readmission model (logistic regression) ===")
    print(f"Test ROC-AUC = {auc:.3f}   (positives: {y.mean():.1%} of {len(y):,} encounters)")

    names = model.named_steps["pre"].get_feature_names_out()
    coefs = model.named_steps["clf"].coef_[0]
    print("Standardised coefficients (positive = higher readmission odds):")
    for n, c in sorted(zip(names, coefs), key=lambda t: -abs(t[1])):
        print(f"  {n:<28} {c:+.3f}")

    fpr, tpr, _ = roc_curve(y_te, proba)
    P.style()
    fig, ax = plt.subplots(figsize=(6, 5.5))
    ax.plot(fpr, tpr, color=P.TEAL, lw=2, label=f"Model (AUC = {auc:.2f})")
    ax.plot([0, 1], [0, 1], color=P.GREY, ls="--", lw=1, label="Chance")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title("30-day readmission — ROC (SYNTHETIC)")
    ax.legend(loc="lower right")
    print("saved:", P.save(fig, "05_readmission_roc.png"))


def equity_analysis(df) -> None:
    print("\n=== Equity: readmission by SEIFA IRSD quintile ===")
    grp = (df.groupby("seifa_irsd_quintile")[TARGET]
           .agg(rate="mean", n="size").reset_index())
    for _, r in grp.iterrows():
        print(f"  quintile {int(r['seifa_irsd_quintile'])} "
              f"(1=most disadvantaged): rate={r['rate']:.1%}  n={int(r['n']):,}")

    lr = stats.linregress(grp["seifa_irsd_quintile"], grp["rate"])
    direction = "lower" if lr.slope < 0 else "higher"
    print(f"Linear trend: slope = {lr.slope:+.4f}/quintile, p = {lr.pvalue:.3f} "
          f"=> {direction} readmission as advantage increases"
          + ("" if lr.pvalue < 0.05 else " (not significant)"))

    P.style()
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.bar(grp["seifa_irsd_quintile"], grp["rate"] * 100, color=P.TEAL, width=0.6)
    xs = np.array(grp["seifa_irsd_quintile"])
    ax.plot(xs, (lr.intercept + lr.slope * xs) * 100, color=P.CORAL, lw=2, label="Trend")
    ax.set_xlabel("SEIFA IRSD quintile (1 = most disadvantaged → 5 = least)")
    ax.set_ylabel("30-day readmission rate (%)")
    ax.set_title("Readmission rate by socio-economic disadvantage (SYNTHETIC)")
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.legend()
    print("saved:", P.save(fig, "05_equity_seifa.png"))


def main() -> None:
    df = load_encounters()
    readmission_model(df)
    equity_analysis(df)


if __name__ == "__main__":
    main()
