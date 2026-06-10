"""Lightweight statistical helpers (no heavy deps) for benchmark inference."""

from __future__ import annotations

import math
from dataclasses import dataclass

Z_95 = 1.959963985


@dataclass
class ProportionTest:
    p_hat: float
    n: int
    p_ref: float
    z: float
    p_value: float
    ci_low: float
    ci_high: float

    @property
    def verdict(self) -> str:
        if self.p_value >= 0.05:
            return "within"
        return "above" if self.p_hat > self.p_ref else "below"


def _norm_sf(x: float) -> float:
    """Upper-tail standard-normal probability via erfc (stdlib)."""
    return 0.5 * math.erfc(x / math.sqrt(2.0))


def one_sample_proportion_test(p_hat: float, n: int, p_ref: float) -> ProportionTest:
    """
    Two-sided z-test of an observed proportion against a reference proportion,
    with a Wald 95% CI for the observed proportion. Used to ask: is this
    hospital's on-time rate significantly different from the pooled rate?
    """
    se_ref = math.sqrt(p_ref * (1 - p_ref) / n)
    z = (p_hat - p_ref) / se_ref if se_ref > 0 else 0.0
    p_value = 2.0 * _norm_sf(abs(z))
    se_hat = math.sqrt(max(p_hat * (1 - p_hat), 1e-12) / n)
    return ProportionTest(
        p_hat=p_hat, n=n, p_ref=p_ref, z=z, p_value=p_value,
        ci_low=max(0.0, p_hat - Z_95 * se_hat),
        ci_high=min(1.0, p_hat + Z_95 * se_hat),
    )
