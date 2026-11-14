"""Reproduce the eth-pnl-fixed backtest.

Usage:
    python3 backtest.py [--bars data/bars.csv] [--fee-bps 10] [--slip-bps 2]

Prints gross PnL, costs, NET PnL after costs, max drawdown, fills, and
the per-4h-block split. Exit code 0. Requires pandas + numpy only.

Cost model (documented assumption — the challenge publishes no exact
rates, only "maker + taker fees, plus slippage scaled by size"):
  * taker fee  10 bps per fill (Binance spot standard; all fills assumed
    taker/market, the conservative case)
  * slippage    2 bps per fill at 1 ETH, scaling linearly with size
A round trip therefore costs ~24 bps (~$4.70 at ~$1,970/ETH).
"""

import argparse
import sys

import numpy as np

from engine import load_bars, run_backtest, block_pnl
from strategy import positions_for

DEFAULT_BARS = "data/bars.csv"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bars", default=DEFAULT_BARS)
    ap.add_argument("--fee-bps", type=float, default=10.0)
    ap.add_argument("--slip-bps", type=float, default=2.0)
    args = ap.parse_args()

    df = load_bars(args.bars)
    pos = positions_for(df)
    r = run_backtest(df, pos, fee_bps=args.fee_bps, slippage_bps=args.slip_bps)

    print(f"bars:            {len(df)}")
    print(f"gross PnL:       ${r['gross_pnl']:.2f}")
    print(f"fees:            ${r['fees']:.2f}")
    print(f"slippage:        ${r['slippage']:.2f}")
    print(f"total cost:      ${r['total_cost']:.2f}")
    print(f"NET PnL:         ${r['net_pnl']:.2f}")
    print(f"max drawdown:    ${r['max_drawdown']:.2f}")
    print(f"fills:           {r['n_fills']} ({r['n_roundtrips']} round trips)")
    print(f"final position:  {r['final_position']:+.0f} ETH")
    print(f"net PnL / 4h block: {block_pnl(r)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
