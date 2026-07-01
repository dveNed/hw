"""Risk/reward and position-sizing engine.

Pure functions and dataclasses — no network, no side effects — so this is the
one part of the system we can test exhaustively and trust. Everything here is
about answering three questions before a trade:

    1. How big should the position be so a loss costs a fixed % of the account?
    2. Is the reward worth the risk (R:R), *after* fees?
    3. Where does the exchange liquidate me, and is my stop safely in front of it?

Conventions
-----------
- Prices are in quote currency (USD).
- ``side`` is "long" or "short".
- ``risk_fraction`` is the fraction of account equity you are willing to lose
  if the stop is hit, e.g. 0.01 == 1%.
- Fees are per-side fractions of notional (e.g. 0.00045 == 4.5 bps taker).
- Funding is ignored here; over short holding periods it's second-order, and
  modelling it well needs the live funding rate (see ``hyperliquid``).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Side(str, Enum):
    LONG = "long"
    SHORT = "short"

    @classmethod
    def parse(cls, value: "str | Side") -> "Side":
        if isinstance(value, Side):
            return value
        v = value.strip().lower()
        if v in ("long", "buy", "l"):
            return cls.LONG
        if v in ("short", "sell", "s"):
            return cls.SHORT
        raise ValueError(f"unknown side: {value!r} (expected long/short)")


def _sign(side: Side) -> int:
    return 1 if side is Side.LONG else -1


def infer_side(entry: float, stop: float) -> Side:
    """A stop sits below entry for a long, above entry for a short."""
    if stop < entry:
        return Side.LONG
    if stop > entry:
        return Side.SHORT
    raise ValueError("stop equals entry; cannot infer side or size a position")


def rr_ratio(entry: float, stop: float, target: float) -> float:
    """Reward-to-risk multiple ignoring fees.

    R = distance to target / distance to stop. An R of 2.0 means the trade
    pays 2 units for every 1 unit risked.
    """
    risk = abs(entry - stop)
    if risk == 0:
        raise ValueError("stop equals entry; risk is zero")
    reward = abs(target - entry)
    return reward / risk


def net_rr_ratio(
    entry: float,
    stop: float,
    target: float,
    *,
    fee_rate: float = 0.0,
) -> float:
    """Reward-to-risk after round-trip fees (entry fill + exit fill).

    Fees widen the effective loss and shrink the effective win, so tight scalps
    with a nominally fine R:R can be net-negative once costs are paid. We charge
    ``fee_rate`` on the entry notional and on the exit notional.
    """
    if fee_rate < 0:
        raise ValueError("fee_rate must be non-negative")
    risk = abs(entry - stop)
    if risk == 0:
        raise ValueError("stop equals entry; risk is zero")
    reward = abs(target - entry)
    # Per-unit fee cost = fee on entry price + fee on exit price.
    win_fees = fee_rate * (entry + target)
    loss_fees = fee_rate * (entry + stop)
    net_reward = reward - win_fees
    net_risk = risk + loss_fees
    return net_reward / net_risk


def position_size(
    equity: float,
    risk_fraction: float,
    entry: float,
    stop: float,
) -> float:
    """Size (in units of the base asset, e.g. BTC) so that hitting the stop
    loses exactly ``risk_fraction`` of ``equity``.

    size = (equity * risk_fraction) / |entry - stop|
    """
    if equity <= 0:
        raise ValueError("equity must be positive")
    if not 0 < risk_fraction < 1:
        raise ValueError("risk_fraction must be in (0, 1), e.g. 0.01 for 1%")
    per_unit_risk = abs(entry - stop)
    if per_unit_risk == 0:
        raise ValueError("stop equals entry; per-unit risk is zero")
    dollars_at_risk = equity * risk_fraction
    return dollars_at_risk / per_unit_risk


def liquidation_price(
    entry: float,
    leverage: float,
    side: Side,
    *,
    maintenance_margin_fraction: float,
) -> float:
    """Estimate isolated-margin liquidation price.

    Derived from: initial_margin + unrealized_pnl == maintenance_margin.
        long : P = entry * (1 - 1/leverage) / (1 - mmf)
        short: P = entry * (1 + 1/leverage) / (1 + mmf)

    ``maintenance_margin_fraction`` (mmf) is exchange/asset specific. On
    Hyperliquid it's roughly 1/(2 * max_leverage) for the asset's tier — for
    BTC at 40x max that's ~0.0125. This is an *estimate*: use the live value
    from the asset context for anything real. Cross-margin liquidation depends
    on the whole account and is not modelled here.
    """
    if leverage <= 0:
        raise ValueError("leverage must be positive")
    mmf = maintenance_margin_fraction
    if not 0 <= mmf < 1:
        raise ValueError("maintenance_margin_fraction must be in [0, 1)")
    if side is Side.LONG:
        return entry * (1 - 1 / leverage) / (1 - mmf)
    return entry * (1 + 1 / leverage) / (1 + mmf)


@dataclass(frozen=True)
class TradePlan:
    """A fully evaluated trade proposal.

    Build one with :func:`build_trade_plan`. Read ``warnings`` before you act on
    ``size`` — a plan can be arithmetically valid and still a bad idea.
    """

    side: Side
    entry: float
    stop: float
    target: float
    equity: float
    risk_fraction: float
    leverage: float
    fee_rate: float

    size: float  # units of base asset (e.g. BTC)
    notional: float  # size * entry, in USD
    margin_required: float  # notional / leverage
    dollars_at_risk: float  # loss if stop hit (pre-fee)
    rr: float  # gross reward:risk
    net_rr: float  # reward:risk after round-trip fees
    liq_price: float  # estimated liquidation price
    stop_to_liq_buffer: float  # fraction of entry between stop and liq price
    warnings: tuple[str, ...]

    @property
    def ok(self) -> bool:
        """True if the plan tripped no warnings."""
        return not self.warnings

    def summary(self) -> str:
        lines = [
            f"{self.side.value.upper()}  entry={self.entry:g}  stop={self.stop:g}  target={self.target:g}",
            f"  size:      {self.size:.6g} units   notional=${self.notional:,.2f}",
            f"  margin:    ${self.margin_required:,.2f} at {self.leverage:g}x",
            f"  risk:      ${self.dollars_at_risk:,.2f} ({self.risk_fraction * 100:g}% of ${self.equity:,.2f})",
            f"  R:R:       {self.rr:.2f} gross / {self.net_rr:.2f} net (fees {self.fee_rate * 1e4:g} bps/side)",
            f"  liq est.:  {self.liq_price:,.2f}  (stop is {self.stop_to_liq_buffer * 100:.2f}% of entry in front of liq)",
        ]
        if self.warnings:
            lines.append("  warnings:")
            lines.extend(f"    - {w}" for w in self.warnings)
        else:
            lines.append("  warnings:  none")
        return "\n".join(lines)


def build_trade_plan(
    *,
    entry: float,
    stop: float,
    target: float,
    equity: float,
    risk_fraction: float = 0.01,
    leverage: float = 1.0,
    fee_rate: float = 0.00045,
    maintenance_margin_fraction: float = 0.0125,
    side: "str | Side | None" = None,
    min_rr: float = 1.5,
) -> TradePlan:
    """Evaluate a trade end to end and flag anything dangerous.

    Sizing is driven purely by the stop distance and ``risk_fraction`` — the
    *account-risk* model, which is the only sizing method that survives contact
    with a losing streak. Leverage only affects the margin you must post and the
    liquidation price; it does NOT change position size here. That separation is
    deliberate: leverage should never be the thing that decides how much you can
    lose on a trade.

    Warnings are raised (not exceptions) for:
      - net R:R below ``min_rr``
      - stop sitting at or beyond the estimated liquidation price
      - margin required exceeding available equity
      - target on the wrong side of entry for the trade direction
    """
    resolved_side = Side.parse(side) if side is not None else infer_side(entry, stop)

    size = position_size(equity, risk_fraction, entry, stop)
    notional = size * entry
    margin_required = notional / leverage
    dollars_at_risk = size * abs(entry - stop)
    gross_rr = rr_ratio(entry, stop, target)
    net_rr = net_rr_ratio(entry, stop, target, fee_rate=fee_rate)
    liq = liquidation_price(
        entry, leverage, resolved_side,
        maintenance_margin_fraction=maintenance_margin_fraction,
    )
    # Positive buffer == stop is reached before liquidation (good).
    if resolved_side is Side.LONG:
        buffer = (stop - liq) / entry
    else:
        buffer = (liq - stop) / entry

    warnings: list[str] = []

    # Target should be in the profitable direction.
    if _sign(resolved_side) * (target - entry) <= 0:
        warnings.append(
            f"target {target:g} is not in profit direction for a {resolved_side.value}"
        )
    if net_rr < min_rr:
        warnings.append(
            f"net R:R {net_rr:.2f} is below minimum {min_rr:g} (fees make this marginal)"
        )
    if buffer <= 0:
        warnings.append(
            f"stop {stop:g} is at/beyond liquidation ~{liq:,.2f}: "
            f"you'd be liquidated before your stop fills — reduce leverage"
        )
    if margin_required > equity:
        warnings.append(
            f"margin required ${margin_required:,.2f} exceeds equity ${equity:,.2f}: "
            f"reduce size or raise leverage"
        )

    return TradePlan(
        side=resolved_side,
        entry=entry,
        stop=stop,
        target=target,
        equity=equity,
        risk_fraction=risk_fraction,
        leverage=leverage,
        fee_rate=fee_rate,
        size=size,
        notional=notional,
        margin_required=margin_required,
        dollars_at_risk=dollars_at_risk,
        rr=gross_rr,
        net_rr=net_rr,
        liq_price=liq,
        stop_to_liq_buffer=buffer,
        warnings=tuple(warnings),
    )
