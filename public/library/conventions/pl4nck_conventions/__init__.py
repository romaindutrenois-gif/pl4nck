"""pl4nck_conventions: market conventions for pricing and validation code.

Day counts, holiday calendars, business-day adjustment and coupon schedules,
in pure Python and tested against QuantLib. Part of the Pl4nck model library.

    from datetime import date
    from pl4nck_conventions import year_fraction, get_calendar, adjust, make_schedule

    cal = get_calendar("TARGET")
    dates = make_schedule(date(2026, 3, 18), date(2031, 3, 18), 6, cal)
    accruals = [year_fraction(a, b, "30E/360") for a, b in zip(dates, dates[1:])]
"""
from .adjust import add_months, adjust, advance, end_of_month, is_end_of_month
from .calendars import Calendar, JointCalendar, easter, get_calendar
from .daycount import day_count, year_fraction
from .schedule import make_schedule, periods

__version__ = "0.1.0"
__all__ = [
    "year_fraction", "day_count", "get_calendar", "Calendar", "JointCalendar", "easter",
    "adjust", "advance", "add_months", "end_of_month", "is_end_of_month", "make_schedule", "periods",
]
