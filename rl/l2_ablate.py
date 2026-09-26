"""Ablations of the shipped L2 stack: each factory drops one layer."""
from rl.l2_combo import SHIP, combo


def _without(name):
    return combo(*[n for n in SHIP if n != name])


def no_shadow(): return _without("shadow")
def no_rt(): return _without("rt")
def no_lot(): return _without("lot")
def no_fert(): return _without("fert")
def no_feed(): return _without("feed")
def no_labour(): return _without("labour")
