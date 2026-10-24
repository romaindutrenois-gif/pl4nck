# Model documentation: Black-Scholes (outline, pre-filled)

Structure aligned with SR 11-7 and the ECB guide to internal models. Text in
*italics* is for you to complete with your institution's context.

## 1. Purpose and scope

- Price European options, discretely monitored Asian options and barrier
  options on a single equity or FX underlying; produce Greeks.
- Serve as benchmark and control variate for more complex models (local
  volatility, Heston), and as the reference Monte Carlo engine.
- *Products, desks and decisions that rely on the model; materiality.*

## 2. Theory

- Under the risk-neutral measure, dS = (r - q) S dt + σ S dW with constant r, q, σ.
- European price: C = S e^(-qT) N(d1) - K e^(-rT) N(d2), with
  d1,2 = [ln(S/K) + (r - q ± σ²/2) T] / (σ√T); put by parity.
- Geometric Asian: ln G is normal, giving a closed form used both as a
  benchmark and as a control variate for the arithmetic Asian.
- Barriers: continuous-monitoring closed forms (Reiner-Rubinstein); discrete
  monitoring approximated by the Broadie-Glasserman-Kou barrier shift.

## 3. Assumptions and limitations

| Assumption | Consequence | Mitigation |
|---|---|---|
| Constant volatility | No smile or term structure: barriers, digitals and autocalls are mispriced | Use as benchmark only for smile-sensitive products; compare with local or stochastic volatility |
| Continuous trading, no costs | Hedging P&L understates real costs | *Reserve or adjustment policy* |
| No jumps | Short-dated out-of-the-money options underpriced | Jump models for products where it matters |
| BGK shift is approximate | Small residual bias for discretely monitored barriers | Tolerance of 1% of price in tests; finer monitoring when material |

## 4. Implementation

- Python package `black_scholes` (`src/black_scholes/model.py`), numpy and scipy only.
- Monte Carlo: exact lognormal steps on monitoring dates, antithetic variates
  (pairs counted as one i.i.d. unit), standard error with every price,
  control-variate coefficient estimated on an independent pilot sample.
- Inputs validated at every public function; degenerate cases (σ = 0, T = 0)
  return the analytic limit.
- *Version control, code review and release process.*

## 5. Testing

- See `docs/test_plan.md`: 11 tests with pre-registered criteria, run with `pytest`.
- Independent reference: QuantLib 1.44 values stored in `tests/reference/`;
  the prototype does not import QuantLib (checked by a test).
- *Results of the test run, environment, date, and reviewer.*

## 6. Use, monitoring and controls

- *Where the model is used, input data sources and their controls.*
- Monitoring: re-run the test suite at every change; track the Monte Carlo
  standard error of production prices; compare with market prices where
  available (implied volatility consistency).
- *Thresholds that trigger a review.*

## 7. Model risk and next steps

- Main model risk: volatility smile. Quantify it on your products by comparing
  with a local or stochastic volatility model (see the Heston kit).
- Next no-regret steps: quasi-Monte Carlo (Sobol with Brownian bridge), AAD
  Greeks, GPU Monte Carlo.
- Quantum angle: Monte Carlo pricing is the textbook target of quantum amplitude
  estimation, but a useful advantage needs fault-tolerant hardware (2030s); this
  variance-reduced Monte Carlo is the benchmark a quantum pricer would have to beat.
