"""Put the same units on the market across many more turns.

Measured on Candidate E against Candidate F, same opponent tape, same
seed: E asks for 1,053 units it actually holds and F asks for 1,127 --
practically the same volume. E puts them through on **88 turns** and F on
**254**. E earns more for them (107,886 against 74,896) because it sells
into a market it has not yet spoiled, and loses anyway, because the
opponent sells *its* milk at an average of 254 coins in E's games against
72 in F's.

Price is a function of one shared inventory and the town eats that
inventory back down continuously. A glut delivered in eighty-eight lumps
is a glut the town has time to digest between lumps; the same units spread
over three times as many turns hold the price down instead of denting it.
And a held-down price is not only cheaper for the opponent to sell into --
it starves the cash its own `BUY_ANIMAL` orders are clamped against, which
is how an agent that leaves prices high ends up funding a bigger rival
farm (10.8ac).

This is the opposite of `candidates/demand_sales.py`, which caps a turn's sales
against what the town can absorb and therefore *reduces* both volume and
occupancy. Here nothing is withheld across the game: every unit still goes
out, in smaller pieces, on more turns.

Two guards, for the same reasons the closing rules exist elsewhere:

* the closing days sell without limit, because reward is the money on the
  books at step 720 and a trickle that has not finished is a loss;
* a shed close to its 100-unit cap sells without limit, because the
  end-of-day drop discards the overflow.

**Not yet wired into any shipped agent.** Whether spreading pays is a
separate question from whether the time profile differs, and this project
has repeatedly answered the first by assuming the second.
"""

from __future__ import annotations

from typing import Any

from rl.runtime import AgentAction, Baseline, clone_action

TURNS_PER_DAY = 24
LIVESTOCK = ("COW", "SHEEP", "GOOSE")


def _shed(observation: dict[str, Any]) -> dict[str, int]:
    private = observation.get("private") or {}
    return {str(k): int(v) for k, v in (private.get("shed") or {}).items()}


def trickle_orders(
    observation: dict[str, Any],
    orders: list[list[Any]],
    *,
    per_turn: int,
    closing_day: int,
    shed_pressure: int,
) -> list[list[Any]]:
    """Trim each SELL to `per_turn` units, leaving the rest for later turns.

    Nothing is dropped: the shed keeps what is not sold now and the next
    turn's order draws on it again, so the same stock reaches the market
    over more turns rather than in one lump.
    """
    if per_turn <= 0:
        return orders
    step = int(observation.get("step", 0))
    if step // TURNS_PER_DAY >= closing_day:
        return orders
    if sum(_shed(observation).values()) >= shed_pressure:
        return orders

    out: list[list[Any]] = []
    for order in orders:
        if not (isinstance(order, list) and len(order) >= 3
                and order[0] == "SELL"):
            out.append(order)
            continue
        item = str(order[1])
        if item in LIVESTOCK:
            out.append(order)
            continue
        try:
            quantity = int(order[2])
        except (TypeError, ValueError):
            out.append(order)
            continue
        if quantity > 0:
            out.append(["SELL", item, min(quantity, per_turn)])
    return out


def build_trickle_agent(
    baseline: Baseline,
    *,
    per_turn: int = 4,
    closing_day: int = 28,
    shed_pressure: int = 85,
) -> Baseline:
    """Wrap an agent so it meters each good onto the market."""

    def decide(observation: dict[str, Any]) -> AgentAction:
        action = clone_action(baseline(observation))
        action["market"] = trickle_orders(
            observation,
            list(action["market"]),
            per_turn=per_turn,
            closing_day=closing_day,
            shed_pressure=shed_pressure,
        )
        return action

    return decide
