"""Black-Scholes prototype from the Veqctor model library (validated kit)."""
from .model import (MCResult, bgk_barrier, bs_greeks, bs_price, geometric_asian_price, mc_price,
                    time_grid)

__version__ = "1.0.0"
__all__ = ["MCResult", "bgk_barrier", "bs_greeks", "bs_price", "geometric_asian_price", "mc_price", "time_grid"]
