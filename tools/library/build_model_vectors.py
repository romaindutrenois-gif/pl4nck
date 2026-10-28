"""Reference values computed with QuantLib for the Veqctor model library.

Run from the repo root:  pip install QuantLib && python3 tools/library/build_model_vectors.py
Writes public/library/models/<id>/reference_quantlib.json.

Conventions used in every file, so a prototype can reproduce them without dates:
  - time in years T = days / 365 (QuantLib Actual/365 Fixed);
  - flat continuously compounded rates r (and dividend yield q);
  - prices per unit notional (per 1 of underlying for equity, per 1 of face for bonds).
"""
import json
import math
from pathlib import Path

import QuantLib as ql

OUT = Path(__file__).resolve().parents[2] / "public" / "library" / "models"
TODAY = ql.Date(15, 1, 2026)
ql.Settings.instance().evaluationDate = TODAY
DC = ql.Actual365Fixed()


def flat(rate):
    return ql.YieldTermStructureHandle(ql.FlatForward(TODAY, rate, DC, ql.Continuous, ql.NoFrequency))


def write(model_id, payload):
    payload = {"model": model_id, "quantlib_version": ql.__version__, "conventions": __doc__.split("Conventions used in every file, so a prototype can reproduce them without dates:\n")[1].strip(), **payload}
    path = OUT / model_id / "reference_quantlib.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1))
    print(path.relative_to(OUT.parents[1]), sum(len(v) for v in payload.values() if isinstance(v, list)), "cases")


def bsm_process(s0, r, q, vol):
    return ql.BlackScholesMertonProcess(
        ql.QuoteHandle(ql.SimpleQuote(s0)), flat(q), flat(r),
        ql.BlackVolTermStructureHandle(ql.BlackConstantVol(TODAY, ql.TARGET(), vol, DC)))


# ---------------------------------------------------------------- Black-Scholes
def black_scholes():
    europeans, asians, barriers = [], [], []
    for s0, r, q, vol in [(100, 0.03, 0.0, 0.2), (100, 0.03, 0.02, 0.35), (100, -0.005, 0.0, 0.15)]:
        proc = bsm_process(s0, r, q, vol)
        engine = ql.AnalyticEuropeanEngine(proc)
        for days in (73, 365, 1825):
            for k in (80, 100, 120):
                for typ, qtyp in (("call", ql.Option.Call), ("put", ql.Option.Put)):
                    opt = ql.VanillaOption(ql.PlainVanillaPayoff(qtyp, k), ql.EuropeanExercise(TODAY + days))
                    opt.setPricingEngine(engine)
                    europeans.append({"s0": s0, "k": k, "r": r, "q": q, "vol": vol, "t": days / 365, "type": typ,
                                      "price": opt.NPV(), "delta": opt.delta(), "gamma": opt.gamma(),
                                      "vega": opt.vega() / 100, "rho": opt.rho() / 100})
        # Discretely monitored geometric average-price Asian (closed form), a classic Monte Carlo control variate
        for days, n_fix in ((365, 12), (730, 24)):
            fixings = [TODAY + int(round(days * (i + 1) / n_fix)) for i in range(n_fix)]
            for k in (90, 100, 110):
                opt = ql.DiscreteAveragingAsianOption(ql.Average.Geometric, 1.0, 0, fixings,
                                                      ql.PlainVanillaPayoff(ql.Option.Call, k), ql.EuropeanExercise(fixings[-1]))
                opt.setPricingEngine(ql.AnalyticDiscreteGeometricAveragePriceAsianEngine(proc))
                asians.append({"s0": s0, "k": k, "r": r, "q": q, "vol": vol, "type": "call",
                               "fixing_times": [(d - TODAY) / 365 for d in fixings], "price": opt.NPV()})
        # Continuously monitored barriers (closed form). See the notes for comparing a discretely
        # monitored Monte Carlo against them.
        for days in (182, 365):
            for kind, qkind, bar in (("down-and-out", ql.Barrier.DownOut, 85), ("up-and-out", ql.Barrier.UpOut, 125)):
                for k in (95, 105):
                    opt = ql.BarrierOption(qkind, bar, 0.0, ql.PlainVanillaPayoff(ql.Option.Call, k), ql.EuropeanExercise(TODAY + days))
                    opt.setPricingEngine(ql.AnalyticBarrierEngine(proc))
                    barriers.append({"s0": s0, "k": k, "barrier": bar, "barrier_type": kind, "rebate": 0.0, "r": r, "q": q,
                                     "vol": vol, "t": days / 365, "type": "call", "monitoring": "continuous", "price": opt.NPV()})
    write("black_scholes", {
        "notes": "Greeks: vega and rho per 1% (absolute 0.01) move; delta and gamma per unit of spot. Geometric Asian: average over the listed fixing times only (not including t=0), payoff max(G - K, 0) at the last fixing. Barriers are continuously monitored. To compare a Monte Carlo with m monitoring dates (step dt), move the barrier away from spot by the Broadie-Glasserman-Kou factor: H*exp(+0.5826*vol*sqrt(dt)) for a down barrier, H*exp(-0.5826*vol*sqrt(dt)) for an up barrier. The correction is approximate: allow about 1% of the price on top of the Monte Carlo error.",
        "european": europeans, "geometric_asian": asians, "barrier": barriers})


# ---------------------------------------------------------------- Heston
def heston():
    cases = []
    sets = [
        {"label": "Feller satisfied", "v0": 0.04, "kappa": 2.0, "theta": 0.04, "sigma": 0.3, "rho": -0.7},
        {"label": "Feller violated (equity-like skew)", "v0": 0.0225, "kappa": 1.5, "theta": 0.04, "sigma": 0.8, "rho": -0.75},
        {"label": "Positive correlation", "v0": 0.09, "kappa": 3.0, "theta": 0.06, "sigma": 0.5, "rho": 0.3},
    ]
    for p in sets:
        for s0, r, q in [(100, 0.03, 0.01)]:
            proc = ql.HestonProcess(flat(r), flat(q), ql.QuoteHandle(ql.SimpleQuote(s0)), p["v0"], p["kappa"], p["theta"], p["sigma"], p["rho"])
            engine = ql.AnalyticHestonEngine(ql.HestonModel(proc), 1e-10, 100000)
            for days in (91, 365, 1825):
                for k in (70, 90, 100, 110, 140):
                    for typ, qtyp in (("call", ql.Option.Call), ("put", ql.Option.Put)):
                        opt = ql.VanillaOption(ql.PlainVanillaPayoff(qtyp, k), ql.EuropeanExercise(TODAY + days))
                        opt.setPricingEngine(engine)
                        price = opt.NPV()
                        t = days / 365
                        cases.append({**p, "s0": s0, "r": r, "q": q, "t": t, "k": k, "type": typ, "price": price,
                                      "feller": 2 * p["kappa"] * p["theta"] - p["sigma"] ** 2})
    write("heston", {
        "notes": "Prices from QuantLib AnalyticHestonEngine (adaptive Gauss-Lobatto, tolerance 1e-10). "
                 "feller = 2 kappa theta - sigma^2 (positive means the variance cannot reach zero). "
                 "sigma is the volatility of variance.",
        "european": cases})


# ---------------------------------------------------------------- Hull-White one factor
def hull_white():
    bond_options, caps = [], []
    for r0, a, sigma in [(0.03, 0.05, 0.01), (0.025, 0.2, 0.015), (-0.002, 0.03, 0.008)]:
        curve = flat(r0)
        model = ql.HullWhite(curve, a, sigma)
        for t_exp, t_bond in [(1, 2), (1, 5), (5, 10), (2, 3)]:
            for typ, qtyp in (("call", ql.Option.Call), ("put", ql.Option.Put)):
                fwd = math.exp(-r0 * (t_bond - t_exp))
                for mny in (0.97, 1.0, 1.03):
                    k = fwd * mny
                    bond_options.append({"r0_flat": r0, "a": a, "sigma": sigma, "option_expiry": t_exp, "bond_maturity": t_bond,
                                         "strike": k, "type": typ, "price": model.discountBondOption(qtyp, k, t_exp, t_bond)})
        # Caps as portfolios of caplets: caplet on simple rate over [t_i, t_i + tau] with strike K
        # equals (1 + K tau) puts on the zero-coupon bond P(t_i, t_i + tau) with strike 1 / (1 + K tau).
        for maturity, tau in [(3, 0.5), (5, 0.25)]:
            for k_rate in (r0 - 0.005, r0, r0 + 0.01):
                n = int(round(maturity / tau))
                caplets = []
                for i in range(1, n):
                    t_i = i * tau
                    put = model.discountBondOption(ql.Option.Put, 1 / (1 + k_rate * tau), t_i, t_i + tau)
                    caplets.append((1 + k_rate * tau) * put)
                caps.append({"r0_flat": r0, "a": a, "sigma": sigma, "cap_maturity": maturity, "accrual": tau, "strike_rate": k_rate,
                             "first_reset": tau, "caplet_prices": caplets, "price": sum(caplets)})
    write("hull_white", {
        "notes": "Initial curve flat at r0_flat (continuous). bond_options: European option on a zero-coupon bond maturing at "
                 "bond_maturity, expiring at option_expiry, from QuantLib HullWhite.discountBondOption. caps: simple-rate caplets "
                 "reset at tau, 2 tau, ..., maturity - tau, accrual tau with year fraction exactly tau (no calendar), unit notional.",
        "bond_option": bond_options, "cap": caps})


if __name__ == "__main__":
    black_scholes()
    heston()
    hull_white()
