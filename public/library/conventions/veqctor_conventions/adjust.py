"""Business-day adjustment and date arithmetic.

    F     Following
    MF    Modified Following (default for most swaps and deposits)
    P     Preceding
    MP    Modified Preceding
    U     Unadjusted
"""
from __future__ import annotations

import calendar as _cal
from datetime import date, timedelta

from .calendars import Calendar

__all__ = ["adjust", "add_months", "advance", "is_end_of_month", "end_of_month", "CONVENTIONS"]

CONVENTIONS = ("F", "MF", "P", "MP", "U")


def end_of_month(d: date) -> date:
    return date(d.year, d.month, _cal.monthrange(d.year, d.month)[1])


def is_end_of_month(d: date) -> bool:
    return d == end_of_month(d)


def adjust(d: date, cal: Calendar, convention: str = "MF") -> date:
    """Move d to a business day according to the convention."""
    c = convention.upper()
    if c == "U" or cal.is_business_day(d):
        return d
    if c in ("F", "MF"):
        x = d
        while cal.is_holiday(x):
            x += timedelta(days=1)
        if c == "MF" and x.month != d.month:
            return adjust(d, cal, "P")
        return x
    if c in ("P", "MP"):
        x = d
        while cal.is_holiday(x):
            x -= timedelta(days=1)
        if c == "MP" and x.month != d.month:
            return adjust(d, cal, "F")
        return x
    raise ValueError(f"Unknown convention {convention!r}; choose from {CONVENTIONS}")


def add_months(d: date, n: int, end_of_month_rule: bool = False) -> date:
    """Calendar month arithmetic, clipping to the month's last day.

    With end_of_month_rule, a month-end start date stays on month ends.
    """
    m = d.month - 1 + n
    y, m = d.year + m // 12, m % 12 + 1
    last = _cal.monthrange(y, m)[1]
    if end_of_month_rule and is_end_of_month(d):
        return date(y, m, last)
    return date(y, m, min(d.day, last))


def advance(d: date, n: int, unit: str, cal: Calendar, convention: str = "F", end_of_month_rule: bool = False) -> date:
    """Advance d by n units ('D' business days, 'W', 'M', 'Y') then adjust.

    Business days ('D') count only business days, as for spot lags (T+2).
    """
    u = unit.upper()
    if u == "D":
        x = d
        if n == 0:
            return adjust(x, cal, convention)
        step = 1 if n > 0 else -1
        for _ in range(abs(n)):
            x += timedelta(days=step)
            while cal.is_holiday(x):
                x += timedelta(days=step)
        return x
    if u == "W":
        return adjust(d + timedelta(weeks=n), cal, convention)
    if u in ("M", "Y"):
        months = n if u == "M" else 12 * n
        # QuantLib's rule: d is 'end of month' if the next business day is in another month
        eom = end_of_month_rule and adjust(d + timedelta(days=1), cal, "F").month != d.month
        x = add_months(d, months)
        if eom:
            return _last_business_day(x, cal)
        return adjust(x, cal, convention)
    raise ValueError("unit must be one of 'D', 'W', 'M', 'Y'")


def _last_business_day(d: date, cal: Calendar) -> date:
    return adjust(end_of_month(d), cal, "P")
