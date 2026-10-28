"""Coupon schedules, following QuantLib's Schedule for regular periods.

    make_schedule(date(2026, 3, 18), date(2031, 3, 18), tenor_months=6,
                  calendar=get_calendar("TARGET"), convention="MF",
                  rule="backward")

Rules:
    backward  generate from the termination date (swaps, most bonds): a short
              first period (stub) if the dates do not divide evenly
    forward   generate from the effective date: a short last period instead

The termination date is unadjusted by default (ISDA); set
termination_convention to adjust it. With end_of_month=True, a schedule
anchored on a month end stays on (business) month ends.
"""
from __future__ import annotations

from datetime import date, timedelta

from .adjust import add_months, adjust
from .adjust import end_of_month as _end_of_month
from .calendars import Calendar

__all__ = ["make_schedule", "periods"]


def _cal_is_end_of_month(d: date, cal: Calendar) -> bool:
    return adjust(d + timedelta(days=1), cal, "F").month != d.month


def make_schedule(
    effective: date,
    termination: date,
    tenor_months: int,
    calendar: Calendar,
    convention: str = "MF",
    termination_convention: str = "U",
    rule: str = "backward",
    end_of_month: bool = False,
) -> list[date]:
    """Adjusted schedule dates, from effective to termination included."""
    if termination <= effective:
        raise ValueError("termination must be after effective")
    if tenor_months <= 0:
        raise ValueError("tenor_months must be positive")
    rule = rule.lower()
    eom = end_of_month
    same = lambda x, y: adjust(x, calendar, convention) == adjust(y, calendar, convention)  # noqa: E731
    if rule == "backward":
        seed, dates, n = termination, [termination], 1
        while True:
            t = add_months(seed, -n * tenor_months, eom)
            if t < effective:
                break
            if not same(dates[-1], t):
                dates.append(t)
            n += 1
        if not same(dates[-1], effective):
            dates.append(effective)
        dates.reverse()
    elif rule == "forward":
        seed, dates, n = effective, [effective], 1
        while True:
            t = add_months(seed, n * tenor_months, eom)
            if t > termination:
                break
            if not same(dates[-1], t):
                dates.append(t)
            n += 1
        if adjust(dates[-1], calendar, termination_convention) != adjust(termination, calendar, termination_convention):
            dates.append(termination)
    else:
        raise ValueError("rule must be 'backward' or 'forward'")

    # Adjustments (QuantLib 1.4x logic): first date with the convention, last date
    # with the termination convention, inner dates on business month ends if the
    # end-of-month rule applies to the seed date.
    dates[0] = adjust(dates[0], calendar, convention)
    dates[-1] = adjust(dates[-1], calendar, termination_convention)
    on_month_end = eom and _cal_is_end_of_month(seed, calendar)
    for i in range(1, len(dates) - 1):
        dates[i] = adjust(_end_of_month(dates[i]) if on_month_end else dates[i], calendar, convention)

    # Remove a next-to-last date pushed onto or past the end by adjustment
    if len(dates) >= 2 and dates[-2] >= dates[-1]:
        dates[-2] = dates[-1]
        dates.pop()
    if len(dates) >= 2 and dates[1] <= dates[0]:
        del dates[1]
    return dates


def periods(dates: list[date]) -> list[tuple[date, date]]:
    """Consecutive (start, end) accrual periods of a schedule."""
    return list(zip(dates[:-1], dates[1:]))
