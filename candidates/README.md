# candidates/ — agents A to M and their parts

Every agent built between 31 August and 27 September, before the final layered
stack in [`stack/`](../stack/README.md). Each was measured on real ladder games
and either submitted, kept as a component, or rejected. The module docstrings
record the evidence; [`docs/research/GOAL.md`](../docs/research/GOAL.md) is the
running research log behind them.

## The agents

| Module | Agent | Idea |
|---|---|---|
| [`candidate_a.py`](candidate_a.py) | A | Follows a recorded elite calendar, with guarded recovery when the game drifts from it and live end-game liquidation |
| [`candidate_b.py`](candidate_b.py) | B | A plus a market residual: sequential affordability (sell first to fund a same-turn purchase) |
| [`candidate_c.py`](candidate_c.py), [`candidate_c2.py`](candidate_c2.py) | C, C2 | A portfolio of complete recorded routes, switching on public state at block boundaries |
| [`candidate_d.py`](candidate_d.py) | D | The route chosen by searching 245 recorded tapes on the real top 500, not by the player's rank |
| [`candidate_e.py`](candidate_e.py) | E | An agent that plans from scratch with a marginal-value model of what this town wants |
| [`candidate_f.py`](candidate_f.py) | F | D's route with a demand engine that sells at the rate the town absorbs |
| [`candidate_g.py`](candidate_g.py) | G | A farm built from the rules around the goods whose price never falls |
| [`candidate_h_package.py`](candidate_h_package.py), [`candidate_h2_package.py`](candidate_h2_package.py), [`candidate_h_demand.py`](candidate_h_demand.py), [`candidate_h3.py`](candidate_h3.py) | H, H2, H3 | A route-following base with my market-demand layer and order sequencing on top |
| [`candidate_i.py`](candidate_i.py) | I | A route follower driven by recorded top-of-ladder routes |
| [`candidate_j.py`](candidate_j.py), [`candidate_j2.py`](candidate_j2.py) | J, J2 | A live scheduler: every task is priced in coins per worker-turn |
| [`candidate_k.py`](candidate_k.py), [`candidate_k2.py`](candidate_k2.py), [`candidate_k_auction.py`](candidate_k_auction.py) | K, K2 | H2's farm sold at J's prices; K2 overrides the route only where it can prove a gain |

Agents L and M, and the N series, live in [`stack/`](../stack/README.md).

## Components

| Module | What it does |
|---|---|
| [`market.py`](market.py) | What a unit will really fetch, given everything already sold this turn |
| [`economics.py`](economics.py) | Marginal value of a farm action, in coins |
| [`demand.py`](demand.py), [`demand_sales.py`](demand_sales.py) | Read each product's town demand from the observation; sell at the rate it is eaten |
| [`denial.py`](denial.py) | Price a sale by what it costs the opponent too |
| [`sell_floor.py`](sell_floor.py), [`sell_gate.py`](sell_gate.py), [`trickle.py`](trickle.py) | Sale timing experiments: hold at the floor, hold in a glut, spread a lot over many turns |
| [`route_portfolio.py`](route_portfolio.py), [`macro_plan.py`](macro_plan.py), [`handover.py`](handover.py) | Switch between recorded routes; follow the build order 204 elite games agree on; open with a route, finish with the economics |
| [`crew_extra.py`](crew_extra.py), [`extra_hands.py`](extra_hands.py), [`idle_rescue.py`](idle_rescue.py), [`idle_work.py`](idle_work.py) | Give a recorded route more workers, or turn its idle turns into work |
| [`herd_swap.py`](herd_swap.py), [`expansion.py`](expansion.py) | Steer a recorded route's herd toward local demand; buy a fourth quadrant with idle cash |
| [`submitted.py`](submitted.py), [`g_variant.py`](g_variant.py), [`j_variant.py`](j_variant.py), [`candidate_g_inspector.py`](candidate_g_inspector.py), [`candidate_hd.py`](candidate_hd.py) | Load packaged submissions by name; constant sweeps; G's move-by-move inspector; an alternative H build |

The packaged form of each submitted agent is in
[`submissions/`](../submissions/README.md).
