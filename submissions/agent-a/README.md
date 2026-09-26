# Agent A (submitted 2026-09-26 06:13 UTC as "A NEWER MORE SOLID AGENT A")

**What it is:** a verbatim copy of a public Kaggle notebook's `main.py`:
tetsutani, *demand-preserving-turn-sale-timing* (Apache-2.0). Not one line of
the agent is ours. The author's own licence notices are kept in the file.

It sits at the end of the public "lineage": Ahmed Berat Ozer's V39 chassis,
yhay81's Shop Router action tapes (one of 41 routes, chosen on day 6 from the
first two shops), and about 40 reflex layers stacked on top by thomastschinkel,
aurax7, prvsiyan, Dmitrii Gluzdov, tetsutani and others. The last layer (IG)
closes holes in the market-order queue so sales execute earlier.

| | |
|---|---|
| file | `main.py`, 494,062 bytes, sha256 `e8ca9e7c00aa...` |
| entry point Kaggle runs | `ig_agent` (last callable in the file) |
| imports | standard library only |
| same code as | `nb_guru_master_v3` (byte-identical main.py) |

## What we did — selection and checking, not agent code

1. Pulled every public Kaggriculture notebook we could find, extracted the
   agent from each (23 notebooks; 17 runnable), scanned them for unsafe code,
   and verified each one's real entry point (several expose an inner layer as
   `agent`).
2. Ran them against each other and our own live submissions in the arena:
   728 games — this agent won 102 of 104; then a finals round of the eight
   strongest, 56 games each — it won 52 of 56.
3. Played it against an independent copy of itself: 10 of 12 exact ties, so a
   change to it can be measured against a clean "all draws" baseline.
4. Packaged the notebook's exact bytes (`tools/packaging/package_public.py`)
   and played 4 verification games with the file loaded the way Kaggle loads
   it: no errors, slowest turn 367 ms against the 60 s budget.

Our own changes go into **Agent L** (`rl/candidate_l.py`), which uses this
file unmodified as its base.
