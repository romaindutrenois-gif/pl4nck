"""Holiday calendars for settlement.

Pure Python. Each calendar reproduces QuantLib's holiday list for every day
from 2000 to 2050 (tests/reference/conventions_quantlib.json).
One-off holidays (royal events, national mourning) are only known once they
are announced: check the calendar every year against an official source.

    TARGET   Euro area settlement (TARGET2 / T2)
    FR       France, settlement (QuantLib France.Settlement)
    UK       United Kingdom, settlement (QuantLib UnitedKingdom.Settlement)
    US       United States, settlement (QuantLib UnitedStates.Settlement)

Combine calendars with JointCalendar (a day is a holiday if it is one in any).
"""
from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache

__all__ = ["Calendar", "JointCalendar", "get_calendar", "easter", "CALENDARS"]


@lru_cache(maxsize=None)
def easter(year: int) -> date:
    """Gregorian Easter Sunday (Meeus/Jones/Butcher algorithm)."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """n-th given weekday (Mon=0) of a month; n=-1 for the last one."""
    if n > 0:
        d = date(year, month, 1)
        d += timedelta(days=(weekday - d.weekday()) % 7)
        return d + timedelta(weeks=n - 1)
    d = date(year + (month == 12), month % 12 + 1, 1) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - weekday) % 7)


def _observed_us(d: date) -> date:
    """US rule: Saturday holidays move to Friday, Sunday holidays to Monday."""
    if d.weekday() == 5:
        return d - timedelta(days=1)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


class Calendar:
    """Base calendar: weekends are Saturday and Sunday."""

    name = "WeekendsOnly"

    def is_weekend(self, d: date) -> bool:
        return d.weekday() >= 5

    def _holidays(self, year: int) -> frozenset:
        return frozenset()

    @lru_cache(maxsize=None)
    def holidays_in_year(self, year: int) -> frozenset:
        return self._holidays(year)

    def is_holiday(self, d: date) -> bool:
        """True on weekends and public holidays."""
        return self.is_weekend(d) or d in self.holidays_in_year(d.year)

    def is_business_day(self, d: date) -> bool:
        return not self.is_holiday(d)

    def holiday_list(self, start: date, end: date, include_weekends: bool = False) -> list[date]:
        out, d = [], start
        while d <= end:
            if (include_weekends and self.is_holiday(d)) or (not self.is_weekend(d) and self.is_holiday(d)):
                out.append(d)
            d += timedelta(days=1)
        return out

    def business_days_between(self, start: date, end: date) -> int:
        """Business days in (start, end], QuantLib's default counting."""
        n, d = 0, start + timedelta(days=1)
        while d <= end:
            n += self.is_business_day(d)
            d += timedelta(days=1)
        return n

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, Calendar) and other.name == self.name

    def __repr__(self):
        return f"{type(self).__name__}()"


class Target(Calendar):
    name = "TARGET"

    def _holidays(self, y):
        e = easter(y)
        h = {date(y, 1, 1), date(y, 12, 25)}
        if y >= 2000:
            h |= {e - timedelta(days=2), e + timedelta(days=1), date(y, 5, 1), date(y, 12, 26)}
        if y in (1998, 1999, 2001):
            h.add(date(y, 12, 31))
        return frozenset(h)


class France(Calendar):
    name = "FR"

    def _holidays(self, y):
        e = easter(y)
        return frozenset({
            date(y, 1, 1), e + timedelta(days=1), date(y, 5, 1), date(y, 5, 8),
            e + timedelta(days=39), e + timedelta(days=50), date(y, 7, 14),
            date(y, 8, 15), date(y, 11, 1), date(y, 11, 11), date(y, 12, 25),
        })


class UnitedKingdom(Calendar):
    name = "UK"
    _special = {
        date(1999, 12, 31), date(2002, 6, 3), date(2011, 4, 29), date(2012, 6, 5),
        date(2022, 6, 3), date(2022, 9, 19), date(2023, 5, 8),
    }

    def _holidays(self, y):
        e = easter(y)
        h = {e - timedelta(days=2), e + timedelta(days=1)}
        # New Year's Day, moved to Monday if on a weekend
        ny = date(y, 1, 1)
        h.add(ny + timedelta(days=(7 - ny.weekday()) % 7) if ny.weekday() >= 5 else ny)
        # Early May bank holiday: first Monday of May (moved for VE Day 2020)
        h.add(date(2020, 5, 8) if y == 2020 else _nth_weekday(y, 5, 0, 1))
        # Spring bank holiday: last Monday of May (moved for jubilees)
        h.add({2002: date(2002, 6, 4), 2012: date(2012, 6, 4), 2022: date(2022, 6, 2)}.get(y, _nth_weekday(y, 5, 0, -1)))
        # Summer bank holiday: last Monday of August
        h.add(_nth_weekday(y, 8, 0, -1))
        # Christmas and Boxing Day, substitute days when on a weekend
        xmas, boxing = date(y, 12, 25), date(y, 12, 26)
        if xmas.weekday() == 5:      # Sat, Sun -> Mon, Tue
            h |= {date(y, 12, 27), date(y, 12, 28)}
        elif xmas.weekday() == 6:    # Sun, Mon -> Tue for Christmas
            h |= {boxing, date(y, 12, 27)}
        elif xmas.weekday() == 4:    # Fri, Sat -> Mon for Boxing Day
            h |= {xmas, date(y, 12, 28)}
        else:
            h |= {xmas, boxing}
        h |= {d for d in self._special if d.year == y}
        return frozenset(h)


class UnitedStates(Calendar):
    name = "US"

    def _holidays(self, y):
        h = set()
        # New Year's Day: Sunday -> Monday; a Saturday New Year is not moved back to Dec 31
        ny = date(y, 1, 1)
        h.add(ny + timedelta(days=1) if ny.weekday() == 6 else ny)
        # A Saturday New Year of y+1 is observed on Friday Dec 31 of y
        if date(y + 1, 1, 1).weekday() == 5:
            h.add(date(y, 12, 31))
        if y >= 1983:
            h.add(_nth_weekday(y, 1, 0, 3))   # Martin Luther King Jr. Day
        h.add(_nth_weekday(y, 2, 0, 3))       # Washington's Birthday
        h.add(_nth_weekday(y, 5, 0, -1))      # Memorial Day
        if y >= 2022:
            h.add(_observed_us(date(y, 6, 19)))  # Juneteenth
        h.add(_observed_us(date(y, 7, 4)))    # Independence Day
        h.add(_nth_weekday(y, 9, 0, 1))       # Labor Day
        h.add(_nth_weekday(y, 10, 0, 2))      # Columbus Day
        h.add(_observed_us(date(y, 11, 11)))  # Veterans Day
        h.add(_nth_weekday(y, 11, 3, 4))      # Thanksgiving
        h.add(_observed_us(date(y, 12, 25)))  # Christmas
        return frozenset(h)


class JointCalendar(Calendar):
    """Holiday if it is a holiday in any of the given calendars."""

    def __init__(self, *calendars: Calendar):
        self.calendars = calendars
        self.name = "+".join(c.name for c in calendars)

    def is_holiday(self, d: date) -> bool:
        return any(c.is_holiday(d) for c in self.calendars)

    def __repr__(self):
        return f"JointCalendar({', '.join(map(repr, self.calendars))})"


CALENDARS = {c.name: c for c in (Calendar(), Target(), France(), UnitedKingdom(), UnitedStates())}


def get_calendar(name: str) -> Calendar:
    """Calendar by name; join several with '+', e.g. 'TARGET+UK'."""
    parts = [p.strip().upper() for p in name.split("+")]
    cals = [CALENDARS["WeekendsOnly" if p == "WEEKENDSONLY" else p] for p in parts]
    return cals[0] if len(cals) == 1 else JointCalendar(*cals)
