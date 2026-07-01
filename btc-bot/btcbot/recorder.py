"""Market-data recorder.

Polls Hyperliquid asset contexts on an interval and appends them to a
newline-delimited JSON (JSONL) file — one row per coin per tick. This is the
raw material for backtesting later: funding, open interest, mark/oracle price
and volume over time.

It also computes a cheap open-interest delta between ticks and flags large
drops, which are a rough proxy for liquidation cascades (OI collapses as
leveraged positions are force-closed). It's a heuristic, not a true liquidation
feed — noted in the README as a follow-up.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .hyperliquid import AssetContext, HyperliquidClient


def _now_ms() -> int:
    return int(time.time() * 1000)


def _daily_path(out_dir: Path, coin: str) -> Path:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return out_dir / f"{coin}_{day}.jsonl"


class Recorder:
    def __init__(
        self,
        client: HyperliquidClient,
        coins: list[str],
        out_dir: "str | Path" = "data",
        *,
        oi_drop_alert: float = 0.02,
        on_event: "Callable[[str], None] | None" = None,
    ) -> None:
        self.client = client
        self.coins = coins
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.oi_drop_alert = oi_drop_alert
        self.on_event = on_event or print
        self._last_oi: dict[str, float] = {}

    def _row(self, ctx: AssetContext) -> dict:
        row = asdict(ctx)
        row["ts"] = _now_ms()
        row["premium"] = ctx.premium
        prev_oi = self._last_oi.get(ctx.coin)
        if prev_oi:
            row["oi_delta_frac"] = (ctx.open_interest - prev_oi) / prev_oi
        else:
            row["oi_delta_frac"] = None
        return row

    def tick(self) -> list[dict]:
        """Fetch, log one round of context for all tracked coins, return rows."""
        contexts = self.client.asset_contexts()
        rows = []
        for coin in self.coins:
            ctx = contexts.get(coin)
            if ctx is None:
                self.on_event(f"[warn] {coin} not present in asset contexts this tick")
                continue
            row = self._row(ctx)
            path = _daily_path(self.out_dir, coin)
            with path.open("a") as fh:
                fh.write(json.dumps(row) + "\n")
            drop = row["oi_delta_frac"]
            if drop is not None and drop <= -self.oi_drop_alert:
                self.on_event(
                    f"[ALERT] {coin} open interest dropped {drop * 100:.2f}% "
                    f"in one tick (mark={ctx.mark_px:g}) — possible liquidation cascade"
                )
            self._last_oi[coin] = ctx.open_interest
            rows.append(row)
        return rows

    def run(self, interval_s: float = 15.0, max_ticks: "int | None" = None) -> None:
        """Poll forever (or ``max_ticks`` times). Ctrl-C to stop."""
        self.on_event(
            f"recording {self.coins} every {interval_s:g}s -> {self.out_dir}/ (Ctrl-C to stop)"
        )
        count = 0
        try:
            while max_ticks is None or count < max_ticks:
                start = time.time()
                try:
                    self.tick()
                except Exception as exc:  # keep the loop alive across transient errors
                    self.on_event(f"[error] tick failed: {exc}")
                count += 1
                elapsed = time.time() - start
                if max_ticks is None or count < max_ticks:
                    time.sleep(max(0.0, interval_s - elapsed))
        except KeyboardInterrupt:
            self.on_event("\nstopped.")
