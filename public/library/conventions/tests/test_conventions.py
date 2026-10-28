"""veqctor_conventions checked against QuantLib reference values.

The expected values in reference/conventions_quantlib.json were computed with
QuantLib (version recorded in the file). QuantLib is NOT needed to run these
tests: they only compare against the stored numbers and dates.
"""
import json
from datetime import date
from pathlib import Path

import pytest

from veqctor_conventions import adjust, advance, get_calendar, make_schedule, year_fraction

REF = json.loads((Path(__file__).parent / "reference" / "conventions_quantlib.json").read_text())
D = date.fromisoformat


def test_reference_version_recorded():
    assert REF["quantlib_version"]


@pytest.mark.parametrize("start,end,convention,termination,expected", REF["daycount"][:: max(1, len(REF["daycount"]) // 600)])
def test_year_fraction_sample(start, end, convention, termination, expected):
    got = year_fraction(D(start), D(end), convention, D(termination) if termination else None)
    assert got == pytest.approx(expected, abs=1e-12)


def test_year_fraction_all():
    bad = [
        row for row in REF["daycount"]
        if abs(year_fraction(D(row[0]), D(row[1]), row[2], D(row[3]) if row[3] else None) - row[4]) > 1e-12
    ]
    assert not bad, f"{len(bad)} mismatches, first: {bad[:3]}"


@pytest.mark.parametrize("name", sorted(REF["holidays"]))
def test_holidays_2000_2050(name):
    got = [d.isoformat() for d in get_calendar(name).holiday_list(date(2000, 1, 1), date(2050, 12, 31))]
    expected = REF["holidays"][name]
    assert got == expected, f"missing {sorted(set(expected) - set(got))[:5]}, extra {sorted(set(got) - set(expected))[:5]}"


def test_adjust():
    bad = [r for r in REF["adjust"] if adjust(D(r[0]), get_calendar(r[1]), r[2]).isoformat() != r[3]]
    assert not bad, bad[:3]


def test_advance():
    bad = [r for r in REF["advance"] if advance(D(r[0]), r[1], r[2], get_calendar(r[3]), r[4], r[5]).isoformat() != r[6]]
    assert not bad, bad[:3]


def test_schedules():
    bad = []
    for eff, term, m, cal, conv, tconv, rule, eom, expected in REF["schedules"]:
        got = [d.isoformat() for d in make_schedule(D(eff), D(term), m, get_calendar(cal), conv, tconv, rule, eom)]
        if got != expected:
            bad.append((eff, term, m, cal, rule, eom))
    assert not bad, bad[:3]


def test_joint_calendar():
    joint = get_calendar("TARGET+UK")
    assert joint.is_holiday(date(2026, 5, 25))   # UK spring bank holiday, TARGET open
    assert joint.is_holiday(date(2026, 5, 1))    # TARGET Labour Day, UK open
    assert joint.is_business_day(date(2026, 5, 26))


def test_spot_lag_over_easter():
    # Thursday before Easter 2026, T+2 on TARGET skips Good Friday and Easter Monday
    assert advance(date(2026, 4, 2), 2, "D", get_calendar("TARGET")) == date(2026, 4, 8)
