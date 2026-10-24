"""Black-Scholes: closed forms, Greeks and a Monte Carlo pricer with standard errors.

Conventions: time in years, flat continuously compounded rate r and dividend
(or foreign) yield q, prices per unit of underlying. Vega and rho are per 1%
(0.01 absolute) move; delta and gamma per unit of spot.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import norm

BGK_BETA = 0.5826  # Broadie-Glasserman-Kou constant, -zeta(1/2)/sqrt(2*pi)


# ---------------------------------------------------------------- input checks
def _sign(option: str) -> float:
    if option not in ("call", "put"):
        raise ValueError("option must be 'call' or 'put'")
    return 1.0 if option == "call" else -1.0


def _check(s0, k, vol, t, allow_degenerate=True):
    if not (s0 > 0 and k > 0):
        raise ValueError("spot and strike must be positive")
    if vol < 0 or t < 0:
        raise ValueError("volatility and maturity cannot be negative")
    if not allow_degenerate and (vol == 0 or t == 0):
        raise ValueError("volatility and maturity must be positive here")


def _check_times(times) -> np.ndarray:
    t = np.asarray(times, dtype=float)
    if t.ndim != 1 or t.size == 0 or t[0] <= 0 or np.any(np.diff(t) <= 0):
        raise ValueError("times must be a non-empty, strictly increasing grid of positive times")
    return t


def _d1d2(s0, k, r, q, vol, t):
    sd = vol * np.sqrt(t)
    d1 = (np.log(s0 / k) + (r - q) * t) / sd + 0.5 * sd
    return d1, d1 - sd


# ---------------------------------------------------------------- closed forms
def bs_price(s0, k, r, q, vol, t, option="call") -> float:
    """European price.

    Degenerate cases: vol = 0 or t = 0 return the discounted forward intrinsic
    value max(w (S e^-qT - K e^-rT), 0), which is the limit of the formula.
    """
    w = _sign(option)
    _check(s0, k, vol, t)
    if t == 0 or vol == 0:
        return float(max(w * (s0 * np.exp(-q * t) - k * np.exp(-r * t)), 0.0))
    d1, d2 = _d1d2(s0, k, r, q, vol, t)
    return float(w * (s0 * np.exp(-q * t) * norm.cdf(w * d1) - k * np.exp(-r * t) * norm.cdf(w * d2)))


def bs_greeks(s0, k, r, q, vol, t, option="call") -> dict:
    """Delta and gamma per unit of spot; vega and rho per 1% move. Needs vol > 0 and t > 0."""
    w = _sign(option)
    _check(s0, k, vol, t, allow_degenerate=False)
    d1, d2 = _d1d2(s0, k, r, q, vol, t)
    eq, er = np.exp(-q * t), np.exp(-r * t)
    return {
        "delta": float(w * eq * norm.cdf(w * d1)),
        "gamma": float(eq * norm.pdf(d1) / (s0 * vol * np.sqrt(t))),
        "vega": float(0.01 * s0 * eq * norm.pdf(d1) * np.sqrt(t)),
        "rho": float(0.01 * w * k * t * er * norm.cdf(w * d2)),
    }


def geometric_asian_price(s0, k, r, q, vol, fixing_times, option="call") -> float:
    """Discretely monitored geometric average-price option, in closed form.

    The average runs over the fixing times only (t = 0 excluded); payment at
    the last fixing. ln G is normal with mean ln S + (r - q - vol^2/2) mean(t)
    and variance vol^2 sum_ij min(t_i, t_j) / n^2.
    """
    w = _sign(option)
    t = _check_times(fixing_times)
    _check(s0, k, vol, t[-1], allow_degenerate=False)
    m = np.log(s0) + (r - q - 0.5 * vol**2) * t.mean()
    v = vol**2 * np.minimum.outer(t, t).sum() / t.size**2
    sd = np.sqrt(v)
    d1 = (m + v - np.log(k)) / sd
    return float(np.exp(-r * t[-1]) * w * (np.exp(m + 0.5 * v) * norm.cdf(w * d1) - k * norm.cdf(w * (d1 - sd))))


# ---------------------------------------------------------------- Monte Carlo
def time_grid(t, n_dates) -> np.ndarray:
    """Equally spaced monitoring dates in (0, t]."""
    if t <= 0 or n_dates < 1:
        raise ValueError("t must be positive and n_dates at least 1")
    return np.linspace(t / n_dates, t, n_dates)


def bgk_barrier(barrier, vol, dt, down=True) -> float:
    """Barrier for a discretely monitored Monte Carlo that approximates a continuous one.

    Moves the barrier away from spot: H exp(+0.5826 vol sqrt(dt)) for a down
    barrier, H exp(-0.5826 vol sqrt(dt)) for an up barrier. Approximate: keep a
    tolerance of about 1% of the price on top of the Monte Carlo error.
    """
    return float(barrier * np.exp((1.0 if down else -1.0) * BGK_BETA * vol * np.sqrt(dt)))


@dataclass
class MCResult:
    price: float
    std_error: float
    n_paths: int
    variance_reduction: float  # variance without / with the control variate (1.0 if none)


def _payoff(logs, k, kind, w, barrier):
    s = np.exp(logs)
    if kind == "geometric_asian":
        ref = np.exp(logs.mean(axis=1))
    elif kind == "arithmetic_asian":
        ref = s.mean(axis=1)
    elif kind in ("european", "down_out", "up_out"):
        ref = s[:, -1]
    else:
        raise ValueError(f"unknown kind: {kind}")
    pay = np.maximum(w * (ref - k), 0.0)
    if kind == "down_out":
        pay = pay * (s.min(axis=1) > barrier)
    elif kind == "up_out":
        pay = pay * (s.max(axis=1) < barrier)
    return pay


def mc_price(s0, k, r, q, vol, times, kind="european", option="call", n_paths=100_000, seed=0,
             antithetic=True, control_variate=False, barrier=None, pilot_paths=10_000) -> MCResult:
    """Monte Carlo price with exact lognormal steps on the monitoring dates `times`.

    kind: european, geometric_asian, arithmetic_asian, down_out, up_out.
    Antithetic pairs are averaged and counted as one i.i.d. unit for the
    standard error. The control variate (arithmetic Asian only) is the geometric
    Asian; its coefficient is estimated on an independent pilot sample, so the
    estimator stays unbiased.
    """
    w = _sign(option)
    t = _check_times(times)
    _check(s0, k, vol, t[-1], allow_degenerate=False)
    if control_variate and kind != "arithmetic_asian":
        raise ValueError("control variate is for arithmetic_asian only")
    if kind in ("down_out", "up_out") and (barrier is None or barrier <= 0):
        raise ValueError("a positive barrier is required")
    if n_paths < 2 or (antithetic and n_paths < 4):
        raise ValueError("n_paths too small")

    dt = np.diff(t, prepend=0.0)
    disc = np.exp(-r * t[-1])
    drift = (r - q - 0.5 * vol**2) * dt
    rng = np.random.default_rng(seed)

    def sample(n, kd_list):
        z = rng.standard_normal((n, t.size))
        out = []
        for kd in kd_list:
            pay = lambda zz: disc * _payoff(np.log(s0) + np.cumsum(drift + vol * np.sqrt(dt) * zz, axis=1), k, kd, w, barrier)  # noqa: E731
            y = pay(z)
            out.append(0.5 * (y + pay(-z)) if antithetic else y)
        return out

    n = n_paths // 2 if antithetic else n_paths
    if not control_variate:
        (y,) = sample(n, [kind])
        return MCResult(float(y.mean()), float(y.std(ddof=1) / np.sqrt(n)), 2 * n if antithetic else n, 1.0)

    cv_exact = geometric_asian_price(s0, k, r, q, vol, t, option)
    yp, xp = sample(max(pilot_paths // (2 if antithetic else 1), 2), [kind, "geometric_asian"])
    beta = np.cov(yp, xp)[0, 1] / xp.var(ddof=1)
    y, x = sample(n, [kind, "geometric_asian"])
    adj = y - beta * (x - cv_exact)
    vrf = y.var(ddof=1) / adj.var(ddof=1) if adj.var(ddof=1) > 0 else float("inf")
    return MCResult(float(adj.mean()), float(adj.std(ddof=1) / np.sqrt(n)), 2 * n if antithetic else n, float(vrf))
