# Black-Scholes validation kit (v1.0.0)

From the [Veqctor](https://veqctor.com/library#black_scholes) model library.
A prototype, its validation tests with pre-registered criteria, independent
QuantLib reference values and a pre-filled documentation outline. Everything
runs locally; nothing is sent anywhere.

## Contents

| Path | What it is |
|---|---|
| `src/black_scholes/` | Prototype: closed forms (European, Greeks, geometric Asian) and a Monte Carlo pricer (antithetics, geometric-Asian control variate, barriers with the BGK shift) |
| `src/veqctor_conventions/` | Day counts, calendars, adjustments and schedules, tested against QuantLib |
| `tests/test_model.py` | The validation tests listed in `docs/test_plan.docx` |
| `tests/reference/` | QuantLib 1.44 reference values (data only; QuantLib is not needed) |
| `tests/conventions/` | 611 tests of the conventions module |
| `docs/test_plan.docx` | Tests, what they check, acceptance criteria, where each is implemented |
| `docs/model_documentation.docx` | Model documentation aligned with SR 11-7, pre-filled; shaded paragraphs are yours to complete |
| `docs/latex/` | The same two documents in LaTeX, for teams that write in LaTeX |
| `examples/run_example.py` | Prices against benchmarks in one screen |

## Run it

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .[test]
pytest
python examples/run_example.py
```

635 tests (11 for the model, 611 for the conventions module, plus parametrised cases), about 10 seconds on a laptop.

## Adapt it

- Replace the reference cases with your own (same JSON layout) to test your
  production pricer: point the tests at your function instead of `bs_price`.
- Use `veqctor_conventions.year_fraction` when maturities come from dates.
- Next steps on the roadmap: quasi-Monte Carlo, AAD Greeks, then local or
  stochastic volatility (see the Heston kit).

Reviewed and tested by Veqctor before release. Still adapt it to your data,
standards and validation policy before any use.
