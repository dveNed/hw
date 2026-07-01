"""Thin Hyperliquid public-data client.

Read-only. Talks to the ``/info`` POST endpoint documented at
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint

We deliberately avoid the official SDK to keep the dependency surface tiny
(just ``requests``) and to keep full control over ret/backoff and logging.

Nothing here signs transactions or places orders.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import requests

MAINNET_INFO_URL = "https://api.hyperliquid.xyz/info"
TESTNET_INFO_URL = "https://api.hyperliquid-testnet.xyz/info"


@dataclass(frozen=True)
class AssetContext:
    """Per-asset market context from ``metaAndAssetCtxs``.

    Field names mirror Hyperliquid's payload. ``funding`` is the current hourly
    funding rate (a small fraction, e.g. 0.0000125). ``open_interest`` is in
    units of the base asset.
    """

    coin: str
    mark_px: float
    oracle_px: float
    mid_px: "float | None"
    funding: float
    open_interest: float
    day_ntl_vlm: float
    prev_day_px: float

    @property
    def premium(self) -> "float | None":
        """Mark vs oracle as a fraction — a quick perp/spot dislocation gauge."""
        if not self.oracle_px:
            return None
        return (self.mark_px - self.oracle_px) / self.oracle_px


class HyperliquidClient:
    def __init__(
        self,
        *,
        base_url: str = MAINNET_INFO_URL,
        timeout: float = 10.0,
        max_retries: int = 4,
        session: "requests.Session | None" = None,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = session or requests.Session()

    def _post(self, payload: dict) -> object:
        """POST to /info with exponential backoff on network/5xx errors."""
        delay = 1.0
        last_exc: "Exception | None" = None
        for attempt in range(self.max_retries):
            try:
                resp = self.session.post(
                    self.base_url, json=payload, timeout=self.timeout
                )
                if resp.status_code >= 500:
                    resp.raise_for_status()
                resp.raise_for_status()
                return resp.json()
            except (requests.RequestException, ValueError) as exc:
                last_exc = exc
                if attempt == self.max_retries - 1:
                    break
                time.sleep(delay)
                delay *= 2
        raise RuntimeError(
            f"Hyperliquid /info request failed after {self.max_retries} attempts: {last_exc}"
        )

    def all_mids(self) -> dict[str, float]:
        """Current mid price for every asset, keyed by coin symbol."""
        data = self._post({"type": "allMids"})
        return {coin: float(px) for coin, px in data.items()}  # type: ignore[union-attr]

    def meta(self) -> dict:
        """Universe metadata: list of assets with max leverage, decimals, etc."""
        return self._post({"type": "meta"})  # type: ignore[return-value]

    def asset_contexts(self) -> dict[str, AssetContext]:
        """Live context (funding, OI, mark, oracle, volume) keyed by coin.

        ``metaAndAssetCtxs`` returns ``[meta, ctxs]`` where ``ctxs[i]``
        corresponds to ``meta["universe"][i]``.
        """
        meta, ctxs = self._post({"type": "metaAndAssetCtxs"})  # type: ignore[misc]
        universe = meta["universe"]
        mids = self.all_mids()
        out: dict[str, AssetContext] = {}
        for asset, ctx in zip(universe, ctxs):
            coin = asset["name"]
            mid = mids.get(coin)
            out[coin] = AssetContext(
                coin=coin,
                mark_px=float(ctx["markPx"]),
                oracle_px=float(ctx["oraclePx"]),
                mid_px=float(mid) if mid is not None else None,
                funding=float(ctx.get("funding", 0.0)),
                open_interest=float(ctx.get("openInterest", 0.0)),
                day_ntl_vlm=float(ctx.get("dayNtlVlm", 0.0)),
                prev_day_px=float(ctx.get("prevDayPx", 0.0)),
            )
        return out

    def context(self, coin: str) -> AssetContext:
        """Convenience: context for a single coin (e.g. "BTC")."""
        ctxs = self.asset_contexts()
        try:
            return ctxs[coin]
        except KeyError:
            raise KeyError(
                f"{coin!r} not found on Hyperliquid; available e.g. {sorted(ctxs)[:8]}..."
            ) from None

    def candles(
        self,
        coin: str,
        interval: str,
        start_ms: int,
        end_ms: "int | None" = None,
    ) -> list[dict]:
        """Historical candles. ``interval`` is like "1m", "15m", "1h", "1d".

        Times are Unix epoch milliseconds. Returns raw candle dicts with keys
        t/T (open/close time), o/h/l/c, v (volume), n (trades).
        """
        req = {"coin": coin, "interval": interval, "startTime": start_ms}
        if end_ms is not None:
            req["endTime"] = end_ms
        return self._post({"type": "candleSnapshot", "req": req})  # type: ignore[return-value]

    def funding_history(
        self, coin: str, start_ms: int, end_ms: "int | None" = None
    ) -> list[dict]:
        """Historical funding rates for a coin over a time window."""
        req = {"coin": coin, "startTime": start_ms}
        if end_ms is not None:
            req["endTime"] = end_ms
        return self._post({"type": "fundingHistory", **req})  # type: ignore[return-value]
