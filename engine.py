"""Backtest engine for the AIProve eth-pnl-fixed challenge.

Fills: a signal computed on bar i is executed at the OPEN of bar i+1
(no lookahead, no phantom fills). Position is an integer number of ETH
(-SIZE, 0, +SIZE). Costs are charged per fill:

  fee      = 0.10% of notional (Binance spot taker, all fills assumed taker)
  slippage = 2 bps of notional per fill at SIZE_ETH = 1, scaling linearly
             with size (slippage_bps = 2 * size_eth / 1.0)

PnL is reported in USD for a fixed SIZE_ETH position. The strategy module
only decides the target position per bar; the engine does the accounting.
"""
import numpy as np
import pandas as pd

TAKER_FEE_BPS = 10.0     # 0.10% per fill
SLIPPAGE_BPS_AT_1ETH = 2.0
SIZE_ETH = 1.0


def load_bars(path):
    df = pd.read_csv(path)
    return df


def run_backtest(df, positions, fee_bps=TAKER_FEE_BPS,
                 slippage_bps=SLIPPAGE_BPS_AT_1ETH, size_eth=SIZE_ETH):
    """positions: array of target positions in ETH, decided on bar i,
    executed at open of bar i+1. Returns dict of stats + equity curve."""
    close = df['close'].to_numpy(dtype=float)
    open_ = df['open'].to_numpy(dtype=float)
    n = len(df)
    pos = np.zeros(n, dtype=float)          # position held DURING bar i
    target = np.asarray(positions, dtype=float)
    # target[i] decided on bar i -> held from bar i+1 onward
    pos[1:] = target[:-1]
    pos[0] = 0.0

    trades = np.diff(pos, prepend=0.0)      # signed size change at open of bar i
    # fill price = open of the bar where the trade executes
    fill_notional = np.abs(trades) * open_
    fee = fill_notional * fee_bps / 1e4
    slip = fill_notional * slippage_bps * (np.abs(trades) / size_eth) / 1e4
    # slippage scales with the size of THIS trade relative to 1 ETH
    costs = fee + slip

    # mark-to-market PnL while holding: pos[i] * (close[i] - close[i-1])
    # for i>=1; entry bar PnL uses open->close of that bar is handled by
    # holding from open: position held during bar i earns close[i]-open[i]
    # if entered at open of bar i, else close[i]-close[i-1].
    mtm = np.zeros(n)
    prev_close = np.concatenate([[open_[0]], close[:-1]])
    mtm = pos * (close - prev_close)
    # bars where we entered at open: replace close[i]-close[i-1] with close[i]-open[i]
    entered = trades != 0
    mtm[entered] = pos[entered] * (close[entered] - open_[entered])

    gross = mtm.sum()
    total_cost = costs.sum()
    net = gross - total_cost
    equity = np.cumsum(mtm - costs)
    running_max = np.maximum.accumulate(np.concatenate([[0.0], equity]))
    dd = running_max[1:] - equity
    max_dd = dd.max() if len(dd) else 0.0
    n_trades = int(np.count_nonzero(trades))
    n_roundtrips = n_trades // 2
    return {
        'per_bar_net': mtm - costs,
        'gross_pnl': round(float(gross), 2),
        'fees': round(float(fee.sum()), 2),
        'slippage': round(float(slip.sum()), 2),
        'total_cost': round(float(total_cost), 2),
        'net_pnl': round(float(net), 2),
        'max_drawdown': round(float(max_dd), 2),
        'n_fills': n_trades,
        'n_roundtrips': n_roundtrips,
        'final_position': float(pos[-1]),
        'equity': equity,
    }


def block_pnl(result):
    """Net PnL per 4h block (240 bars), exact attribution from a full run."""
    pb = result['per_bar_net']
    return [round(float(pb[i*240:(i+1)*240].sum()), 2) for i in range(6)]
