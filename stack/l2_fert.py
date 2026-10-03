"""Fertilize young wheat from day one, with the fertilizer A already carries.

A's v9 FERT layer turns a worker's age-1 WATER on a wheat/carrot into
FERTILIZE when that worker carries fertilizer (the age-1 watering is optional;
fertilized for ages 1-3 a wheat plant ends at 6 units instead of 4). It only
acts from day 14, reasoning that fertilizer is worth using once its price is
below two wheat -- but two wheat (~$70-80) exceed the fertilizer price from
the start ($55 early, ~$33 mid-game), and against 2600-2700 lineage teams A
harvests ~48 fewer wheat a game because fewer of its wheat plants are
fertilized. These variants only move the parent's start day.
"""

from stack.candidate_l import l_stack


def _patch(first_day, ages=None):
    def inner(agent, env):
        env["V9_FERT_FIRST_DAY"] = first_day
        if ages is not None:
            env["V9_FERT_AGES"] = ages
        return agent
    return inner


def build():          # from day 3
    return l_stack(inner=_patch(3))


def build_d6():
    return l_stack(inner=_patch(6))


def build_d10():
    return l_stack(inner=_patch(10))
