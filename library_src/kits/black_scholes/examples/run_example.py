"""Black-Scholes prototype against its benchmarks, in one screen of output."""
from black_scholes import bgk_barrier, bs_greeks, bs_price, geometric_asian_price, mc_price, time_grid

s0, k, r, q, vol, t = 100.0, 100.0, 0.03, 0.01, 0.2, 1.0

print("European call")
print(f"  closed form   {bs_price(s0, k, r, q, vol, t):.6f}")
m = mc_price(s0, k, r, q, vol, [t], n_paths=200_000, seed=1)
print(f"  Monte Carlo   {m.price:.6f} +/- {m.std_error:.6f}")
print("  Greeks       ", {g: round(v, 6) for g, v in bs_greeks(s0, k, r, q, vol, t).items()})

times = time_grid(t, 12)
print("\nMonthly Asian call")
print(f"  geometric, closed form  {geometric_asian_price(s0, k, r, q, vol, times):.6f}")
plain = mc_price(s0, k, r, q, vol, times, "arithmetic_asian", n_paths=100_000, seed=2)
cv = mc_price(s0, k, r, q, vol, times, "arithmetic_asian", n_paths=100_000, seed=3, control_variate=True)
print(f"  arithmetic, plain MC    {plain.price:.6f} +/- {plain.std_error:.6f}")
print(f"  arithmetic, with CV     {cv.price:.6f} +/- {cv.std_error:.6f}  (variance / {cv.variance_reduction:.0f})")

steps = 250
h = bgk_barrier(85.0, vol, t / steps, down=True)
b = mc_price(s0, k, r, q, vol, time_grid(t, steps), "down_out", n_paths=100_000, seed=4, barrier=h)
print(f"\nDown-and-out call, barrier 85, {steps} monitoring dates with BGK shift: {b.price:.4f} +/- {b.std_error:.4f}")
