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

from pathlib import Path

from rl.candidate_l import l_stack

ROOT_DIR = Path(__file__).resolve().parents[1]

ALL = ("fert", "feed", "crop", "rt", "lot", "dump", "labour", "shadow", "msell", "race", "annex",
       "runner", "dlast", "place", "safety", "shed", "book")


def combo(*names, shadow_mode="both", shadow_programs=("A",), lot_opts=None,
          shadow_opts=None, gate=120, rt_opts=None, race_opts=None, msell_opts=None,
          crop_opts=None, parent_file=None, env_patch=None, parent_patches=None,
          annex_opts=None, mf_opts=None, dlast_opts=None, runner_opts=None, book_opts=None):
    names = set(names)
    unknown = names - set(ALL)
    if unknown:
        raise ValueError(f"unknown layers {unknown}")

    book = {}

    def inner(agent, env):
        if "book" in names:           # N11: remember the parent's own sales (innermost)
            from rl.own_book import ob_record
            agent = book["rec"] = ob_record(agent)
            book["env"] = env
        if env_patch:                 # constants of the parent read at call time (N3)
            env.update(env_patch)
        if "fert" in names:
            from rl.l2_wheat_fert import fert_inner
            agent = fert_inner(agent, env)
        if "feed" in names:
            from rl.l2_animals import an_wrap
            agent = an_wrap(agent, env, {})
        if "crop" in names:
            from rl.n_crops import n_crops_inner
            agent = n_crops_inner(agent, env, **(crop_opts or {}))
        if "rt" in names:
            from rl.l2_wheat_rt import rt_inner
            agent = rt_inner(agent, env, **(rt_opts or {}))
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
        if "msell" in names:
            from rl.m_sell import m_sell_wrap
            agent = m_sell_wrap(agent, **(msell_opts or {}))
        if "race" in names:
            from rl.l2_race import race_wrap
            agent = race_wrap(agent, **(race_opts or {}))
        if "annex" in names:
            from rl.tomato_annex import ta_wrap
            agent = ta_wrap(agent, **(annex_opts or {}))
        if "runner" in names:
            from rl.fert_runner import fr_wrap
            agent = fr_wrap(agent, **(runner_opts or {}))
        if "dlast" in names:
            from rl.draw_last import dl_wrap
            agent = dl_wrap(agent, **(dlast_opts or {}))
        if "place" in names:
            from rl.place_guard import pg_wrap
            agent = pg_wrap(agent)
        if "shed" in names:
            from rl.shed_guard import sg_wrap
            agent = sg_wrap(agent)
        if "book" in names:
            from rl.own_book import ob_wrap
            agent = ob_wrap(agent, book["env"], book["rec"], **(book_opts or {}))
        if "safety" in names:
            from rl.safety import sf_wrap
            agent = sf_wrap(agent, name="L2")
        return agent

    return l_stack(inner=inner, outer=outer, gate=gate, parent_file=parent_file,
                   parent_patches=parent_patches, mf_opts=mf_opts)


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


# L4b: L3 as tested (lot layer kept) + the 14-program library + the agree rule.
# Between near-copies that are not in each other's library the lot layer wins
# the selling race (L3 beat L4-without-lot by 3.6k in a direct game), so it stays.
def l4b():
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP, shadow_programs=tuple(SH_LIBRARY) + NEW_LIBRARY,
                 shadow_opts={"early_when_agree": True})


def l4b_origgate():
    """L4 with A's original V219 gate (three tomato shops) instead of L's relaxed one."""
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP, shadow_programs=tuple(SH_LIBRARY) + NEW_LIBRARY,
                 shadow_opts={"early_when_agree": True}, gate=None)


# L4c: L4 without the wheat round trip. In real ladder games the round trip can
# hand money to an opponent that trades wheat on the same steps (live episode
# 114070787 vs tomfng: with it -18,053, without it +1,124; the opponent gained
# ~8.8k from our trades).
SHIP4C = ("feed", "lot", "labour", "shadow", "safety")


def l4c():
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP4C, shadow_programs=tuple(SH_LIBRARY) + NEW_LIBRARY,
                 shadow_opts={"early_when_agree": True})


# L4d: L4 whose round trip prices each trip against the opponent's recent
# wheat flow. Against tomfng the opponent sold wheat into every trip window
# (the engine quotes both players the same unit price, so their sales rode on
# our purchase and our sale landed on their supply); against most opponents
# the windows are empty and L4d trades exactly like L4.
def l4d(window=8):
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP, shadow_programs=tuple(SH_LIBRARY) + NEW_LIBRARY,
                 shadow_opts={"early_when_agree": True}, rt_opts={"flow_window": window})


def l4d4():
    return l4d(4)


def l4d16():
    return l4d(16)


def l4e(window=8):
    """L4d pricing each trip against the median recent window (one-off sales ignored)."""
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP, shadow_programs=tuple(SH_LIBRARY) + NEW_LIBRARY,
                 shadow_opts={"early_when_agree": True},
                 rt_opts={"flow_window": window, "flow_stat": "median"})


# L5 candidates: L4 + the endgame selling race (rl/l2_race.py), outside the
# shadow so it sees our final orders. `rt` picks the round-trip pricing.
def l5(rt=None, **race):
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP, "race", shadow_programs=tuple(SH_LIBRARY) + NEW_LIBRARY,
                 shadow_opts={"early_when_agree": True}, rt_opts=rt, race_opts=race)


def l5_d24():
    return l5(first_step=576)


def l5e():
    return l5(rt={"flow_window": 8, "flow_stat": "median"})


# Public programs posted 2026-09-26/27 that L4e loses to in seat 0 (by ~250):
# near-copies of the herd-safe lineage. In the library, the shadow models them.
NEW_LIBRARY_0927 = ("nb_haodou092_harvest_ledger", "nb_dmitriigluzd_7_turn_rescue_historical_lb_2800",
                    "nb_leoprovorov_lucky_boy_best_version_score_2552_1", "nb_arsgorynich_v40_challenger",
                    "nb_haideptry_2950_peak_farm")


def l5lib():
    """L4e with the 2026-09-27 programs added to the shadow library (19 programs)."""
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP, shadow_programs=tuple(SH_LIBRARY) + NEW_LIBRARY + NEW_LIBRARY_0927,
                 shadow_opts={"early_when_agree": True},
                 rt_opts={"flow_window": 8, "flow_stat": "median"})


def l5h():
    """L4e + harvest-ledger only: the one 2026-09-27 program our ladder opponents run
    (whole-game sync in 16 of 163 recent L2/L3 games)."""
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP, shadow_programs=tuple(SH_LIBRARY) + NEW_LIBRARY + ("nb_haodou092_harvest_ledger",),
                 shadow_opts={"early_when_agree": True},
                 rt_opts={"flow_window": 8, "flow_stat": "median"})


# ---- Agent M: our own decision layers, starting on L5's body ----------------
M_LIBRARY_EXTRA = ("nb_haodou092_harvest_ledger",)


def m1(**msell):
    """M part 1 = L5 + the in-game opponent-clock seller (rl/m_sell.py)."""
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP, "msell", shadow_programs=tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA,
                 shadow_opts={"early_when_agree": True},
                 rt_opts={"flow_window": 8, "flow_stat": "median"}, msell_opts=msell)


def m1_lead0():
    return m1(lead=0)


def m2():
    """M part 1 with the value check: race only when their lot outweighs what the
    town eats before the hour we usually sell."""
    return m1(value_check=True)


def m3():
    """M1, racing only goods our own stack sells as whole lots."""
    return m1(require_own_lot=True)


def m4():
    """M1, racing only goods the opponent recently sold mostly in whole lots."""
    return m1(pace_check=0.5)


def m5():
    """M1, racing a good only after the opponent has sold a lot of it while we held one."""
    return m1(after_beaten=True)


def m7():
    """M1, racing only when the opponent's recent lot came before our own usual hour."""
    return m1(before_us=True)


def m8():
    """M5, where being beaten on one good starts races on every good."""
    return m1(after_beaten=True, beaten_any=True)


def m9():
    """M8 without wool races: one shop type buys wool, so a raced lot walks its
    price down steeply (the largest same-step leak left after M5)."""
    return m1(after_beaten=True, beaten_any=True,
              items=("CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK"))


# 2026-09-28: tetsutani's own notebook now ships harvest-ledger's program (they
# tie to the coin, seats swapped); a second variant, haideptry's 2965 master
# hybrid, plays 5 of L4's 80 opponents all game and 9 more past day 16.
LIBRARY_0928 = ("nb_haodou092_harvest_ledger", "nb_haideptry_the_2965_master_hybrid_engine")


def l6():
    """L5 + the 2965 master hybrid in the shadow library (16 programs)."""
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP, shadow_programs=tuple(SH_LIBRARY) + NEW_LIBRARY + LIBRARY_0928,
                 shadow_opts={"early_when_agree": True},
                 rt_opts={"flow_window": 8, "flow_stat": "median"})


def m10():
    """M8 (race every good once beaten on one) + the 2965 master hybrid in the library."""
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP, "msell", shadow_programs=tuple(SH_LIBRARY) + NEW_LIBRARY + LIBRARY_0928,
                 shadow_opts={"early_when_agree": True},
                 rt_opts={"flow_window": 8, "flow_stat": "median"},
                 msell_opts={"after_beaten": True, "beaten_any": True})


# ---- Agent N: our own crop decisions on M's stack ----------------------------
def n1(**crop):
    """N part 1 = M (M8) + the gated late strawberry batch (rl/n_crops.py)."""
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP, "msell", "crop", shadow_programs=tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA,
                 shadow_opts={"early_when_agree": True},
                 rt_opts={"flow_window": 8, "flow_stat": "median"},
                 msell_opts={"after_beaten": True, "beaten_any": True}, crop_opts=crop)


def n1_all():
    """N1 with the gate open in every town (to measure the swap itself)."""
    return n1(min_price=0, min_shops=0)


def m11():
    """M8 + the shadow's same-turn early sale against programs it knows (early_now)."""
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP, "msell", shadow_programs=tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts={"flow_window": 8, "flow_stat": "median"},
                 msell_opts={"after_beaten": True, "beaten_any": True})


# ---- Agent N: our whole decision stack on the strongest public farm plan -----
# 2026-09-28: every public program was screened against A (2 seeds x 2 seats);
# only tetsutani's new version (= harvest-ledger) and haideptry's 2965 master
# hybrid beat it (3/4, +924 and +978 a game). Our agents all farm with A (the
# old version), and the 2300-2400 band upgraded to the new one on 9-27: L3 won
# 86% there on 9-27, L5 49% and M 58% on 9-28. Both new programs keep A's
# chassis (_IMPL, FarmView, projected_shed, future_sells), so every layer fits.
HARVEST_LEDGER = "rl/public/nb_haodou092_harvest_ledger.py"
MASTER_2965 = "rl/public/nb_haideptry_the_2965_master_hybrid_engine.py"


def _n(parent, **extra):
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP, "msell", shadow_programs=tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts={"flow_window": 8, "flow_stat": "median"},
                 msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / parent), **extra)


def n2():
    """N = M2's decision stack on harvest-ledger's farm plan (its own tomato gate)."""
    return _n(HARVEST_LEDGER)


def n2m():
    """N on the 2965 master hybrid's farm plan."""
    return _n(MASTER_2965)


def hl_plain():
    """harvest-ledger with only the queue-order layer (L's first layer), for reference."""
    return l_stack_on(HARVEST_LEDGER)


def l_stack_on(parent):
    from rl.candidate_l import l_stack
    return l_stack(gate=None, parent_file=str(ROOT_DIR / parent))


# ---- Agent N3: N's layers re-tested on the new plan, one removed at a time ----
def _n_without(layer, parent=MASTER_2965):
    from rl.l2_shadow import SH_LIBRARY
    names = [x for x in SHIP if x != layer] + ["msell"]
    return combo(*names, shadow_programs=tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts={"flow_window": 8, "flow_stat": "median"},
                 msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / parent))


def n_no_lot():
    return _n_without("lot")


def n_no_rt():
    return _n_without("rt")


def n_no_feed():
    return _n_without("feed")


def n_no_labour():
    return _n_without("labour")


def n_no_msell():
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP, shadow_programs=tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts={"flow_window": 8, "flow_stat": "median"},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965))



# N3: the 2965 master starts its day-18 tomato project (buy SE, 20 tiles of
# tomatoes) only when its forecast of the 80 units reaches 9,000 coins. In 7 of
# N's 21 live losses to 2400+ opponents the rival started it and we did not
# (planted on day 20: Jun_value 78 vs 58, Utkarsh 78 vs 68, Hozuma 68 vs 58).
def n3_rev(threshold):
    return _n(MASTER_2965, env_patch={"_CXTB_MIN_REVENUE": threshold})


def n3r7():
    return n3_rev(7000)


def n3r5():
    return n3_rev(5000)


# N3: N with the shadow library extended by the programs N's own live
# opponents play (filled in from tools/analysis/sync_presence on N/N2's games).
N3_EXTRA = ("nb_haideptry_the_2965_master_hybrid_engine",)


def n3(extra=None):
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(extra if extra is not None else N3_EXTRA)
    return combo(*SHIP, "msell", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts={"flow_window": 8, "flow_stat": "median"},
                 msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965))


# N3 round-trip size: 2400+ rivals trade more wheat around the town's draw
# (BorisV bought 3,832 units from day 14 to our 2,991; Knight of Favonius
# netted +14,833 on wheat to our +11,076). Our trip is capped at 60 units.
def _n3_rt(q_max, margin=10):
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA)
    return combo(*SHIP, "msell", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts={"flow_window": 8, "flow_stat": "median", "q_max": q_max, "room_margin": margin},
                 msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965))


def n3q90():
    return _n3_rt(90)


def n3q120():
    return _n3_rt(120)


def n3q():
    """N3 with 90-unit round trips only while the opponent trades no wheat
    around the draw (last 8 windows all quiet)."""
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA)
    return combo(*SHIP, "msell", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts={"flow_window": 8, "flow_stat": "median", "q_quiet": 90},
                 msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965))


def n3t():
    """N3 + the pre-draw trap guard on the wheat round trip."""
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA)
    return combo(*SHIP, "msell", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts={"flow_window": 8, "flow_stat": "median", "trap_guard": 20},
                 msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965))


def n3tf():
    """N3t + the parent's wheat fertilizing from day 10 (V9_FERT_FIRST_DAY, 14 in the
    plan): N waters age-1 wheat, which yields nothing, in 82% of its day 9-11 lives;
    V9_FERT swaps that watering for a fertilize when the unit carries fertilizer."""
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA)
    return combo(*SHIP, "msell", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts={"flow_window": 8, "flow_stat": "median", "trap_guard": 20},
                 msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965),
                 env_patch={"V9_FERT_FIRST_DAY": 10})



# N3: the plan's fertilizer couriers (R51) hire only when the extra crop value is
# at least 1.5 x (fertilizer bought + the day's hire) + 50; N fertilizes 22% of its
# wheat lives against the top teams' 59-74% (5.4 units a fertilized life vs 2.7).
R51_LOOSE = [("if value<1.5*cost+50 or farm['money']<total_cost+cost+3000:break",
              "if value<1.15*cost+20 or farm['money']<total_cost+cost+3000:break")]


def n3tr():
    """N3t with the fertilizer couriers' bar lowered to 1.15 x cost + 20."""
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA)
    return combo(*SHIP, "msell", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts={"flow_window": 8, "flow_stat": "median", "trap_guard": 20},
                 msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965), parent_patches=R51_LOOSE)



def _n3t_with(extra=(), **kw):
    """N3t (the trap guard) plus extra layers / options."""
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA)
    return combo(*SHIP, "msell", *extra, shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts={"flow_window": 8, "flow_stat": "median", "trap_guard": 20},
                 msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965), **kw)


def n3ta():
    """N3t + the tomato annex: 5 more tomato tiles (SE row 7) beside the parent's
    day-18 project, on the annex's own hands (rl/tomato_annex.py)."""
    return _n3t_with(("annex",))


def n3ta10():
    """N3t + a 10-tile tomato annex (SE rows 7-8)."""
    return _n3t_with(("annex",), annex_opts={"rows": (7, 8)})



# The plan's V233 six-sheep crew collects fertilizer on every tile before it
# carries the wool home, so its wool sells 3 turns after a mirror rival's
# (rhythm master: 6,018 coins on one game). Collect fertilizer only once no
# wool is carried and no target still holds yield. Measured by the body-knobs
# study on the 8 V233 games of N and N2: +11,994 (2 losses flipped) and +12,541.
WOOL_FIRST = [(
    "            elif tile['fertilizer_available']:command=['COLLECT_FERTILIZER']\n"
    "        if command:tasks.append((abs(pos[0]-x)+abs(pos[1]-y),targets.index(target),target,command))",
    "            elif tile['fertilizer_available'] and not inv.get('WOOL',0) and not any(isinstance(farm['tiles'][_ty][_tx],dict) and farm['tiles'][_ty][_tx].get('yield_units') for _tx,_ty in targets):command=['COLLECT_FERTILIZER']\n"
    "        if command:tasks.append((abs(pos[0]-x)+abs(pos[1]-y),targets.index(target),target,command))")]

# market_front may move the parent's fertilizer purchase ahead of its sale; with
# the shed near full the purchase fills short and a tomato tile goes unfertilized
# on day 27 (78 tomatoes to the mirror's 80 in 16 of 20 games). +4,064 over 24.
MF_FERT = {"sell_first": ("FERTILIZER",)}


def n3tw():
    """N3t + the V233 wool-first crew."""
    return _n3t_with(parent_patches=WOOL_FIRST)


def n3twf():
    """N3t + wool-first + fertilizer SELL before BUY in market_front."""
    return _n3t_with(parent_patches=WOOL_FIRST, mf_opts=MF_FERT)


ANNEX_GATE = {"min_tomato_shops": 3, "min_shortage": 140}


def n3twfa():
    """N3twf + the gated tomato annex (5 tiles)."""
    return _n3t_with(("annex",), parent_patches=WOOL_FIRST, mf_opts=MF_FERT, annex_opts=dict(ANNEX_GATE))


def n3ta_gated():
    """N3t + the gated tomato annex (5 tiles)."""
    return _n3t_with(("annex",), annex_opts=dict(ANNEX_GATE))


def n3twfa10():
    """N3twf + the gated tomato annex on 10 tiles (SE rows 7-8)."""
    return _n3t_with(("annex",), parent_patches=WOOL_FIRST, mf_opts=MF_FERT,
                     annex_opts=dict(ANNEX_GATE, rows=(7, 8)))



def n4d(**dl):
    """N3 + our draw-step wheat purchases settled last (rl/draw_last.py)."""
    return _n3t_with(("annex", "dlast"), parent_patches=WOOL_FIRST, mf_opts=MF_FERT,
                     annex_opts=dict(ANNEX_GATE), dlast_opts=dl)


def n4d9():
    """draw_last with padding: the purchase settles in slot 9."""
    return n4d(pad=True)


def n4d1():
    """draw_last without padding: last in our own queue."""
    return n4d(pad=False)


def _n4(dlast=None, **rt_extra):
    """N3 + optional draw_last + round-trip options (N4 candidates)."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20}
    rt.update(rt_extra)
    extra = ("annex", "dlast") if dlast is not None else ("annex",)
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA)
    return combo(*SHIP, "msell", *extra, shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965), parent_patches=WOOL_FIRST,
                 mf_opts=MF_FERT, annex_opts=dict(ANNEX_GATE), dlast_opts=dlast)


def n4L():
    """N3 + lockstep trip sizing (purchases interleaved with the rival's)."""
    return _n4(lockstep=1)


def n4dL():
    """N3 + draw_last (slot 9) + lockstep sizing with our purchase after theirs."""
    return _n4(dlast={"pad": True}, lockstep=1, lock_after=True)


def n4r():
    """N3 + draw_last only against a detected rider (exact cost reconciliation)."""
    return _n4(dlast={"pad": True, "detect": True})


def n4rL():
    """n4r + lockstep trip sizing against honest same-step round-trippers."""
    return _n4(dlast={"pad": True, "detect": True}, lockstep=1)


def _n4x(dlast=None, env_patch=None, extra=(), annex=None, runner=None, **rt_extra):
    """N4 (N3 + adaptive draw_last) with optional extra layers / parent constants."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20}
    rt.update(rt_extra)
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA)
    return combo(*SHIP, "msell", "annex", "dlast", *extra, shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965), parent_patches=WOOL_FIRST,
                 mf_opts=MF_FERT, annex_opts=dict(annex or ANNEX_GATE),
                 dlast_opts=dict(dlast or {"pad": True, "detect": True}), env_patch=env_patch,
                 runner_opts=runner)


def n4f():
    """N4 + the parent's carried-fertilizer wheat layer from day 10 (V9_FERT_FIRST_DAY)."""
    return _n4x(env_patch={"V9_FERT_FIRST_DAY": 10})


def n4():
    """Agent N4 as packaged (submissions/candidate-n4): N3 + adaptive draw_last."""
    return _n4x()



def n4fr():
    """N4 + the fertilizer runner (rl/fert_runner.py)."""
    return _n4x(extra=("runner",))


def n4hl():
    """N4 on harvest-ledger's farm plan (N2's base) instead of the 2965 master's."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20}
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA)
    return combo(*SHIP, "msell", "annex", "dlast", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / HARVEST_LEDGER), parent_patches=WOOL_FIRST,
                 mf_opts=MF_FERT, annex_opts=dict(ANNEX_GATE),
                 dlast_opts={"pad": True, "detect": True})


# The 3000-rated teams keep 7-11 geese; against the top 500 our lost games are
# -6.5k on eggs a game (3.4k to 10.0k), while milk and wool are even. The egg
# book barely falls with supply (base 50, log above target) where milk and wool
# crash when both farms sell them. The plan converts the tape's geese into
# sheep or cows in yarn / milk towns (v9 HERD) and by expected value (HERD2).
KEEP_GEESE = {"V9_HERD_MIN_WOOL": 10 ** 9, "V9_HERD_MIN_MILK": 10 ** 9, "_HD2_MIN_GAIN": 10 ** 12}


def n4g1():
    """N4 keeping the tape's geese (v9 HERD and HERD2 swaps off)."""
    return _n4x(env_patch=dict(KEEP_GEESE))


def n4g2():
    """N4g1 + COWSWAP turning cows into geese whenever geese are worth as much."""
    return _n4x(env_patch=dict(KEEP_GEESE, _CS_RATIO=1.0, _CS_MIN_GAIN=0.0))


# 2026-09-29 library refresh: 11 new public programs; only this one played one of
# N/N2's 194 recent opponents for a whole game.
N5_EXTRA = ("nb_hosen42_v11_hc1_vs_h5_validation",)


def n5():
    """N4 + the 9-29 library addition (N5_EXTRA) in the opponent shadow."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20}
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA) + N5_EXTRA
    return combo(*SHIP, "msell", "annex", "dlast", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965), parent_patches=WOOL_FIRST,
                 mf_opts=MF_FERT, annex_opts=dict(ANNEX_GATE),
                 dlast_opts={"pad": True, "detect": True})


# The base plan's step-3 counter pair (SELL 20 / BUY 20 wheat) assumes 20 wheat
# in stock; with 5 it buys 15 outright and the opening tape runs out of cash
# (3 live games lost by 15-20k). market_front caps such a buy-back at the stock.
MF_N6 = dict(MF_FERT, cap_counters=True)


def n6():
    """N5 + the counter-pair cap in market_front."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20}
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA) + N5_EXTRA
    return combo(*SHIP, "msell", "annex", "dlast", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965), parent_patches=WOOL_FIRST,
                 mf_opts=MF_N6, annex_opts=dict(ANNEX_GATE),
                 dlast_opts={"pad": True, "detect": True})


def n7s():
    """N6 + the round trip's sandwich accounting (rival sells at the draw, buys back next step)."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20, "sandwich": True}
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA) + N5_EXTRA
    return combo(*SHIP, "msell", "annex", "dlast", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965), parent_patches=WOOL_FIRST,
                 mf_opts=MF_N6, annex_opts=dict(ANNEX_GATE),
                 dlast_opts={"pad": True, "detect": True})


def n7r():
    """N7s + rider detection from the implied same-step sale (riders that buy more than they sell: Rio)."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20, "sandwich": True}
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA) + N5_EXTRA
    return combo(*SHIP, "msell", "annex", "dlast", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965), parent_patches=WOOL_FIRST,
                 mf_opts=MF_N6, annex_opts=dict(ANNEX_GATE),
                 dlast_opts={"pad": True, "detect": True, "implied": True})



def n7():
    """Agent N7: N6 + sandwich accounting + implied-sale riders + the placement guard."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20, "sandwich": True}
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA) + N5_EXTRA
    return combo(*SHIP, "msell", "annex", "dlast", "place", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965), parent_patches=WOOL_FIRST,
                 mf_opts=MF_N6, annex_opts=dict(ANNEX_GATE),
                 dlast_opts={"pad": True, "detect": True, "implied": True})



def n7g():
    """N7 + the trip governor in draw_last (pause round trips whose realized margin is gone)."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20, "sandwich": True}
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA) + N5_EXTRA
    return combo(*SHIP, "msell", "annex", "dlast", "place", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965), parent_patches=WOOL_FIRST,
                 mf_opts=MF_N6, annex_opts=dict(ANNEX_GATE),
                 dlast_opts={"pad": True, "detect": True, "implied": True, "governor": True})


def n7g0():
    """N7g with the governor pausing only losing trip streaks (mean realized margin < 0)."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20, "sandwich": True}
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA) + N5_EXTRA
    return combo(*SHIP, "msell", "annex", "dlast", "place", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965), parent_patches=WOOL_FIRST,
                 mf_opts=MF_N6, annex_opts=dict(ANNEX_GATE),
                 dlast_opts={"pad": True, "detect": True, "implied": True, "governor": True,
                             "gov_margin": 0.0})


def n7a():
    """N7 without the implied-sale rider path: N6 + sandwich accounting + the placement guard."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20, "sandwich": True}
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA) + N5_EXTRA
    return combo(*SHIP, "msell", "annex", "dlast", "place", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965), parent_patches=WOOL_FIRST,
                 mf_opts=MF_N6, annex_opts=dict(ANNEX_GATE),
                 dlast_opts={"pad": True, "detect": True})


def _n8(wheat_weight, adapt=False, drop_aware=False):
    """N7 with the market-front wheat weight scaled (goods sales ahead of our wheat trip);
    with `adapt`, full weight again once the rival is seen round-tripping wheat; with
    `drop_aware`, the seller races goods our workers drop this step."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20, "sandwich": True}
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA) + N5_EXTRA
    return combo(*SHIP, "msell", "annex", "dlast", "place", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True, "drop_aware": drop_aware},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965), parent_patches=WOOL_FIRST,
                 mf_opts=dict(MF_N6, wheat_weight=wheat_weight, wheat_adapt=adapt),
                 annex_opts=dict(ANNEX_GATE),
                 dlast_opts={"pad": True, "detect": True, "implied": True})


def n8w0():
    return _n8(0.0)


def n8w25():
    return _n8(0.25)


def n8a0():
    return _n8(0.0, adapt=True)


def n8a25():
    return _n8(0.25, adapt=True)


def n8d():
    """N7 + the drop-aware seller only (wheat weight 1)."""
    return _n8(1.0, drop_aware=True)


def n8a25d():
    return _n8(0.25, adapt=True, drop_aware=True)


def n3w():
    """N3 + N8's adaptive wheat weight only (no N4-N7 layers): the hedge for the final pair."""
    return _n3t_with(("annex",), parent_patches=WOOL_FIRST,
                     mf_opts=dict(MF_FERT, wheat_weight=0.25, wheat_adapt=True),
                     annex_opts=dict(ANNEX_GATE))


N9_EXTRA = ("nb_haodou092_harvest_ledger_r0930",)


def n9():
    """N8 + harvest-ledger's 9-30 version in the shadow library (18 programs)."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20, "sandwich": True}
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA) + N5_EXTRA + N9_EXTRA
    return combo(*SHIP, "msell", "annex", "dlast", "place", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965), parent_patches=WOOL_FIRST,
                 mf_opts=dict(MF_N6, wheat_weight=0.25, wheat_adapt=True),
                 annex_opts=dict(ANNEX_GATE),
                 dlast_opts={"pad": True, "detect": True, "implied": True})


def n3w9():
    """N3w + harvest-ledger's 9-30 version in the shadow library (17 programs)."""
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA) + N9_EXTRA
    return combo(*SHIP, "msell", "annex", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts={"flow_window": 8, "flow_stat": "median", "trap_guard": 20},
                 msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965), parent_patches=WOOL_FIRST,
                 mf_opts=dict(MF_FERT, wheat_weight=0.25, wheat_adapt=True),
                 annex_opts=dict(ANNEX_GATE))


def _n9_annex(**annex):
    """N9 with a different tomato-annex gate/size (top-bracket experiments)."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20, "sandwich": True}
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA) + N5_EXTRA + N9_EXTRA
    return combo(*SHIP, "msell", "annex", "dlast", "place", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965), parent_patches=WOOL_FIRST,
                 mf_opts=dict(MF_N6, wheat_weight=0.25, wheat_adapt=True),
                 annex_opts=annex,
                 dlast_opts={"pad": True, "detect": True, "implied": True})


def n10a():
    """N9, annex gate loosened: 2 tomato shops, shortage 100."""
    return _n9_annex(min_tomato_shops=2, min_shortage=100)


def n10b():
    """N9, annex gate off (fires whenever the parent's project conditions allow)."""
    return _n9_annex()


def n10c():
    """N9, 10-tile annex (SE rows 7-8) behind the standard gate."""
    return _n9_annex(min_tomato_shops=3, min_shortage=140, rows=(7, 8))


def _imit_patch(route_file, terminal=True):
    """Parent patch: add routes from `route_file` ({"routes": {id: tape}, "table": {"S1|S2": id}})
    and switch to the table's route at step 144 when the first two shops match."""
    return [(
        "_IMPL=make_agent(_ROUTES,router=_router,**_SETTINGS)",
        "import json as _imj\n"
        f"_IMD=_imj.load(open(r'{route_file}',encoding='utf-8'))\n"
        "for _imk,_imv in _IMD['routes'].items():\n"
        "    _ROUTES[int(_imk)]=_imv\n"
        "_IMT={tuple(k.split('|')):int(v) for k,v in _IMD['table'].items()}\n"
        f"_IM_TERMINAL={bool(terminal)}\n"
        "_router_base=_router\n"
        "def _router(observation,step,state):\n"
        "    r=_router_base(observation,step,state)\n"
        "    if step>=144:\n"
        "        if 'im_route' not in state:\n"
        "            shops=tuple((_get(_get(observation,'town',{}),'unlocked_shops',[]) or [])[:2])\n"
        "            state['im_route']=_IMT.get(shops)\n"
        "        if state['im_route'] is not None and not (_IM_TERMINAL and step>=648):\n"
        "            return state['im_route']\n"
        "    return r\n"
        "_IMPL=make_agent(_ROUTES,router=_router,**_SETTINGS)")]


def _imit(route_file, terminal=True):
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20, "sandwich": True}
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA) + N5_EXTRA + N9_EXTRA
    return combo(*SHIP, "msell", "annex", "dlast", "place", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965),
                 parent_patches=list(WOOL_FIRST) + _imit_patch(route_file, terminal),
                 mf_opts=dict(MF_N6, wheat_weight=0.25, wheat_adapt=True),
                 annex_opts=dict(ANNEX_GATE),
                 dlast_opts={"pad": True, "detect": True, "implied": True})


IMIT_DIR = ROOT_DIR / "rl" / "data" / "imit"


def imit_a():
    """Top-team routes mined from corpus half A (even episode ids)."""
    return _imit(str(IMIT_DIR / "routes_a.json"))


def imit_b():
    """Top-team routes mined from corpus half B (odd episode ids)."""
    return _imit(str(IMIT_DIR / "routes_b.json"))


def _n9_terminal(step):
    """N9 with the parent's terminal liquidation route starting at `step` instead of 648."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20, "sandwich": True}
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA) + N5_EXTRA + N9_EXTRA
    patch = [("if step>=648 and not state.get('day27'):", f"if step>={int(step)} and not state.get('day27'):")]
    return combo(*SHIP, "msell", "annex", "dlast", "place", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965),
                 parent_patches=list(WOOL_FIRST) + patch,
                 mf_opts=dict(MF_N6, wheat_weight=0.25, wheat_adapt=True),
                 annex_opts=dict(ANNEX_GATE),
                 dlast_opts={"pad": True, "detect": True, "implied": True})


def n11t624():
    return _n9_terminal(624)


def n11t640():
    return _n9_terminal(640)


def n11t660():
    return _n9_terminal(660)


def _n9_patched(extra):
    """N9 with extra exact-text patches to the 2965 parent."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20, "sandwich": True}
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA) + N5_EXTRA + N9_EXTRA
    return combo(*SHIP, "msell", "annex", "dlast", "place", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965),
                 parent_patches=list(WOOL_FIRST) + list(extra),
                 mf_opts=dict(MF_N6, wheat_weight=0.25, wheat_adapt=True),
                 annex_opts=dict(ANNEX_GATE),
                 dlast_opts={"pad": True, "detect": True, "implied": True})


def n12early():
    """N9 with the parent's EarlyCycle opening."""
    return _n9_patched([("_ALT_MODE = 'HybridOpening'", "_ALT_MODE = 'EarlyCycle'")])


def n12tomato():
    """N9 with the parent's TomatoInsteadOfCow opening."""
    return _n9_patched([("_ALT_MODE = 'HybridOpening'", "_ALT_MODE = 'TomatoInsteadOfCow'")])


def n11t600():
    return _n9_terminal(600)


def n11t672():
    return _n9_terminal(672)


def n13gen():
    """N9 on the generic route 0 all game (no shop-specific route at step 144); terminal at 648."""
    return _n9_patched([("    if step>=144 and not state.get('day6'):", "    if False and step>=144 and not state.get('day6'):")])


def n13gen624():
    """n13gen with the terminal route from step 624."""
    return _n9_patched([("    if step>=144 and not state.get('day6'):", "    if False and step>=144 and not state.get('day6'):"),
                        ("if step>=648 and not state.get('day27'):", "if step>=624 and not state.get('day27'):")])


def n10():
    """Agent N10 = N9 + the 2965 parent's terminal route from step 624 (day 26) instead of 648."""
    return _n9_terminal(624)


def _n9_project_day(day):
    """N9 with the parent's V219 tomato project starting on `day` instead of 18."""
    return _n9_patched([
        ("    if step==432:state['eligible']=_v219_qualifies(observation,native)",
         f"    if step=={24 * int(day)}:state['eligible']=_v219_qualifies(observation,native)"),
        ("    if not state.get('eligible') or day<18:return action",
         f"    if not state.get('eligible') or day<{int(day)}:return action")])


def n14d14():
    return _n9_project_day(14)


def n14d16():
    return _n9_project_day(16)


HARVEST_LEDGER_0930 = "rl/public/nb_haodou092_harvest_ledger_r0930.py"


def n9hl():
    """N9's whole stack on harvest-ledger's 9-30 farm plan (same engine family as the 2965 master)."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20, "sandwich": True}
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA) + N5_EXTRA + N9_EXTRA
    return combo(*SHIP, "msell", "annex", "dlast", "place", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / HARVEST_LEDGER_0930), parent_patches=WOOL_FIRST,
                 mf_opts=dict(MF_N6, wheat_weight=0.25, wheat_adapt=True),
                 annex_opts=dict(ANNEX_GATE),
                 dlast_opts={"pad": True, "detect": True, "implied": True})


_GUARD_BASE = ("_SETTINGS={'hand_align': True, 'weed_repair': True, 'sell_lead': True, 'budget_guard': False, "
               "'room_guard': False, 'clamp_sells': False, 'dead_stock': False, 'terminal_liquidation': False, "
               "'front_run': False}")


def _n9_guards(*on):
    """N9 with some of the 2965 chassis's disabled guards switched on."""
    new = _GUARD_BASE
    for g in on:
        new = new.replace(f"'{g}': False", f"'{g}': True")
    return _n9_patched([(_GUARD_BASE, new)])


def g_room():
    return _n9_guards("room_guard")


def g_budget():
    return _n9_guards("budget_guard")


def g_dead():
    return _n9_guards("dead_stock")


def g_term():
    return _n9_guards("terminal_liquidation")


def g_clamp():
    return _n9_guards("clamp_sells")


def g_all():
    return _n9_guards("room_guard", "budget_guard", "dead_stock", "terminal_liquidation", "clamp_sells")



def n10s():
    """N9 + rl/shed_guard.py (sell the day-end shed overflow instead of losing it)."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20, "sandwich": True}
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA) + N5_EXTRA + N9_EXTRA
    return combo(*SHIP, "msell", "annex", "dlast", "place", "shed", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965), parent_patches=WOOL_FIRST,
                 mf_opts=dict(MF_N6, wheat_weight=0.25, wheat_adapt=True),
                 annex_opts=dict(ANNEX_GATE),
                 dlast_opts={"pad": True, "detect": True, "implied": True})


def n10():
    """Agent N10 = N9 + rl/shed_guard.py (the day-end drop destroys nothing)."""
    return n10s()


def n11():
    """N10 + rl/own_book.py (the parent's rival-sale trackers see what we really sold)."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20, "sandwich": True}
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA) + N5_EXTRA + N9_EXTRA
    return combo(*SHIP, "msell", "annex", "dlast", "place", "shed", "book", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965), parent_patches=WOOL_FIRST,
                 mf_opts=dict(MF_N6, wheat_weight=0.25, wheat_adapt=True),
                 annex_opts=dict(ANNEX_GATE),
                 dlast_opts={"pad": True, "detect": True, "implied": True})


def n11b():
    """N11 with the race/PREDICT snapshot rebuilt wholly from the final action (V53's way)."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20, "sandwich": True}
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA) + N5_EXTRA + N9_EXTRA
    return combo(*SHIP, "msell", "annex", "dlast", "place", "shed", "book", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965), parent_patches=WOOL_FIRST,
                 mf_opts=dict(MF_N6, wheat_weight=0.25, wheat_adapt=True),
                 annex_opts=dict(ANNEX_GATE), book_opts={"race_final": True},
                 dlast_opts={"pad": True, "detect": True, "implied": True})


N12_EXTRA = ("nb_haodou092_harvest_ledger_r1001",)


def n12():
    """N11 + harvest-ledger's 10-01 version in the shadow library (19 programs)."""
    rt = {"flow_window": 8, "flow_stat": "median", "trap_guard": 20, "sandwich": True}
    from rl.l2_shadow import SH_LIBRARY
    lib = tuple(SH_LIBRARY) + NEW_LIBRARY + M_LIBRARY_EXTRA + tuple(N3_EXTRA) + N5_EXTRA + N9_EXTRA + N12_EXTRA
    return combo(*SHIP, "msell", "annex", "dlast", "place", "shed", "book", shadow_programs=lib,
                 shadow_opts={"early_when_agree": True, "early_now": True},
                 rt_opts=rt, msell_opts={"after_beaten": True, "beaten_any": True},
                 gate=None, parent_file=str(ROOT_DIR / MASTER_2965), parent_patches=WOOL_FIRST,
                 mf_opts=dict(MF_N6, wheat_weight=0.25, wheat_adapt=True),
                 annex_opts=dict(ANNEX_GATE),
                 dlast_opts={"pad": True, "detect": True, "implied": True})
