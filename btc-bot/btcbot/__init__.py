"""btcbot — a Hyperliquid data + risk foundation for a Bitcoin trading system.

This package is intentionally split into layers that run at different speeds:

- ``hyperliquid``: thin REST client for public market data (price, funding,
  open interest, candles). No auth, read-only.
- ``recorder``: a polling loop that logs market context to disk so we can
  build a dataset for backtesting later.
- ``risk``: pure-logic risk/reward + position-sizing engine. No network, fully
  testable. This is the part that keeps the account alive.

Nothing here places orders. Trading execution is deliberately out of scope for
this foundation.
"""

__all__ = ["hyperliquid", "recorder", "risk"]
__version__ = "0.1.0"
