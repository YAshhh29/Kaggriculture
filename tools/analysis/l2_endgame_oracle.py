"""Upper bound on endgame sale TIMING against the recorded opponents.

For every live game of A / L, per item, the oracle knows the opponent's
executed sales at every step (from the exact replay), the town's consumption
and the exact price function, and re-times OUR sales of that item from
``--start`` to step 718 to maximise (our revenue - their revenue) on it.
Units cannot be sold before they are in our shed (arrival = the shed gain
before the market of each step, from the replay) and everything must be sold
by step 718. Within a step our order is assumed to trade first; the baseline
(our real sales) is scored under the same model, so gain = oracle - baseline.

Model simplifications, stated: our units never change the opponent's
executed quantities (true for a tape); a unit sold at $1 is treated as moving
the inventory like any other (the engine does not move it); WHEAT and
FERTILIZER are left out (the parent picks them up as feed / fertilizer).

    python -m tools.analysis.l2_endgame_oracle --start 600
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.analysis.l2_endgame_log import OUT, records  # noqa: E402
from tools.analysis.l2_endgame_policies import tick_units  # noqa: E402

ITEMS = ["CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"]


def trace(record):
    """Per step: our shed before the market, our and their executed sales,
    market inventory before the market, shops."""
    import kaggle_environments.envs.kaggriculture.kaggriculture as engine
    from tools.analysis.l2_endgame_bench import Game
    g = Game(record)
    side = g.side
    rows = {}
    orig = engine._process_market
    now = {"t": 0}

    def market(state, env_):
        t = now["t"]
        ours = dict(state[side].observation.private["shed"])
        theirs = dict(state[1 - side].observation.private["shed"])
        inv = dict(state[0].observation.market["inventory"])
        out = orig(state, env_)
        ours2 = state[side].observation.private["shed"]
        theirs2 = state[1 - side].observation.private["shed"]
        rows[t] = {"avail": {i: int(ours.get(i, 0)) for i in ITEMS},
                   "sold": {i: int(ours.get(i, 0)) - int(ours2.get(i, 0)) for i in ITEMS},
                   "opp": {i: int(theirs.get(i, 0)) - int(theirs2.get(i, 0)) for i in ITEMS},
                   "inv": {i: int(inv[i]) for i in ITEMS},
                   "shops": list(state[0].observation.town["unlocked_shops"])}
        return out

    def hooks(t, state, acts):
        now["t"] = t

    engine._process_market = market
    try:
        g.run(hooks=hooks)
    finally:
        engine._process_market = orig
    return rows


def price_table(item, lo, hi):
    from stack.market_front import _mf_price
    return np.array([_mf_price(item, x) for x in range(lo, hi)], dtype=float)


def solve(rows, item, start, end=718, nightly=False):
    """DP over our cumulative sales S since ``start``. Returns (baseline
    margin value, oracle value, oracle own revenue - baseline own revenue).
    ``nightly``: nothing may be held over a night (the late-game shed has
    ~0-11 units of room at the night drop), i.e. at hour 23 of every day all
    units that have arrived must be sold."""
    steps = list(range(start, end + 1))
    sold = np.array([max(0, rows[t]["sold"][item]) for t in steps])
    opp = np.array([max(0, rows[t]["opp"][item]) for t in steps])
    # arrivals: shed gain between the end of the previous market and this one
    arr = []
    prev_left = rows[start]["avail"][item]
    arr.append(prev_left)
    for k, t in enumerate(steps[1:], 1):
        left_before = rows[steps[k - 1]]["avail"][item] - rows[steps[k - 1]]["sold"][item]
        arr.append(max(0, rows[t]["avail"][item] - left_before))
    arr = np.array(arr)
    total = int(sold.sum())
    if total == 0:
        return 0.0, 0.0, 0.0, 0
    cum_arr = np.minimum(np.cumsum(arr), total)
    base_inv = np.array([rows[t]["inv"][item] for t in steps])
    cum_sold_before = np.concatenate([[0], np.cumsum(sold)[:-1]])
    # inventory before our sale at step k if we have sold S units since start:
    #   base_inv[k] - cum_sold_before[k] + S
    root = base_inv - cum_sold_before
    lo = int(root.min()) - 5
    hi = int(root.max() + total + opp.max() + 5)
    P = price_table(item, lo, hi)
    cP = np.concatenate([[0.0], np.cumsum(P)])   # cP[j] = sum P[0..j-1]

    def rev(x0, n):   # revenue of n units starting at inventory x0 (arrays ok)
        a = x0 - lo
        return cP[a + n] - cP[a]

    def step_value(k, S, q):
        x = root[k] + S
        ours = rev(x, q)
        theirs = rev(x + q, opp[k]) if opp[k] > 0 else 0.0
        return ours - theirs, ours

    # baseline under the model
    S = 0
    base_val = base_own = 0.0
    for k in range(len(steps)):
        v, o = step_value(k, S, sold[k])
        base_val += v
        base_own += o
        S += sold[k]
    # DP backwards: V[S] at step k = best value from step k with S sold so far
    Sgrid = np.arange(total + 1)
    V = np.full(total + 1, -1e18)
    own = np.zeros(total + 1)
    V[total] = 0.0
    for k in range(len(steps) - 1, -1, -1):
        newV = np.full(total + 1, -1e18)
        newO = np.zeros(total + 1)
        cap = int(cum_arr[k])
        for s in range(0, min(cap, total) + 1):
            qmax = cap - s
            qs = np.arange(0, qmax + 1)
            if k == len(steps) - 1:
                qs = np.array([total - s]) if total - s <= qmax else np.array([], dtype=int)
                if qs.size == 0:
                    continue
            elif nightly and steps[k] % 24 == 23:
                qs = np.array([qmax])
            x = root[k] + s
            ours = rev(np.full(qs.shape, x), qs)
            theirs = (rev(x + qs, np.full(qs.shape, opp[k])) if opp[k] > 0
                      else np.zeros(qs.shape))
            tot = ours - theirs + V[s + qs]
            j = int(np.argmax(tot))
            newV[s] = tot[j]
            newO[s] = ours[j] + own[s + qs[j]]
        V, own = newV, newO
    return base_val, float(V[0]), float(own[0]) - base_own, total


def job(args):
    record, start, nightly = args
    rows = trace(record)
    out = {"episode_id": record["episode_id"],
           "agent": {56571049: "A", 56582917: "L"}.get(record.get("submission")),
           "margin": record["rewards"]["us"] - record["rewards"]["them"], "items": {}}
    for item in ITEMS:
        b, o, own, units = solve(rows, item, start, nightly=nightly)
        out["items"][item] = {"base": b, "oracle": o, "gain": o - b,
                              "own_gain": own, "units": units}
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", type=int, default=600)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--nightly", action="store_true",
                    help="nothing may be held over a night")
    args = ap.parse_args()
    with Pool(args.workers) as pool:
        rows = pool.map(job, [(r, args.start, args.nightly) for r in records()])
    path = OUT / f"oracle_from_{args.start}{'_nightly' if args.nightly else ''}.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    print(f"saved {path.relative_to(ROOT)}")
    print(f"timing oracle from step {args.start}: gain in (our - their) revenue per game")
    for item in ITEMS:
        g = [r["items"][item]["gain"] for r in rows]
        og = [r["items"][item]["own_gain"] for r in rows]
        u = [r["items"][item]["units"] for r in rows]
        print(f"  {item:11s} mean {statistics.mean(g):+7.0f} median {statistics.median(g):+6.0f} "
              f"max {max(g):+7.0f}  own {statistics.mean(og):+6.0f}  units/game {statistics.mean(u):5.1f}")
    tot = [sum(r["items"][i]["gain"] for i in ITEMS) for r in rows]
    print(f"  {'ALL':11s} mean {statistics.mean(tot):+7.0f} median {statistics.median(tot):+6.0f} max {max(tot):+7.0f}")
    lost = [r for r in rows if r["margin"] < 0]
    flips = sum(1 for r, t in zip(rows, tot) if r["margin"] < 0 and r["margin"] + t > 0)
    print(f"  live losses {len(lost)}; flipped by the oracle gain: {flips}")


if __name__ == "__main__":
    main()
