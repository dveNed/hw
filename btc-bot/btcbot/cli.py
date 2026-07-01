"""Command-line entry point.

    python -m btcbot rr    --entry 60000 --stop 59400 --target 61200 --equity 10000
    python -m btcbot ctx   --coin BTC
    python -m btcbot record --coins BTC ETH --interval 15

The ``rr`` command is fully offline. ``ctx`` and ``record`` need network access
to Hyperliquid.
"""

from __future__ import annotations

import argparse
import sys

from . import risk
from .hyperliquid import HyperliquidClient, MAINNET_INFO_URL, TESTNET_INFO_URL
from .recorder import Recorder


def _cmd_rr(args: argparse.Namespace) -> int:
    plan = risk.build_trade_plan(
        entry=args.entry,
        stop=args.stop,
        target=args.target,
        equity=args.equity,
        risk_fraction=args.risk / 100.0,
        leverage=args.leverage,
        fee_rate=args.fee_bps / 1e4,
        maintenance_margin_fraction=args.mmf,
        side=args.side,
        min_rr=args.min_rr,
    )
    print(plan.summary())
    return 0 if plan.ok else 1


def _client(args: argparse.Namespace) -> HyperliquidClient:
    return HyperliquidClient(base_url=TESTNET_INFO_URL if args.testnet else MAINNET_INFO_URL)


def _cmd_ctx(args: argparse.Namespace) -> int:
    ctx = _client(args).context(args.coin)
    prem = ctx.premium
    print(f"{ctx.coin}")
    print(f"  mark:          {ctx.mark_px:,.2f}")
    print(f"  oracle:        {ctx.oracle_px:,.2f}")
    print(f"  mid:           {ctx.mid_px if ctx.mid_px is None else f'{ctx.mid_px:,.2f}'}")
    print(f"  premium:       {'n/a' if prem is None else f'{prem * 100:+.4f}%'}")
    print(f"  funding (1h):  {ctx.funding * 100:+.5f}%")
    print(f"  open interest: {ctx.open_interest:,.4f} {ctx.coin}")
    print(f"  24h volume:    ${ctx.day_ntl_vlm:,.0f}")
    chg = (ctx.mark_px - ctx.prev_day_px) / ctx.prev_day_px * 100 if ctx.prev_day_px else 0.0
    print(f"  24h change:    {chg:+.2f}%")
    return 0


def _cmd_record(args: argparse.Namespace) -> int:
    rec = Recorder(
        _client(args),
        coins=args.coins,
        out_dir=args.out,
        oi_drop_alert=args.oi_alert / 100.0,
    )
    rec.run(interval_s=args.interval, max_ticks=args.max_ticks)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="btcbot", description="Hyperliquid data + risk toolkit")
    p.add_argument("--testnet", action="store_true", help="use Hyperliquid testnet")
    sub = p.add_subparsers(dest="cmd", required=True)

    rr = sub.add_parser("rr", help="risk/reward + position sizing (offline)")
    rr.add_argument("--entry", type=float, required=True)
    rr.add_argument("--stop", type=float, required=True)
    rr.add_argument("--target", type=float, required=True)
    rr.add_argument("--equity", type=float, required=True, help="account equity in USD")
    rr.add_argument("--risk", type=float, default=1.0, help="%% of equity to risk (default 1)")
    rr.add_argument("--leverage", type=float, default=1.0)
    rr.add_argument("--fee-bps", type=float, default=4.5, help="per-side fee in bps (default 4.5)")
    rr.add_argument("--mmf", type=float, default=0.0125, help="maintenance margin fraction")
    rr.add_argument("--side", choices=["long", "short"], default=None, help="default: inferred")
    rr.add_argument("--min-rr", type=float, default=1.5, help="warn below this net R:R")
    rr.set_defaults(func=_cmd_rr)

    ctx = sub.add_parser("ctx", help="print live market context for a coin")
    ctx.add_argument("--coin", default="BTC")
    ctx.set_defaults(func=_cmd_ctx)

    rec = sub.add_parser("record", help="log market context to JSONL on an interval")
    rec.add_argument("--coins", nargs="+", default=["BTC"])
    rec.add_argument("--interval", type=float, default=15.0, help="seconds between ticks")
    rec.add_argument("--out", default="data", help="output directory")
    rec.add_argument("--oi-alert", type=float, default=2.0, help="%% OI drop to alert on")
    rec.add_argument("--max-ticks", type=int, default=None, help="stop after N ticks")
    rec.set_defaults(func=_cmd_record)

    return p


def main(argv: "list[str] | None" = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
