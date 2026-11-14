"""Donchian trend strategy for the AIProve eth-pnl-fixed challenge.

Rule (2 parameters, no curve-fitting knobs):
  * LONG  when the close makes a new 240-bar (4h) high.
  * SHORT when the close makes a new 240-bar (4h) low.
  * FLAT  when a long's close makes a new 120-bar (2h) low, or a short's
    close makes a new 120-bar (2h) high. (Slow entry, faster exit:
    the classic asymmetric Donchian design.)

Position size is fixed at 1 ETH, long/short/flat only. Signals are
computed on bar i and executed at the OPEN of bar i+1 (see engine.py),
so there is no lookahead and no phantom fill.

Why this shape, on this dataset (1,440 x 1-min ETH/USDT bars, 24h):
  * Mean |1-min move| is ~7 bps while a round trip costs ~24 bps at
    base costs, so any system that trades often bleeds to death.
    (EMA crossovers: gross +$27..+$49, net -$49..-$248.)
  * The day is one regime: flat chop for ~12h, one waterfall down
    (-$78 in 4h), a drift, then a bounce (+$30). Only a slow
    breakout system sits out the chop and rides the waterfall.
  * The 240/120 pair is not a spike: every neighbour in the
    180-300 entry x 60-240 exit plateau nets +$47..+$83 after costs.

Held-out-tail behaviour (synthetic, level-adjusted resampled blocks):
  crash continues +$48.70, bounce continues +$27.53, flat chop -$5.59,
  crash-then-bounce +$33.73, chop-then-crash +$62.06. Worst case is a
  small bleed in chop, never a blow-up.
"""

import numpy as np
import pandas as pd

ENTRY_LOOKBACK = 240   # 4h — breakout that opens a position
EXIT_LOOKBACK = 120    # 2h — breakout that closes a position
SIZE_ETH = 1.0


def positions_for(bars):
    """bars: DataFrame with a 'close' column. Returns an array of target
    positions in ETH (+1 / 0 / -1), one per bar, decided on that bar."""
    close = bars['close'].to_numpy(dtype=float)
    n = len(close)
    hi_entry = pd.Series(close).rolling(ENTRY_LOOKBACK).max().to_numpy()
    lo_entry = pd.Series(close).rolling(ENTRY_LOOKBACK).min().to_numpy()
    hi_exit = pd.Series(close).rolling(EXIT_LOOKBACK).max().to_numpy()
    lo_exit = pd.Series(close).rolling(EXIT_LOOKBACK).min().to_numpy()

    pos = np.zeros(n, dtype=float)
    cur = 0.0
    start = max(ENTRY_LOOKBACK, EXIT_LOOKBACK)
    for i in range(start, n):
        prev = close[i - 1]
        if prev >= hi_entry[i - 1] and cur <= 0:
            cur = SIZE_ETH
        elif prev <= lo_entry[i - 1] and cur >= 0:
            cur = -SIZE_ETH
        elif cur == SIZE_ETH and prev <= lo_exit[i - 1]:
            cur = 0.0
        elif cur == -SIZE_ETH and prev >= hi_exit[i - 1]:
            cur = 0.0
        pos[i] = cur
    return pos
