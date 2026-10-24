"""Compute QuantLib reference values for pl4nck_conventions and check the module against them.

Run from the repo root:  pip install QuantLib && python3 tools/library/build_conventions_vectors.py
Writes public/library/conventions/tests/reference/conventions_quantlib.json.
"""
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

import QuantLib as ql

ROOT = Path(__file__).resolve().parents[2] / "public" / "library" / "conventions"
sys.path.insert(0, str(ROOT))
import pl4nck_conventions as pc  # noqa: E402

rng = random.Random(20261024)
qd = lambda d: ql.Date(d.day, d.month, d.year)  # noqa: E731
pd = lambda d: date(d.year(), d.month(), d.dayOfMonth())  # noqa: E731
iso = lambda d: d.isoformat()  # noqa: E731

CALS = {
    "TARGET": ql.TARGET(),
    "FR": ql.France(ql.France.Settlement),
    "UK": ql.UnitedKingdom(ql.UnitedKingdom.Settlement),
    "US": ql.UnitedStates(ql.UnitedStates.Settlement),
}
SAFE = ["TARGET", "UK", "US"]  # FR excluded from derived vectors because of the QuantLib defect below
BDC = {"F": ql.Following, "MF": ql.ModifiedFollowing, "P": ql.Preceding, "MP": ql.ModifiedPreceding, "U": ql.Unadjusted}


def rand_date(y0=2000, y1=2049):
    return date(y0, 1, 1) + timedelta(days=rng.randrange((date(y1, 12, 31) - date(y0, 1, 1)).days))


def edge_dates():
    out = []
    for y in (2000, 2004, 2023, 2024, 2100 - 76):
        for m, d in ((2, 28), (2, 29), (1, 30), (1, 31), (3, 30), (3, 31), (12, 31), (8, 31), (6, 30)):
            try:
                out.append(date(y, m, d))
            except ValueError:
                pass
    return out


out = {"quantlib_version": ql.__version__, "daycount": [], "holidays": {}, "adjust": [], "advance": [], "schedules": []}
errors = []

# Day counts
pairs = []
edges = edge_dates()
for a in edges:
    for b in edges:
        if b > a:
            pairs.append((a, b))
pairs = rng.sample(pairs, min(len(pairs), 300))
for _ in range(400):
    a = rand_date()
    pairs.append((a, a + timedelta(days=rng.randrange(1, 4000))))
for a, b in pairs:
    for name, dc in [("ACT/360", ql.Actual360()), ("ACT/365F", ql.Actual365Fixed()),
                     ("ACT/ACT ISDA", ql.ActualActual(ql.ActualActual.ISDA)),
                     ("30/360", ql.Thirty360(ql.Thirty360.BondBasis)), ("30E/360", ql.Thirty360(ql.Thirty360.European))]:
        v = dc.yearFraction(qd(a), qd(b))
        out["daycount"].append([iso(a), iso(b), name, None, v])
    term = b if rng.random() < 0.5 else b + timedelta(days=365)
    v = ql.Thirty360(ql.Thirty360.ISDA, qd(term)).yearFraction(qd(a), qd(b))
    out["daycount"].append([iso(a), iso(b), "30E/360 ISDA", iso(term), v])
for a, b, name, term, v in out["daycount"]:
    mine = pc.year_fraction(date.fromisoformat(a), date.fromisoformat(b), name, date.fromisoformat(term) if term else None)
    if abs(mine - v) > 1e-12:
        errors.append(("daycount", a, b, name, term, v, mine))

# Holidays, weekdays only, 2000-2050
# Known QuantLib 1.44 defect: France.Settlement hard-codes Ascension on May 10 and
# Whit Monday on May 21, although both move with Easter (Easter + 39 and + 50 days).
# The reference keeps QuantLib's list with those two holidays corrected, and records
# the correction so it stays visible.
def fr_correct(dates):
    fixed = [d for d in dates if not (d.month == 5 and d.day in (10, 21))]
    for y in range(2000, 2051):
        for k in (39, 50):
            d = pc.easter(y) + timedelta(days=k)
            if d.weekday() < 5:
                fixed.append(d)
    return sorted(set(fixed))


out["notes"] = {"FR": "QuantLib 1.44 France.Settlement places Ascension on May 10 and Whit Monday on May 21 every year. "
                      "Both are moveable (Easter + 39 and Easter + 50 days, Code du travail L3133-1); the reference corrects them."}
for name, cal in CALS.items():
    raw = [pd(d) for d in ql.Calendar.holidayList(cal, ql.Date(1, 1, 2000), ql.Date(31, 12, 2050), False)]
    ref = [iso(d) for d in (fr_correct(raw) if name == "FR" else raw)]
    out["holidays"][name] = ref
    mine = [iso(d) for d in pc.get_calendar(name).holiday_list(date(2000, 1, 1), date(2050, 12, 31))]
    if mine != ref:
        errors.append(("holidays", name, sorted(set(ref) - set(mine))[:10], sorted(set(mine) - set(ref))[:10]))

# Adjustments
for _ in range(500):
    d = rand_date()
    name = rng.choice(SAFE)
    conv = rng.choice(list(BDC))
    v = iso(pd(CALS[name].adjust(qd(d), BDC[conv])))
    out["adjust"].append([iso(d), name, conv, v])
    mine = iso(pc.adjust(d, pc.get_calendar(name), conv))
    if mine != v:
        errors.append(("adjust", iso(d), name, conv, v, mine))

# Advance: spot lags and month tenors, with and without end-of-month rule
UNIT = {"D": ql.Days, "W": ql.Weeks, "M": ql.Months, "Y": ql.Years}
cases = [(date(2024, 2, 29), 1, "M"), (date(2024, 4, 30), 1, "M"), (date(2026, 1, 30), 1, "M"), (date(2026, 2, 27), 1, "M")]
for _ in range(400):
    unit = rng.choice(["D", "D", "W", "M", "M", "Y"])
    n = rng.choice([1, 2, 3, 6, 12, -1, -2]) if unit != "D" else rng.choice([0, 1, 2, 3, 5, -2])
    cases.append((rand_date(), n, unit))
for d, n, unit in cases:
    name = rng.choice(SAFE)
    conv = rng.choice(["F", "MF", "P"])
    eom = rng.random() < 0.5
    v = iso(pd(CALS[name].advance(qd(d), n, UNIT[unit], BDC[conv], eom)))
    out["advance"].append([iso(d), n, unit, name, conv, eom, v])
    mine = iso(pc.advance(d, n, unit, pc.get_calendar(name), conv, eom))
    if mine != v:
        errors.append(("advance", iso(d), n, unit, name, conv, eom, v, mine))

# Schedules
RULE = {"backward": ql.DateGeneration.Backward, "forward": ql.DateGeneration.Forward}
sched_cases = [
    (date(2026, 3, 18), date(2031, 3, 18), 6, "TARGET", "MF", "U", "backward", False),
    (date(2026, 1, 31), date(2031, 1, 31), 6, "TARGET", "MF", "U", "backward", True),
    (date(2026, 2, 28), date(2030, 8, 31), 6, "UK", "MF", "MF", "backward", True),
    (date(2026, 5, 15), date(2029, 11, 3), 12, "US", "F", "U", "forward", False),
    (date(2026, 5, 15), date(2029, 11, 3), 3, "US", "MF", "U", "backward", False),
]
for _ in range(80):
    eff = rand_date(2000, 2040)
    term = add = pc.add_months(eff, rng.choice([12, 24, 36, 60, 84, 120, 360]))
    if rng.random() < 0.4:
        term = add + timedelta(days=rng.randrange(-80, 80))
    if rng.random() < 0.2:
        eff, term = pc.end_of_month(eff), pc.end_of_month(term)
    sched_cases.append((eff, term, rng.choice([1, 3, 6, 12]), rng.choice(SAFE), rng.choice(["F", "MF", "P", "U"]),
                        rng.choice(["U", "U", "MF", "F"]), rng.choice(["backward", "forward"]), rng.random() < 0.4))
for eff, term, m, name, conv, tconv, rule, eom in sched_cases:
    if term <= eff:
        continue
    s = ql.Schedule(qd(eff), qd(term), ql.Period(m, ql.Months), CALS[name], BDC[conv], BDC[tconv], RULE[rule], eom)
    ref = [iso(pd(d)) for d in s]
    out["schedules"].append([iso(eff), iso(term), m, name, conv, tconv, rule, eom, ref])
    mine = [iso(d) for d in pc.make_schedule(eff, term, m, pc.get_calendar(name), conv, tconv, rule, eom)]
    if mine != ref:
        errors.append(("schedule", iso(eff), iso(term), m, name, conv, tconv, rule, eom, ref, mine))

print(f"QuantLib {ql.__version__}: {len(out['daycount'])} day counts, {sum(map(len, out['holidays'].values()))} holidays, "
      f"{len(out['adjust'])} adjustments, {len(out['advance'])} advances, {len(out['schedules'])} schedules")
print(f"{len(errors)} mismatches")
for e in errors[:15]:
    print(e)
if errors:
    sys.exit(1)
dest = ROOT / "tests" / "reference" / "conventions_quantlib.json"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(out, separators=(",", ":")))
print("wrote", dest.relative_to(ROOT.parents[2]), f"{dest.stat().st_size // 1024} KB")
