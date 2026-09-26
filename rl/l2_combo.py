"""L2 combinations: stack the layers that beat L on their own, and test whether they add up.

Order, innermost (closest to the route) first:

    parent (Agent A, gate 120)
      -> fert   rl/l2_wheat_fert.py   fertilize young wheat with carried fertilizer (priced)
      -> feed   rl/l2_animals.py      drop FEEDs that provably buy nothing
      -> rt     rl/l2_wheat_rt.py     wheat round trip around the town's wheat draw (masks the parent)
      -> lot    rl/l2_outfarm.py      sell a premium lot whole instead of a few units a step
      -> dump   rl/l2_endgame.py      endgame trickle dump
      -> market_front (L's queue order)
      -> labour rl/l2_labour.py       in-place recycler for PASS / no-op turns
      -> shadow rl/l2_shadow.py       exact opponent shadow for copies of A
      -> safety rl/safety.py          never forfeit a game

Unit-command layers sit closest to the parent because they read its tape and
commands; order-size layers come after them; labour and the shadow wrap the
finished L like they did when tested alone.
"""

from rl.candidate_l import l_stack

ALL = ("fert", "feed", "rt", "lot", "dump", "labour", "shadow", "safety")


def combo(*names, shadow_mode="both"):
    names = set(names)
    unknown = names - set(ALL)
    if unknown:
        raise ValueError(f"unknown layers {unknown}")

    def inner(agent, env):
        if "fert" in names:
            from rl.l2_wheat_fert import fert_inner
            agent = fert_inner(agent, env)
        if "feed" in names:
            from rl.l2_animals import an_wrap
            agent = an_wrap(agent, env, {})
        if "rt" in names:
            from rl.l2_wheat_rt import rt_inner
            agent = rt_inner(agent, env)
        if "lot" in names:
            from rl.l2_outfarm import lot_wrap
            agent = lot_wrap(agent, env)
        if "dump" in names:
            from rl.l2_endgame import trickle_dump
            agent = trickle_dump(agent)
        return agent

    def outer(agent):
        if "labour" in names:
            from rl.l2_labour import lb_wrap
            agent = lb_wrap(agent)
        if "shadow" in names:
            from rl.l2_shadow import shadow_wrap
            agent = shadow_wrap(agent, reorder=shadow_mode in ("both", "reorder"),
                                early=shadow_mode in ("both", "early"))
        if "safety" in names:
            from rl.safety import sf_wrap
            agent = sf_wrap(agent, name="L2")
        return agent

    return l_stack(inner=inner, outer=outer)


def lot_dump():
    return combo("lot", "dump")


def lot_rt():
    return combo("lot", "rt")


def lot_dump_rt():
    return combo("lot", "dump", "rt")


def core():                     # the three big market layers + the small safe ones
    return combo("fert", "feed", "rt", "lot", "dump", "labour")


def core_lot():                 # same without the endgame dump (in case lot covers it)
    return combo("fert", "feed", "rt", "lot", "labour")


def full():                     # everything, with the shadow and the safety guard
    return combo(*ALL)
