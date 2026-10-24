"""Validation tests for the Black-Scholes prototype.

Each test implements one row of docs/test_plan.md with its pre-registered
acceptance criterion. Reference values come from tests/reference/
black_scholes_quantlib.json (computed with QuantLib; QuantLib is not needed
here). Monte Carlo tests use fixed seeds, so results are reproducible.
"""
import json
import math
from pathlib import Path

import numpy as np
import pytest

from black_scholes import bgk_barrier, bs_greeks, bs_price, geometric_asian_price, mc_price, time_grid

REF = json.loads((Path(__file__).parent / "reference" / "black_scholes_quantlib.json").read_text())
EURO, ASIAN, BARRIER = REF["european"], REF["geometric_asian"], REF["barrier"]


def args(c):
    return c["s0"], c["k"], c["r"], c["q"], c["vol"]


# 1. Closed form against QuantLib: prices and Greeks, absolute error below 1e-8
def test_closed_form_prices_against_quantlib():
    worst = max(abs(bs_price(*args(c), c["t"], c["type"]) - c["price"]) for c in EURO)
    assert worst < 1e-8, f"worst price error {worst:.2e}"


@pytest.mark.parametrize("greek", ["delta", "gamma", "vega", "rho"])
def test_greeks_against_quantlib(greek):
    worst = max(abs(bs_greeks(*args(c), c["t"], c["type"])[greek] - c[greek]) for c in EURO)
    assert worst < 1e-8, f"worst {greek} error {worst:.2e}"


def test_geometric_asian_closed_form_against_quantlib():
    worst = max(abs(geometric_asian_price(*args(c), c["fixing_times"], c["type"]) - c["price"]) for c in ASIAN)
    assert worst < 1e-8, f"worst error {worst:.2e}"


# 2. Put-call parity: C - P = S e^-qT - K e^-rT, below 1e-10
def test_put_call_parity():
    worst = 0.0
    for c in EURO:
        s0, k, r, q, vol = args(c)
        t = c["t"]
        lhs = bs_price(s0, k, r, q, vol, t, "call") - bs_price(s0, k, r, q, vol, t, "put")
        worst = max(worst, abs(lhs - (s0 * math.exp(-q * t) - k * math.exp(-r * t))))
    assert worst < 1e-10, f"worst parity gap {worst:.2e}"


# 3. Monte Carlo against closed forms: within 3 standard errors
def test_mc_european_within_three_standard_errors():
    worst = 0.0
    for i, c in enumerate(EURO):
        m = mc_price(*args(c), [c["t"]], "european", c["type"], n_paths=40_000, seed=100 + i)
        worst = max(worst, abs(m.price - c["price"]) / m.std_error)
    assert worst < 3.0, f"worst deviation {worst:.2f} standard errors"


def test_mc_geometric_asian_within_three_standard_errors():
    worst = 0.0
    for i, c in enumerate(ASIAN):
        m = mc_price(*args(c), c["fixing_times"], "geometric_asian", c["type"], n_paths=40_000, seed=200 + i)
        worst = max(worst, abs(m.price - c["price"]) / m.std_error)
    assert worst < 3.0, f"worst deviation {worst:.2f} standard errors"


# 4. Convergence rate: log-log slope of the standard error, -0.5 +/- 0.05
def test_convergence_rate():
    ns = [2**p for p in range(12, 19)]
    se = [mc_price(100, 100, 0.03, 0.0, 0.2, [1.0], n_paths=n, seed=7).std_error for n in ns]
    slope = np.polyfit(np.log(ns), np.log(se), 1)[0]
    assert abs(slope + 0.5) < 0.05, f"slope {slope:.3f}"


# 5. Control variate efficiency: reported, above 10 at the money
def test_control_variate_efficiency():
    times = time_grid(1.0, 12)
    m = mc_price(100, 100, 0.03, 0.0, 0.2, times, "arithmetic_asian", n_paths=40_000, seed=11, control_variate=True)
    plain = mc_price(100, 100, 0.03, 0.0, 0.2, times, "arithmetic_asian", n_paths=40_000, seed=12)
    print(f"variance reduction factor: {m.variance_reduction:.0f}")
    assert m.variance_reduction > 10
    assert abs(m.price - plain.price) < 3 * math.hypot(m.std_error, plain.std_error)


# 6. Barriers with discrete monitoring and the BGK shift: within 3 SE + 1% of price
def test_mc_barrier_with_bgk_shift():
    failures = []
    for i, c in enumerate(BARRIER):
        steps = 200
        down = c["barrier_type"].startswith("down")
        h = bgk_barrier(c["barrier"], c["vol"], c["t"] / steps, down)
        m = mc_price(*args(c), time_grid(c["t"], steps), "down_out" if down else "up_out", c["type"],
                     n_paths=40_000, seed=300 + i, barrier=h)
        if abs(m.price - c["price"]) > 3 * m.std_error + 0.01 * c["price"]:
            failures.append((c["barrier_type"], c["k"], c["t"], round(m.price, 4), round(c["price"], 4)))
    assert not failures, failures


# 7. No-arbitrage shape: call price decreasing and convex in strike
def test_call_decreasing_and_convex_in_strike():
    strikes = np.linspace(50, 150, 101)
    prices = np.array([bs_price(100, k, 0.03, 0.01, 0.25, 2.0) for k in strikes])
    assert np.all(np.diff(prices) < 0)
    assert np.all(np.diff(prices, 2) > -1e-12)


# 8. Limits: vol -> 0 gives the discounted forward intrinsic; t -> 0 gives intrinsic
@pytest.mark.parametrize("k", [80, 100, 120])
def test_limits(k):
    s0, r, q, t = 100, 0.03, 0.01, 1.5
    fwd_intrinsic = max(s0 * math.exp(-q * t) - k * math.exp(-r * t), 0.0)
    assert abs(bs_price(s0, k, r, q, 1e-9, t) - fwd_intrinsic) < 1e-8
    assert abs(bs_price(s0, k, r, q, 0.0, t) - fwd_intrinsic) < 1e-12
    assert abs(bs_price(s0, k, r, q, 0.2, 1e-12) - max(s0 - k, 0.0)) < 1e-4
    assert bs_price(s0, k, r, q, 0.2, 0.0) == max(s0 - k, 0.0)


# 9. Seed stability: the spread across 10 seeds matches the reported standard error
def test_seed_stability():
    runs = [mc_price(100, 105, 0.03, 0.0, 0.2, [1.0], n_paths=20_000, seed=s) for s in range(10)]
    spread = np.std([m.price for m in runs], ddof=1)
    se = np.mean([m.std_error for m in runs])
    assert 0.4 < spread / se < 2.0, f"spread {spread:.4f} vs standard error {se:.4f}"


# Input checks
@pytest.mark.parametrize("bad", [
    dict(s0=-1), dict(k=0), dict(vol=-0.1), dict(t=-1), dict(option="digital"),
])
def test_invalid_inputs_raise(bad):
    kw = dict(s0=100, k=100, r=0.03, q=0.0, vol=0.2, t=1.0, option="call") | bad
    with pytest.raises(ValueError):
        bs_price(**kw)


def test_invalid_time_grid_raises():
    with pytest.raises(ValueError):
        mc_price(100, 100, 0.03, 0.0, 0.2, [0.5, 0.25])
