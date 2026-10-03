# stack/ — the final agent

The agents that finished the competition (N10 and N11) are a route-following
base engine with **thirteen layers of my own design** around it. Every layer
is a function that takes an agent and returns a new one: it sees the
observation, lets the agent below decide, and may adjust the action on the way
back out.

![How the final agent decides each turn](../docs/assets/architecture.svg)

The base engine is *The 2965 Master Hybrid Engine* by haideptry, open-source
code from the competition's public notebooks (Apache-2.0). It follows one of
41 recorded 30-day routes, picked on day 6 from the town's first two shops,
and switches to a shared end-game route on day 27.
It is not committed here; `tools/data/extract_notebook_agents.py` recovers it
from its notebook into `rl/public/`.

## Layers in the final agent (outermost first)

| Layer | Since | Kind | What it does |
|---|---|---|---|
| [`safety.py`](safety.py) | L | Guard | Never lets an exception escape, repairs malformed actions, keeps a time budget other layers consult |
| [`own_book.py`](own_book.py) | N11 | Opponent model | Corrects the base engine's record of our own sales, so its estimate of the rival's sales is not inflated by ours |
| [`shed_guard.py`](shed_guard.py) | N10 | Guard | On a day's last hour, cuts purchases and sells the excess so the day-end drop into the 100-unit shed destroys nothing |
| [`place_guard.py`](place_guard.py) | N7 | Guard | Builds the missing pasture or coop before an animal is placed |
| [`draw_last.py`](draw_last.py) | N4 | Market | Detects riders around our wheat purchase at the town draw and moves it to the last slot |
| [`tomato_annex.py`](tomato_annex.py) | N3 | Farm | A five-tile tomato annex with its own hands, only when three tomato shops are open and the town is short |
| [`m_sell.py`](m_sell.py) | M | Opponent model | Learns the rival's selling hour during the game and sells our lot first once beaten to one |
| [`l2_shadow.py`](l2_shadow.py) | L3 | Opponent model | Runs 18 public programs in lockstep with the game; when one reproduces the rival's moves, reorders and advances our sales against its known schedule |
| [`l2_labour.py`](l2_labour.py) | L2 | Farm | Gives a unit that would idle a useful command on its own tile (care, water, collect) without moving it off its route |
| [`market_front.py`](market_front.py) | L | Market | The market settles orders slot by slot; puts the orders with the largest price damage into the earliest slots |
| [`l2_outfarm.py`](l2_outfarm.py) (`lot`) | L2 | Market | Sells a whole lot at once while racing the rival for the same product |
| [`l2_wheat_rt.py`](l2_wheat_rt.py) | L2 | Market | The wheat round trip: buys just before the town eats wheat, sells the same units back a turn later |
| [`l2_animals.py`](l2_animals.py) | L2 | Farm | Drops FEED orders that provably buy nothing |

The composition for every agent from L to N12 is in
[`l2_combo.py`](l2_combo.py) (`n10()`, `n11()`, `n12()` …), on top of
[`candidate_l.py`](candidate_l.py), which loads a base program exactly the way
Kaggle loads a submission. The packager
([`tools/packaging/package_l3.py`](../tools/packaging/package_l3.py)) embeds
each layer's source into one standard-library-only file.

## Experiments kept for the record

Measured and not shipped (each module's docstring has the result):
`l2_carrot.py`, `l2_fert.py`, `l2_wheat_fert.py`, `l2_endgame.py`,
`l2_race.py`, `se_project.py`, `fert_runner.py`, `fert_worker.py`,
`n_crops.py`. Test harness variants: `l2_null.py` (must tie the agent it
wraps), `l2_safe.py`, `l2_ablate.py` (drops one layer at a time).

[`pub_agents.py`](pub_agents.py) and [`public_agents.py`](public_agents.py)
load public programs, and my older packages, as opponents for evaluation.

## Rebuild a final package

```powershell
./.conda/python.exe -m tools.packaging.build_final N11            # -> build/N11/main.py
./.conda/python.exe -m tools.packaging.build_final N10 --verify   # + 8 games vs the local factory
```
