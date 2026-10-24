# Test plan: Black-Scholes prototype

Criteria were fixed before the code was written and are not loosened afterwards.
Reference values: `tests/reference/black_scholes_quantlib.json` (QuantLib 1.44:
54 European prices with Greeks, including a negative rate; 18 discrete geometric
Asian calls; 24 continuously monitored barrier calls). Monte Carlo tests use
fixed seeds so every run gives the same result.

| # | Test | What it checks | Acceptance criterion | Implemented in |
|---|---|---|---|---|
| 1 | Closed form against QuantLib | European prices and Greeks (delta, gamma, vega, rho); geometric Asian closed form | Absolute error below 1e-8 on every case | `test_closed_form_prices_against_quantlib`, `test_greeks_against_quantlib`, `test_geometric_asian_closed_form_against_quantlib` |
| 2 | Put-call parity | C - P = S e^(-qT) - K e^(-rT) | Below 1e-10 | `test_put_call_parity` |
| 3 | Monte Carlo against closed forms | European and geometric Asian prices | Within 3 standard errors on every case | `test_mc_european_within_three_standard_errors`, `test_mc_geometric_asian_within_three_standard_errors` |
| 4 | Convergence rate | Standard error from 4,096 to 262,144 paths | Log-log slope -0.5 ± 0.05 | `test_convergence_rate` |
| 5 | Control variate efficiency | Arithmetic Asian with the geometric control, coefficient from a pilot sample | Variance reduction factor reported and above 10 at the money; price consistent with plain Monte Carlo | `test_control_variate_efficiency` |
| 6 | Barrier with discrete monitoring | Monte Carlo with 200 dates and the Broadie-Glasserman-Kou shift against the continuous closed form | Within 3 standard errors plus 1% of price | `test_mc_barrier_with_bgk_shift` |
| 7 | No-arbitrage shape | Call price across strikes 50 to 150 | Strictly decreasing and convex | `test_call_decreasing_and_convex_in_strike` |
| 8 | Limits | σ → 0 and T → 0 | Discounted forward intrinsic to 1e-8; intrinsic at T = 0 | `test_limits` |
| 9 | Seed stability | Price across 10 seeds | Spread between 0.4 and 2 times the reported standard error | `test_seed_stability` |
| 10 | Input checks | Negative spot, zero strike, negative volatility or maturity, unknown option type, non-increasing time grid | ValueError raised | `test_invalid_inputs_raise`, `test_invalid_time_grid_raises` |
| 11 | Independence | The prototype does not import the reference library | No QuantLib import under `src/` | `test_independence.py` |

## Not covered by this plan

- Calibration to market quotes (Black-Scholes has one volatility per option: implied volatility inversion is a separate test).
- Discrete dividends, term structures of rates and volatility.
- Performance targets: depend on your hardware and production constraints.

## Conventions

The conventions module (`src/pl4nck_conventions`) has its own 611 tests in
`tests/conventions/`, against QuantLib reference values. Use it when maturities
come from dates: `year_fraction(trade_date, expiry, "ACT/365F")` reproduces the
time convention of the reference values.
