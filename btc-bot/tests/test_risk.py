import math

import pytest

from btcbot import risk
from btcbot.risk import Side


def test_infer_side():
    assert risk.infer_side(100, 95) is Side.LONG
    assert risk.infer_side(100, 105) is Side.SHORT
    with pytest.raises(ValueError):
        risk.infer_side(100, 100)


def test_rr_ratio():
    # risk 5, reward 10 -> 2R
    assert risk.rr_ratio(entry=100, stop=95, target=110) == pytest.approx(2.0)
    # symmetric for shorts
    assert risk.rr_ratio(entry=100, stop=105, target=90) == pytest.approx(2.0)
    with pytest.raises(ValueError):
        risk.rr_ratio(100, 100, 110)


def test_net_rr_below_gross():
    gross = risk.rr_ratio(100, 95, 110)
    net = risk.net_rr_ratio(100, 95, 110, fee_rate=0.001)
    assert net < gross
    # zero fee -> identical to gross
    assert risk.net_rr_ratio(100, 95, 110, fee_rate=0.0) == pytest.approx(gross)


def test_position_size_risks_exact_fraction():
    # $10k equity, risk 1% = $100, stop 5 away -> 20 units, loses exactly $100.
    size = risk.position_size(equity=10_000, risk_fraction=0.01, entry=100, stop=95)
    assert size == pytest.approx(20.0)
    assert size * abs(100 - 95) == pytest.approx(100.0)


def test_position_size_validation():
    with pytest.raises(ValueError):
        risk.position_size(0, 0.01, 100, 95)
    with pytest.raises(ValueError):
        risk.position_size(10_000, 1.5, 100, 95)
    with pytest.raises(ValueError):
        risk.position_size(10_000, 0.01, 100, 100)


def test_liquidation_price_long_below_short_above():
    long_liq = risk.liquidation_price(100, 10, Side.LONG, maintenance_margin_fraction=0.0125)
    short_liq = risk.liquidation_price(100, 10, Side.SHORT, maintenance_margin_fraction=0.0125)
    assert long_liq < 100 < short_liq
    # higher leverage -> liquidation closer to entry
    tighter = risk.liquidation_price(100, 50, Side.LONG, maintenance_margin_fraction=0.0125)
    assert tighter > long_liq  # closer to 100 from below


def test_liquidation_price_formula():
    # long: entry*(1-1/L)/(1-mmf)
    expected = 100 * (1 - 1 / 10) / (1 - 0.0125)
    assert risk.liquidation_price(100, 10, Side.LONG, maintenance_margin_fraction=0.0125) == pytest.approx(expected)


def test_trade_plan_clean_long():
    plan = risk.build_trade_plan(
        entry=60_000, stop=59_400, target=61_200, equity=10_000,
        risk_fraction=0.01, leverage=5, fee_rate=0.00045,
    )
    assert plan.side is Side.LONG
    assert plan.ok, plan.warnings
    assert plan.dollars_at_risk == pytest.approx(100.0)
    assert plan.rr == pytest.approx(2.0)
    assert plan.notional == pytest.approx(plan.size * 60_000)
    assert plan.margin_required == pytest.approx(plan.notional / 5)


def test_trade_plan_warns_low_rr():
    plan = risk.build_trade_plan(
        entry=100, stop=95, target=101, equity=10_000, min_rr=1.5,
    )
    assert not plan.ok
    assert any("R:R" in w for w in plan.warnings)


def test_trade_plan_warns_stop_beyond_liquidation():
    # 50x leverage: liquidation ~2% away; a stop 5% away sits past it.
    plan = risk.build_trade_plan(
        entry=100, stop=95, target=110, equity=10_000, leverage=50,
    )
    assert any("liquidation" in w for w in plan.warnings)


def test_trade_plan_warns_target_wrong_side():
    # forced long but target below entry
    plan = risk.build_trade_plan(
        entry=100, stop=95, target=99, equity=10_000, side="long",
    )
    assert any("profit direction" in w for w in plan.warnings)


def test_trade_plan_warns_margin_exceeds_equity():
    # tiny stop distance -> huge size -> notional dwarfs equity at 1x.
    plan = risk.build_trade_plan(
        entry=100, stop=99.99, target=100.5, equity=1_000,
        risk_fraction=0.5, leverage=1,
    )
    assert any("margin required" in w for w in plan.warnings)


def test_side_parse():
    assert Side.parse("BUY") is Side.LONG
    assert Side.parse("sell") is Side.SHORT
    assert Side.parse(Side.LONG) is Side.LONG
    with pytest.raises(ValueError):
        Side.parse("sideways")
