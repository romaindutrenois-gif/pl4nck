"""Day-count conventions: year fractions between two dates.

Pure Python, no dependency. Every convention is tested against QuantLib
(tests/reference/conventions_quantlib.json).

Names follow ISDA 2006 Section 4.16 where possible:

    ACT/360        Actual/360
    ACT/365F       Actual/365 (Fixed)
    ACT/ACT ISDA   Actual/Actual (ISDA): days in leap years / 366 + others / 365
    30/360         30/360 US bond basis ("Bond Basis", ISDA 4.16(f))
    30E/360        30E/360 Eurobond basis (ISDA 4.16(g))
    30E/360 ISDA   30E/360 (ISDA), ISDA 4.16(h): needs the termination date
"""
from __future__ import annotations

from datetime import date

__all__ = ["year_fraction", "day_count", "CONVENTIONS"]

CONVENTIONS = ("ACT/360", "ACT/365F", "ACT/ACT ISDA", "30/360", "30E/360", "30E/360 ISDA")


def _is_leap(y: int) -> bool:
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def _is_last_of_feb(d: date) -> bool:
    return d.month == 2 and d.day == (29 if _is_leap(d.year) else 28)


def _thirty(y1, m1, d1, y2, m2, d2) -> int:
    return 360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)


def day_count(start: date, end: date, convention: str, termination: date | None = None) -> int:
    """Number of days between start and end under the convention's counting rule."""
    c = convention.upper()
    if c in ("ACT/360", "ACT/365F", "ACT/ACT ISDA"):
        return (end - start).days
    y1, m1, d1, y2, m2, d2 = start.year, start.month, start.day, end.year, end.month, end.day
    if c == "30/360":  # US bond basis
        if d1 == 31:
            d1 = 30
        if d2 == 31 and d1 == 30:
            d2 = 30
    elif c == "30E/360":  # Eurobond basis
        d1, d2 = min(d1, 30), min(d2, 30)
    elif c == "30E/360 ISDA":
        if d1 == 31 or _is_last_of_feb(start):
            d1 = 30
        if d2 == 31 or (_is_last_of_feb(end) and end != termination):
            d2 = 30
    else:
        raise ValueError(f"Unknown convention {convention!r}; choose from {CONVENTIONS}")
    return _thirty(y1, m1, d1, y2, m2, d2)


def year_fraction(start: date, end: date, convention: str, termination: date | None = None) -> float:
    """Year fraction from start to end.

    termination is only used by "30E/360 ISDA" (the end date of the whole
    period, where February end-of-month is not adjusted).
    """
    c = convention.upper()
    if end < start:
        return -year_fraction(end, start, convention, termination)
    if c == "ACT/360":
        return (end - start).days / 360.0
    if c == "ACT/365F":
        return (end - start).days / 365.0
    if c == "ACT/ACT ISDA":
        if start.year == end.year:
            return (end - start).days / (366.0 if _is_leap(start.year) else 365.0)
        first = (date(start.year + 1, 1, 1) - start).days / (366.0 if _is_leap(start.year) else 365.0)
        last = (end - date(end.year, 1, 1)).days / (366.0 if _is_leap(end.year) else 365.0)
        return first + (end.year - start.year - 1) + last
    return day_count(start, end, c, termination) / 360.0
