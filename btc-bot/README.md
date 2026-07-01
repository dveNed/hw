# btc-bot

A foundation for a Bitcoin trading system on [Hyperliquid](https://hyperliquid.xyz).
This is **not a bot yet** — it's the bedrock a bot needs: live market data, a
data recorder for building a backtest dataset, and a risk/reward engine that
sizes positions and refuses to let you blow up.

Nothing here places orders.

## Design philosophy: two clock speeds

The plan is a hybrid, not "pure rules" or "pure AI":

- **Fast layer (mechanical, no LLM):** ingest data, detect events (liquidation
  cascades, funding extremes, OI spikes), execute and enforce risk. An LLM must
  never hold your stop-loss.
- **Slow layer (Claude/Opus, on triggers):** the discretionary brain — regime
  classification ("should we even be trading right now?"), setup-quality
  scoring, and position sizing. Its edge is patience and judgment, not speed.
  You will never win a latency race to the bottom of a liquidation wick, so the
  AI's job is deciding *whether* and *how much*, not reacting tick-by-tick.

This repo is the data + risk groundwork for that. The AI decision layer and any
execution come later, and only after ideas survive backtesting + paper trading.

## Layout

```
btcbot/
  hyperliquid.py   # read-only REST client for public market data
  recorder.py      # polling loop -> JSONL dataset (+ OI-drop cascade heuristic)
  risk.py          # pure-logic R:R, position sizing, liquidation price  <-- tested
  cli.py           # `python -m btcbot ...`
tests/
  test_risk.py     # exhaustive tests for the risk engine
```

## Install

```bash
cd btc-bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # runtime (just: requests)
pip install -r requirements-dev.txt      # + pytest, to run tests
```

## Usage

### Risk / reward + position sizing (offline, no network)

Sizes the position so hitting your stop loses exactly `--risk` % of equity, then
checks R:R (after fees), liquidation distance, and margin. Exits non-zero if any
warning fires — safe to gate a script on.

```bash
python -m btcbot rr --entry 60000 --stop 59400 --target 61200 \
    --equity 10000 --risk 1 --leverage 5
```

```
LONG  entry=60000  stop=59400  target=61200
  size:      0.166667 units   notional=$10,000.00
  margin:    $2,000.00 at 5x
  risk:      $100.00 (1% of $10,000.00)
  R:R:       2.00 gross / 1.75 net (fees 4.5 bps/side)
  liq est.:  48,607.59  (stop is 17.99% of entry in front of liq)
  warnings:  none
```

Key idea: **leverage does not change position size.** Size is driven only by
your stop distance and account risk. Leverage only sets the margin you post and
where you get liquidated. That separation is what stops leverage from quietly
deciding how much you can lose.

### Live market context

```bash
python -m btcbot ctx --coin BTC
```

Prints mark/oracle/mid, mark-vs-oracle premium, hourly funding, open interest,
24h volume and change.

### Record data for backtesting

```bash
python -m btcbot record --coins BTC ETH --interval 15 --out data
```

Appends one JSON row per coin per tick to `data/<COIN>_<date>.jsonl` (funding,
OI, prices, volume, and per-tick OI delta). Alerts when open interest drops
sharply in a single tick — a rough proxy for a liquidation cascade.

## Tests

```bash
python -m pytest tests/ -q
```

The risk engine is fully unit-tested (sizing math, liquidation formula, and
every warning path). The network client is not unit-tested against live APIs;
validate it with `python -m btcbot ctx` wherever Hyperliquid is reachable.

## Known limitations / next steps

- **No real liquidation feed.** The recorder infers cascades from OI drops.
  Hyperliquid's public API has no clean historical liquidation endpoint; a
  proper feed likely means the WebSocket `trades` stream or a data provider.
- **Liquidation price is an estimate** (isolated margin, assumed maintenance
  margin fraction). Use the live per-asset value for anything real; cross-margin
  is not modelled.
- **No backtester yet.** Recording builds the dataset; the backtest harness is
  the natural next module.
- **No AI decision layer or execution yet** — deliberately. Data + risk first.
