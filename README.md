# eth-pnl-fixed — Donchian trend strategy

AIProve bounty `eth-pnl-fixed`: highest **net PnL after costs** on the frozen
ETH 1-min dataset. 1st place: 1,000,000 PROVE. Closes 2026-11-20 13:49 UTC.

## Headline result

| | |
|---|---|
| **Net PnL after costs** | **+$79.72** (1 ETH fixed size) |
| Gross PnL | +$86.79 |
| Costs (fees $5.89 + slippage $1.18) | −$7.07 |
| Max drawdown | $32.83 |
| Fills | 3 (1 round trip + 1 entry) |
| Benchmarks | buy & hold −$70.51 · always short +$65.65 |

## Strategy

Asymmetric Donchian breakout, 2 parameters:

- **LONG** on a new 240-bar (4h) high close; **SHORT** on a new 240-bar low close.
- **FLAT** on a new 120-bar (2h) low close while long, or a new 120-bar high
  close while short. Slow entry, faster exit.

Fixed 1 ETH, long/short/flat only. Signals computed on bar `i` execute at
the **open of bar `i+1`** — no lookahead, no phantom fills.

The one trade that matters: short at bar 739 (12h19m, $2,006.03) on the
240-bar low breakdown that opens the day's waterfall; flat at bar 1094
($1,939.58); long at bar 1308 ($1,948.26) into the bounce.

## Why this shape

- Mean |1-min move| is ~7 bps; a round trip costs ~24 bps at base costs.
  Anything that trades often dies on fees (EMA crossovers: gross +$27..+$49,
  **net −$49..−$248**).
- The day is one regime: ~12h of flat chop, one −$78 waterfall in 4h, then
  a +$30 bounce. Only a slow breakout system sits out the chop and rides
  the waterfall.
- The parameters are a plateau, not a spike: every neighbour in
  entry 180–300 × exit 60–240 nets **+$47..+$83** after costs.

## Cost model (assumption, documented)

The challenge publishes no exact fee/slippage rates, only "maker + taker
fees, plus slippage scaled by size". Base case used here:

- taker fee **10 bps** per fill (Binance spot standard; all fills assumed
  taker/market — the conservative case)
- slippage **2 bps** per fill at 1 ETH, scaling linearly with size

Sensitivity (net PnL): 0 bps fees → +$86.79 · 5 bps + 1 bp slip → +$83.25 ·
**10 + 2 → +$79.72** · 20 + 5 → +$72.06. The result is driven by the
one big move, not by the cost assumption (only 3 fills).

## Robustness — synthetic held-out tails

Level-adjusted resampled blocks appended after bar 1439 (returns preserved,
seam jumps removed), strategy re-run from the sample-end position (long 1 ETH):

| tail | tail PnL |
|---|---|
| crash continues | +$48.70 |
| bounce continues | +$27.53 |
| flat chop | −$5.59 |
| crash then bounce | +$33.73 |
| chop then crash | +$62.06 |

Worst case is a small bleed in chop; no blow-up in any regime.

## Reproduce

```bash
python3 backtest.py                 # base case: net +$79.72
python3 backtest.py --fee-bps 20 --slip-bps 5   # pessimistic costs
```

Requires pandas + numpy. Dataset `data/bars.csv` is the frozen published
file, vendored verbatim (sha256 `68a0f9c1…808038`):
`AIProveRH/aiprove`, `challenges/eth-backtest/bars.csv` — 1,440 real
Binance ETH/USDT 1-min bars, 24h ending 2026-11-13 12:17 UTC.

## Files

- `strategy.py` — the strategy: `positions_for(bars)` → target positions.
- `engine.py` — backtest engine: next-open fills, fee/slippage accounting.
- `backtest.py` — runnable entrypoint (prints the headline numbers).
- `data/bars.csv` — vendored dataset.

## Submission (for the main session)

AIProve code-task submit shape (`POST /api/bounties/eth-pnl-fixed/submit`,
Bearer session token, handle `kitxyz`):

```json
{
  "repoUrl": "https://github.com/Kibitty/<repo>",
  "commit": "<full 40-char sha of this repo>",
  "transcript": "<build-session transcript, secrets stripped>",
  "handle": "kitxyz"
}
```

Notes: this repo needs to be **public on GitHub** (blocked on the GitHub PAT,
same as make.fun github-core-clone). No published sandbox entrypoint spec
exists in the AIProve repo (grader v1 only implements forecast); the
entrypoint is `python3 backtest.py` and the strategy interface is
`strategy.positions_for(bars)`, both documented here so a grader can run it
with one command. Do **not** submit from this session — no private key here;
the main session submits after the PAT lands.
