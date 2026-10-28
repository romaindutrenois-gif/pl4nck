# veqctor_conventions

Market conventions for pricing and validation code, in pure Python: day counts,
holiday calendars, business-day adjustment, date arithmetic and coupon schedules.
Part of the [Veqctor](https://github.com/romaindutrenois-gif/pl4nck) model library.

Conventions are the part of a model that everyone assumes and nobody tests, until
cash flows land on the wrong day. This module makes them explicit and checks them.

## What is inside

| Module | Covers |
|---|---|
| `daycount` | ACT/360, ACT/365F, ACT/ACT ISDA, 30/360 (bond basis), 30E/360, 30E/360 ISDA |
| `calendars` | TARGET, France, United Kingdom, United States (settlement), joint calendars (`"TARGET+UK"`) |
| `adjust` | Following, Modified Following, Preceding, Modified Preceding, Unadjusted; spot lags (`advance(d, 2, "D", cal)`), month and year tenors with the end-of-month rule |
| `schedule` | Coupon schedules, backward and forward generation, end-of-month rule |

```python
from datetime import date
from veqctor_conventions import year_fraction, get_calendar, adjust, advance, make_schedule

target = get_calendar("TARGET")
spot = advance(date(2026, 4, 2), 2, "D", target)            # T+2 over Easter: 2026-04-08
dates = make_schedule(date(2026, 3, 18), date(2031, 3, 18), 6, target, "MF")
accruals = [year_fraction(a, b, "30E/360") for a, b in zip(dates, dates[1:])]
```

## How it is tested

`tests/reference/conventions_quantlib.json` holds values computed with QuantLib
(version recorded in the file): about 4,200 year fractions, every holiday from 2000 to
2050 for each calendar, 500 adjustments, 400 date advances and 85 schedules.
The tests compare against these stored values, so **QuantLib is not needed** to run them.

```bash
pip install pytest
pytest tests
```

## Known limits

- Calendars cover the rules in force; one-off holidays (royal events, national mourning)
  are only known once announced. Check each calendar yearly against an official source.
- **QuantLib's France settlement calendar (1.44) is wrong on two holidays:** it places
  Ascension on May 10 and Whit Monday on May 21 every year, while both move with Easter.
  This module uses the correct dates, and the reference file documents the correction.
- Schedules cover regular backward and forward generation. Explicit stubs (first date,
  next-to-last date), IMM and CDS rules are not implemented.
- Not covered yet: ACT/ACT ICMA (needs reference periods), Business/252, other calendars.

Draft, not reviewed for your institution: check it against your conventions and
validation policy before use.
