"""Classical baseline for a vanilla European call.

Implements the reference the quantum result is judged against (validation-reference-anchored
skill): the Black-Scholes closed form (exact, deterministic) plus a Monte-Carlo cross-check
(stochastic, with a confidence interval). Follows the coding-standards skill: frozen inputs,
fail-loud validation, fixed seed, analytical-vs-stochastic distinction.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.stats import norm


@dataclass(frozen=True)
class CallSpec:
    """Immutable European-call specification."""
    S0: float       # spot
    K: float        # strike
    r: float        # risk-free rate
    sigma: float    # volatility
    T: float        # maturity (years)

    def __post_init__(self) -> None:  # fail loud on ill-posed inputs
        for name in ("S0", "K", "sigma", "T"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive, got {getattr(self, name)}")


def bs_call(spec: CallSpec) -> float:
    """Black-Scholes closed form. EXACT — no confidence interval (analytical method)."""
    d1 = (np.log(spec.S0 / spec.K) + (spec.r + 0.5 * spec.sigma**2) * spec.T) / (spec.sigma * np.sqrt(spec.T))
    d2 = d1 - spec.sigma * np.sqrt(spec.T)
    return spec.S0 * norm.cdf(d1) - spec.K * np.exp(-spec.r * spec.T) * norm.cdf(d2)


def mc_call(spec: CallSpec, n: int = 2_000_000, seed: int = 42) -> tuple[float, float]:
    """Monte-Carlo cross-check with antithetic variates. STOCHASTIC — returns (price, 95% half-width)."""
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(n // 2)
    z = np.concatenate([z, -z])  # antithetic
    drift = (spec.r - 0.5 * spec.sigma**2) * spec.T
    diff = spec.sigma * np.sqrt(spec.T) * z
    ST = spec.S0 * np.exp(drift + diff)
    disc_payoff = np.exp(-spec.r * spec.T) * np.maximum(ST - spec.K, 0.0)
    price = disc_payoff.mean()
    half = 1.96 * disc_payoff.std(ddof=1) / np.sqrt(n)
    return float(price), float(half)


if __name__ == "__main__":
    spec = CallSpec(S0=100, K=110, r=0.05, sigma=0.20, T=1.0)
    ref = bs_call(spec)
    mc, half = mc_call(spec)
    print(f"Black-Scholes (reference, exact): {ref:.6f}")
    print(f"Monte-Carlo cross-check:          {mc:.6f} +/- {half:.6f} (95%)")
    print(f"MC contains BS: {abs(mc - ref) <= half}")
