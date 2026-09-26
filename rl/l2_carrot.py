"""Town-adaptive carrot: swap the tape's wheat plantings for carrots sooner.

A's v9 CARROT layer swaps a planted wheat for a carrot only once the current
carrot price is 2x the wheat price (days 10-23). Watered wheat yields 4 units
for a $10 seed and a carrot 3 for $20, and a carrot turns over in 3 days
instead of 4, so a carrot already pays at about (4 * wheat + 10) / 3, i.e.
~1.4x at wheat $40. In towns with pet cafes and farmers markets (the hinge
book runs dry) the tape keeps planting wheat while the carrot price climbs --
live game 113808379 was lost that way (-6.5k).

These variants only change the parent's own constants (it reads them at call
time), so the tape, its carrot rescue (harvest on the age-3 visit) and its
wheat feed reserve all keep working.
"""

from rl.candidate_l import l_stack


def _patch(ratio, first, last, reserve=None):
    def inner(agent, env):
        env["V9_CARROT_RATIO"] = ratio
        env["V9_CARROT_FIRST_DAY"] = first
        env["V9_CARROT_LAST_DAY"] = last
        if reserve is not None:
            env["V9_CARROT_WHEAT_RESERVE"] = reserve
        return agent
    return inner


def build():            # ratio 1.5, days 8-24
    return l_stack(inner=_patch(1.5, 8, 24))


def build_r14():
    return l_stack(inner=_patch(1.4, 8, 24))


def build_r17():
    return l_stack(inner=_patch(1.7, 10, 23))


def build_r15_late():
    return l_stack(inner=_patch(1.5, 10, 25))
