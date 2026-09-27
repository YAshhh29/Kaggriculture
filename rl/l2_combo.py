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


def combo(*names, shadow_mode="both", shadow_programs=("A",), lot_opts=None,
          shadow_opts=None):
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
            agent = lot_wrap(agent, env, **(lot_opts or {}))
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
            agent = shadow_wrap(agent, programs=tuple(shadow_programs),
                                reorder=shadow_mode in ("both", "reorder"),
                                early=shadow_mode in ("both", "early"),
                                **(shadow_opts or {}))
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


# What ships as L2: everything except the endgame dump, which is inert once the
# lot layer runs (dump_units 0 in every combined game) and whose module defines
# its own `projected_shed`, a name the parent also uses.
# Round 3 (seeds 130-159): the wheat-fertilizer layer is a wash against A and L
# (better in 30/60 and 31/60 games) with a worse tail, so it does not ship.
SHIP = ("feed", "rt", "lot", "labour", "shadow", "safety")


def ship():
    return combo(*SHIP)


def ship_lib():
    """L2 with the shadow modelling the whole public library, not only A."""
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP, shadow_programs=SH_LIBRARY)


def l3_lot_rival():
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP, shadow_programs=SH_LIBRARY, lot_opts={"rival_only": True})


def l3_lot_similar():
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP, shadow_programs=SH_LIBRARY, lot_opts={"similar": 0.5})


# L4 candidate: L3's stack with the library extended by the newer public programs
# that real ladder opponents were measured to run (tools/analysis/l2_shadow_sync.py
# on A's 158 live games: whole-game or past-day-16 syncs).
NEW_LIBRARY = ("nb_statma_herd_safe_sale_window_submit", "nb_statma_herd_safe_sale_window_race_ca20",
               "nb_ahmedberatoz_v56_smarter_seeds_and_fertilizer",
               "nb_arsgorynich_order_book_v3_response_improvement",
               "nb_ahmedberatoz_v57_funding_order_invariant",
               "nb_ahmedberatoz_v54_productive_wheat_and_patient")


def ship_lib4():
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP, shadow_programs=tuple(SH_LIBRARY) + NEW_LIBRARY)


# L4: no lot layer. With the library shadow locked on an exact copy, the lot
# layer's whole-lot dumps get in the way of the shadow's own ahead-of-the-rival
# sales (vs every library program, higher mean and worst game without it), and
# on real ladder games it is at best neutral (A's 158: 144 wins without vs 142
# with; L's 116: same wins, +317 a game without).
SHIP4 = ("feed", "rt", "labour", "shadow", "safety")


def l4():
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP4, shadow_programs=tuple(SH_LIBRARY) + NEW_LIBRARY,
                 shadow_opts={"early_when_agree": True})
