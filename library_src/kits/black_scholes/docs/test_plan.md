---
title: "Test plan: Black-Scholes prototype"
subtitle: "Pl4nck validation kit v1.0.0"
---

Criteria were fixed before the code was written and are not loosened afterwards. Reference values
are in `tests/reference/black_scholes_quantlib.json` (QuantLib 1.44): 54 European prices with Greeks,
including a negative rate; 18 discrete geometric Asian calls; 24 continuously monitored barrier
calls. Monte Carlo tests use fixed seeds, so every run gives the same result.

# Tests and acceptance criteria

| # | Test | What it checks | Acceptance criterion |
|--|---------|--------------|------------|
| 1 | Closed form against QuantLib | European prices and Greeks (delta, gamma, vega, rho); geometric Asian closed form | Absolute error below $10^{-8}$ on every case |
| 2 | Put-call parity | $C - P = S_0 e^{-qT} - K e^{-rT}$ | Below $10^{-10}$ |
| 3 | Monte Carlo against closed forms | European and geometric Asian prices | Within 3 standard errors on every case |
| 4 | Convergence rate | Standard error from 4,096 to 262,144 paths | Log-log slope $-0.5 \pm 0.05$ |
| 5 | Control variate efficiency | Arithmetic Asian with the geometric control, coefficient from a pilot sample | Variance reduction factor above 10 at the money; price consistent with plain Monte Carlo |
| 6 | Barrier with discrete monitoring | 200 monitoring dates with the BGK shift against the continuous closed form | Within 3 standard errors plus 1% of price |
| 7 | No-arbitrage shape | Call price for strikes 50 to 150 | Strictly decreasing and convex |
| 8 | Limits | $\sigma \to 0$ and $T \to 0$ | Discounted forward intrinsic to $10^{-8}$; intrinsic at $T = 0$ |
| 9 | Seed stability | Price across 10 seeds | Spread between 0.4 and 2 times the reported standard error |
| 10 | Input checks | Negative spot, zero strike, negative volatility or maturity, unknown option type, non-increasing time grid | `ValueError` raised |
| 11 | Independence | The prototype does not import the reference library | No QuantLib import under `src/` |

# Where each test is implemented

| # | pytest function |
|--|---------------------------------|
| 1 | `test_closed_form_prices_against_quantlib`, `test_greeks_against_quantlib`, `test_geometric_asian_closed_form_against_quantlib` |
| 2 | `test_put_call_parity` |
| 3 | `test_mc_european_within_three_standard_errors`, `test_mc_geometric_asian_within_three_standard_errors` |
| 4 | `test_convergence_rate` |
| 5 | `test_control_variate_efficiency` |
| 6 | `test_mc_barrier_with_bgk_shift` |
| 7 | `test_call_decreasing_and_convex_in_strike` |
| 8 | `test_limits` |
| 9 | `test_seed_stability` |
| 10 | `test_invalid_inputs_raise`, `test_invalid_time_grid_raises` |
| 11 | `test_prototype_does_not_import_quantlib` (in `tests/test_independence.py`) |

# Not covered by this plan

- Calibration to market quotes: implied-volatility inversion is a separate test.
- Discrete dividends, term structures of rates and volatility.
- Performance targets, which depend on your hardware and production constraints.

::: complete
Additional tests required by your validation policy, and the tolerance your institution applies to
each criterion if it differs.
:::

# Conventions

The conventions module (`src/pl4nck_conventions`) has its own 611 tests in `tests/conventions/`,
against QuantLib reference values. When maturities come from dates, `year_fraction(trade_date,
expiry, "ACT/365F")` reproduces the time convention of the reference values.
