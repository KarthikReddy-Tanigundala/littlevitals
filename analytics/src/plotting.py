"""Matplotlib styling + figure saving for the analytics layer (Agg backend)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: render to file, never to a display
import matplotlib.pyplot as plt  # noqa: E402

TEAL = "#1a6b5e"
GREY = "#8a9a97"
CORAL = "#d1495b"
AMBER = "#e0a32e"

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs"


def style() -> None:
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#cfd8d5",
        "axes.grid": True,
        "grid.color": "#eef2f1",
        "font.size": 10,
        "axes.titleweight": "bold",
    })


def save(fig, name: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / name
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path
