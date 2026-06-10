"""
Hospital peer-group discovery — k-means on standardised KPI profiles.

Clusters Victorian hospitals on their mean ED KPI vector (volume, wait, Cat 2/3
on-time, 4-hour rule, YoY growth), then compares the data-driven clusters to the
AIHW peer groups. Uses the real Gold scorecard.

Run:  python analytics/03_hospital_clustering.py
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import matplotlib.pyplot as plt  # noqa: E402
from sklearn.cluster import KMeans  # noqa: E402
from sklearn.decomposition import PCA  # noqa: E402
from sklearn.metrics import silhouette_score  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from src import plotting as P  # noqa: E402
from src.data import load_scorecard  # noqa: E402

K = 3


def main() -> None:
    sc = load_scorecard()
    vic = sc[sc["state_code"] == "VIC"]
    feat = (vic.groupby(["hospital_name", "peer_group"])
            .agg(presentations=("total_ed_presentations", "mean"),
                 wait=("median_ed_wait_all_triage", "mean"),
                 cat2=("pct_ed_seen_on_time_cat2", "mean"),
                 cat3=("pct_ed_seen_on_time_cat3", "mean"),
                 four_hr=("four_hour_rule_pct", "mean"),
                 growth=("yoy_ed_presentations_growth_pct", "mean"))
            .dropna()
            .reset_index())

    X = StandardScaler().fit_transform(
        feat[["presentations", "wait", "cat2", "cat3", "four_hr", "growth"]].values)
    km = KMeans(n_clusters=K, n_init=10, random_state=42).fit(X)
    feat["cluster"] = km.labels_
    sil = silhouette_score(X, km.labels_)
    print(f"k={K} clusters over {len(feat)} VIC hospitals | silhouette = {sil:.2f}\n")
    for c in sorted(feat["cluster"].unique()):
        members = feat.loc[feat["cluster"] == c, "hospital_name"].tolist()
        peers = feat.loc[feat["cluster"] == c, "peer_group"].unique().tolist()
        print(f"Cluster {c}: {', '.join(members)}")
        print(f"           peer groups: {', '.join(peers)}")

    xy = PCA(n_components=2, random_state=42).fit_transform(X)
    P.style()
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = [P.TEAL, P.AMBER, P.CORAL]
    for c in sorted(feat["cluster"].unique()):
        m = feat["cluster"] == c
        ax.scatter(xy[m, 0], xy[m, 1], s=120, color=colors[c % 3], label=f"Cluster {c}",
                   edgecolor="white", zorder=3)
    for i, name in enumerate(feat["hospital_name"]):
        ax.annotate(name, (xy[i, 0], xy[i, 1]), fontsize=7, xytext=(4, 4),
                    textcoords="offset points")
    ax.set_title("Hospital peer-group discovery — k-means (PCA projection)")
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.legend()
    print("\nsaved:", P.save(fig, "03_hospital_clustering.png"))


if __name__ == "__main__":
    main()
