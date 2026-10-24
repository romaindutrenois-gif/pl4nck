---
title: "Model documentation: Black-Scholes"
subtitle: "Pre-filled outline aligned with SR 11-7 and the ECB guide to internal models · Pl4nck validation kit v1.0.0"
---

Shaded paragraphs marked *To complete* are for your institution's context. Everything else
describes the prototype delivered in this kit and can be kept, edited or removed.

# Purpose and scope

The prototype prices European options, discretely monitored Asian options and barrier options on a
single equity or FX underlying, and produces first-order Greeks. It also serves as the benchmark and
control variate for richer models (local volatility, Heston) and as the reference Monte Carlo engine.

::: complete
Products, desks and decisions that rely on the model; materiality of the exposures priced; model
owner and users.
:::

# Theory

Under the risk-neutral measure the underlying follows a geometric Brownian motion with constant
rate $r$, dividend (or foreign) yield $q$ and volatility $\sigma$:

$$dS_t = (r - q)\,S_t\,dt + \sigma\,S_t\,dW_t .$$

The European call and put prices are

$$C = S_0 e^{-qT} N(d_1) - K e^{-rT} N(d_2), \qquad P = K e^{-rT} N(-d_2) - S_0 e^{-qT} N(-d_1),$$

$$d_{1,2} = \frac{\ln(S_0/K) + (r - q \pm \tfrac{1}{2}\sigma^2)\,T}{\sigma\sqrt{T}} .$$

**Geometric Asian option.** For fixing times $t_1 < \dots < t_n$, the log of the geometric average
$G = \left(\prod_i S_{t_i}\right)^{1/n}$ is normal with

$$\mathbb{E}[\ln G] = \ln S_0 + \left(r - q - \tfrac{1}{2}\sigma^2\right)\bar t, \qquad
\operatorname{Var}[\ln G] = \frac{\sigma^2}{n^2}\sum_{i,j}\min(t_i, t_j),$$

which gives a closed form used both as a benchmark and as a control variate for the arithmetic Asian.

**Barrier options.** Continuously monitored barriers have closed forms (Reiner-Rubinstein). A
Monte Carlo with $m$ monitoring dates of step $\Delta t$ approximates them by moving the barrier
away from the spot (Broadie, Glasserman and Kou, 1997):

$$H' = H\,e^{\pm\beta\sigma\sqrt{\Delta t}}, \qquad \beta = -\zeta(\tfrac{1}{2})/\sqrt{2\pi} \approx 0.5826,$$

with the plus sign for a down barrier and the minus sign for an up barrier.

# Assumptions and limitations

| Assumption | Consequence | Mitigation |
|---|---|---|
| Constant volatility | No smile or term structure: barriers, digitals and autocalls are mispriced | Use as a benchmark for smile-sensitive products; compare with local or stochastic volatility |
| Continuous trading, no costs | Hedging P&L understates real costs | Reserve or adjustment policy |
| No jumps | Short-dated out-of-the-money options underpriced | Jump models where it matters |
| BGK shift is approximate | Small residual bias for discretely monitored barriers | Tolerance of 1% of price in tests; finer monitoring when material |

::: complete
Your reserve and adjustment policies for these limitations, and the products for which the model is
not approved.
:::

# Implementation

- Python package `black_scholes` (`src/black_scholes/model.py`), depending only on numpy and scipy.
- Monte Carlo with exact lognormal steps on the monitoring dates; antithetic variates, each pair
  counted as one independent unit; a standard error reported with every price.
- Control variate for the arithmetic Asian: the geometric Asian, with its coefficient estimated on
  an independent pilot sample so that the estimator stays unbiased.
- Inputs validated at every public function; degenerate cases ($\sigma = 0$, $T = 0$) return the
  analytic limit.
- Conventions (day counts, calendars, schedules) from `pl4nck_conventions`, tested separately.

::: complete
Version control, code review and release process; production platform and its differences from
this prototype.
:::

# Testing

The test plan (`test_plan.docx`) lists 11 tests with criteria fixed before the code was written. The
reference values are independent: they were computed with QuantLib 1.44 and stored in
`tests/reference/`, and a test checks that the prototype does not import QuantLib.

| Area | Result in the release build |
|-------------|--------|
| Closed forms and Greeks against QuantLib (54 cases) | Maximum absolute error below $10^{-13}$ |
| Monte Carlo against closed forms (72 cases) | All within 3 standard errors |
| Barriers with BGK shift (24 cases) | All within 3 standard errors plus 1% of price |
| Convergence, limits, seeds, inputs | All passed |

::: complete
Results of your own run: environment, date, reviewer, and any deviation from the criteria.
:::

# Use, monitoring and controls

- Re-run the full test suite at every change of code, library versions or platform.
- Track the Monte Carlo standard error of production prices against a tolerance.
- Compare model prices with market prices where available (implied-volatility consistency).

::: complete
Input data sources and their controls; monitoring thresholds that trigger a model review; review
frequency.
:::

# Model risk and next steps

The main model risk is the volatility smile. Quantify it on your products by comparing with a local
or stochastic volatility model (see the Heston kit).

No-regret next steps: quasi-Monte Carlo (Sobol sequences with a Brownian bridge), adjoint
algorithmic differentiation for Greeks, GPU Monte Carlo.

Quantum angle: Monte Carlo pricing is the textbook target of quantum amplitude estimation, which
reduces the sample complexity from $O(\varepsilon^{-2})$ to $O(\varepsilon^{-1})$. A useful advantage
needs fault-tolerant hardware, not expected before the 2030s; the variance-reduced Monte Carlo of
this kit is the benchmark a quantum pricer would have to beat.
